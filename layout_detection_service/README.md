# Layout Detection Service

## Description
This service detects layouts (tables, typed text, handwritten text) from images consumed from Kafka topics `filtered-BS`, `filtered-ordonnances`, `filtered-facture`, and `filtered-autre`. It utilizes MLflow to track segmentation metrics and sends the results (image and JSON) to the `output-layout` topic.

## Prerequisites
- Docker
- Docker Compose
- Python 3.10.16

## Installation
1. Clone the repository or create the following structure:

   ```bash
   git clone https://github.com/RayenR1/LayoutDetectionService.git
   cd LayoutDetectionService
   ```

2. Set up a virtual environment and install dependencies:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. Configure environment variables as needed.

## Usage
1. Start the service using Docker Compose:

   ```bash
   docker-compose up --build
   ```

2. The service will consume images from Kafka topics and output detected layouts.

## Authors
- **Rayen Jlassi** - Main Development
- **Skander Kammoun** - Keywords & Notebook Contributions

## License
© 2025 EyeQ - Esprit School of Engineering - Doxaria
