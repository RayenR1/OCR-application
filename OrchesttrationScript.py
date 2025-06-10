from confluent_kafka import Consumer, KafkaError
import os
import subprocess
import time
import signal
import pathlib
import binascii

# Configuration Kafka
consumer_config = {
    'bootstrap.servers': '127.0.0.1:9092',
    'group.id': 'orchestrator_group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False
}

# Topics de sortie pour chaque service
CLASSIFIED_TOPICS = {
    "Bulltin soin": "Classified-BS",
    "ordonnances": "Classified-ordonnance",
    "facture": "Classified-facture",
    "autre": "autre"
}

FILTERED_TOPICS = {
    "BS": "filtered-BS",
    "ordonnance": "filtered-ordonnances",
    "facture": "filtered-facture",
    "autre": "filtered-autre"
}

# Pipeline : (topic d'entrée, nom du service, topics de sortie, port)
PIPELINE = [
    ('Input-Images', 'classification_service', list(CLASSIFIED_TOPICS.values()), 8000),
    (list(CLASSIFIED_TOPICS.values()), 'image_filter_service', list(FILTERED_TOPICS.values()), 8001),
    (list(FILTERED_TOPICS.values()), 'layout_detection_service', ['output-layout'], 8002),
    (['output-layout'], 'extraction_service', ['output-ocr'], 8003),
    (['output-ocr'], 'structuring_service', ['output-structuring'], 8004)
]

# Environnement Conda
CONDA_ENV = 'pids'

# Dictionnaire pour stocker les processus Uvicorn
processes = {}

# Base directory of the script
BASE_DIR = pathlib.Path(__file__).parent.resolve()

def start_service(service_name, port):
    """Lance un service FastAPI localement avec Uvicorn"""
    service_dir = BASE_DIR / service_name
    app_path = service_dir / "app" / "main.py"

    # Vérifier si le répertoire et le fichier existent
    if not service_dir.exists():
        print(f"Error: Directory {service_dir} does not exist")
        return False
    if not app_path.exists():
        print(f"Error: File {app_path} does not exist")
        return False

    service_dir_str = str(service_dir).replace('/', '\\') if os.name == 'nt' else str(service_dir)
    cmd = f'cd "{service_dir_str}" && uvicorn app.main:app --host 127.0.0.1 --port {port}'
    print(f"Executing command: {cmd}")

    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=None if os.name == 'nt' else os.setsid
        )
        processes[service_name] = process
        time.sleep(5)  # Attendre que le service démarre

        # Vérifier si le processus est toujours en vie
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            error = stderr or stdout or "Unknown error"
            print(f"Service {service_name} failed to start: {error}")
            if service_name in processes:
                del processes[service_name]
            return False

        print(f"Service {service_name} started on port {port} (PID: {process.pid})")
        return True
    except Exception as e:
        print(f"Error starting {service_name}: {e}")
        return False

def stop_service(service_name):
    """Arrête un service FastAPI"""
    if service_name in processes:
        process = processes[service_name]
        try:
            if os.name == 'nt':
                process.terminate()
            else:
                os.killpg(process.pid, signal.SIGTERM)
            process.wait()
            print(f"Service {service_name} stopped (PID: {process.pid})")
        except Exception as e:
            print(f"Error stopping {service_name}: {e}")
        finally:
            del processes[service_name]

def monitor_topic(input_topics, service_name, output_topics, port, previous_service=None):
    """Surveille les topics d'entrée, lance le service, attend un message dans les topics de sortie"""
    if previous_service and previous_service in processes:
        consumer = Consumer(consumer_config)
        try:
            if isinstance(input_topics, list):
                consumer.subscribe(input_topics)
            else:
                consumer.subscribe([input_topics])
            
            print(f"Monitoring input topics {input_topics} for {service_name}")
            while True:
                msg = consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        print("Reached end of partition")
                        continue
                    print(f"Consumer error: {msg.error()}")
                    consumer.close()
                    return False
                
                print(f"Message detected in input topics {input_topics} for {service_name}")
                stop_service(previous_service)
                if not start_service(service_name, port):
                    consumer.close()
                    return False
                break
        except Exception as e:
            print(f"Error in consumer for {service_name}: {e}")
            consumer.close()
            return False
        consumer.close()
    else:
        if not start_service(service_name, port):
            return False
    
    output_consumer = Consumer(consumer_config)
    try:
        output_consumer.subscribe(output_topics)
        print(f"Monitoring output topics {output_topics} for {service_name}")
        while True:
            out_msg = output_consumer.poll(1.0)
            if out_msg is None:
                time.sleep(1)
                continue
            if out_msg.error():
                if out_msg.error().code() == KafkaError._PARTITION_EOF:
                    print("Reached end of partition")
                    continue
                print(f"Consumer error: {out_msg.error()}")
                output_consumer.close()
                return False
            
            # Vérifier l'existence du message sans décodage
            raw_message = out_msg.value()
            print(f"Message received in output topics {output_topics} for {service_name} (size: {len(raw_message)} bytes, hex: {binascii.hexlify(raw_message[:50]).decode('ascii')[:100]}...)")
            
            output_consumer.close()
            return True
    except Exception as e:
        print(f"Error in output consumer for {service_name}: {e}")
        output_consumer.close()
        return False
    output_consumer.close()
    return False

def run_pipeline():
    """Exécute le pipeline une fois et arrête tous les services sauf le premier"""
    previous_service = None
    for input_topics, service_name, output_topics, port in PIPELINE:
        print(f"Processing step: {service_name}")
        success = monitor_topic(input_topics, service_name, output_topics, port, previous_service)
        if not success:
            print(f"No message received or processed for {service_name}, stopping pipeline")
            break
        previous_service = service_name
    
    first_service = PIPELINE[0][1]
    for service_name in list(processes.keys()):
        if service_name != first_service:
            stop_service(service_name)
    print("Pipeline completed, back to initial state")

def main():
    first_input_topics, first_service, first_output_topics, first_port = PIPELINE[0]
    if not start_service(first_service, first_port):
        print(f"Failed to start {first_service}, exiting")
        return
    print(f"Initial state: {first_service} running, waiting for messages...")
    
    while True:
        consumer = Consumer(consumer_config)
        try:
            consumer.subscribe(first_output_topics)
            
            print(f"Monitoring output topics {first_output_topics} for {first_service}")
            while True:
                msg = consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        print("Reached end of partition")
                        continue
                    print(f"Consumer error: {msg.error()}")
                    consumer.close()
                    break
                
                # Vérifier l'existence du message sans décodage
                raw_message = msg.value()
                print(f"Message received in output topics {first_output_topics} for {first_service} (size: {len(raw_message)} bytes, hex: {binascii.hexlify(raw_message[:50]).decode('ascii')[:100]}...)")
                
                consumer.close()
                run_pipeline()
                if not start_service(first_service, first_port):
                    print(f"Failed to restart {first_service}, exiting")
                    return
                print(f"Initial state: {first_service} running, waiting for messages...")
                break
        except Exception as e:
            print(f"Error in main consumer: {e}")
            consumer.close()
            break

if __name__ == "__main__":
    main()