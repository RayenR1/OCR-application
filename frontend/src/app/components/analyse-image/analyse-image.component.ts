import { Component } from '@angular/core';
import { MessageService } from 'primeng/api';
import { FileSelectEvent } from 'primeng/fileupload';

@Component({
  selector: 'app-analyse-image',
  standalone: false,
  templateUrl: './analyse-image.component.html',
  styleUrl: './analyse-image.component.css'
})
export class AnalyseImageComponent  {

  etape1: boolean = true;
  etape2: boolean = false;
  etape3: boolean = false;
  backendResponse: string = 
  'PARTIE A REMPLIR PAR L\'ADHERENT\n' +
  'ADHESION N° : 461\n' +
  'SINISTRE N° :\n' +
  'DATE : 13/11/2025\n\n' +
  'EMPLOYEUR : C.T.A.M.A\n' +
  'ADHERENT : Nom : Ben Mahdzaf\n' +
  'Prénom : Samira\n' +
  'Adresse :\n' +
  'Emploi :\n\n' +
  'L\'adhérent - le conjoint - l\'enfant (1)\n\n' +
  'Signature du salarié : [Signature manuscrite présente]\n\n' +
  'PARTIE A REMPLIR PAR LE PRATICIEN\n' +
  'Nom et prénom du malade : Ben Mahdzaf Samira\n' +
  'Pièce d\'identité (obligatoire) n° :\n\n' +
  'DATE : 12/11/2025\n' +
  'Désignation C - VPC ou K nomenclature : [illisible]\n' +
  'Montant des honoraires perçus : 20,000\n\n' +
  'Nom et cachet du médecin attestant le paiement des actes médicaux :\n' +
  'Dr. SAADA Ridha\n' +
  'Médecine Générale\n' +
  '[Cachet visible sur le document]\n\n' +
  'EXECUTION DES ORDONNANCES\n' +
  'Désignation : Code ordonnance : 442973\n\n' +
  'PARTIE RESERVEE A L\'ASSUREUR - A NE PAS REMPLIR\n' +
  'N° Sinistre : 0135250C\n' +
  'Matricule :\n' +
  'Bénéf. :\n\n';
  
  
  text: string | undefined;
  items2: any[] | undefined;
  active: number = 0;
  files: File[] = [];
  items: any[];
  uploadedFiles: File[] = [];
  config: { translation: { fileSizeTypes: string[] } } = {
    translation: {
      fileSizeTypes: ['Bytes', 'KB', 'MB', 'GB', 'TB']
    }
  };

  totalSize: number = 0;
  totalSizePercent: number = 0;

  constructor(private messageService: MessageService) {
    this.items = [
      {
        label: 'Delete',
        command: () => {
          this.delete();
        }
      }
    ];
    this.items2 = [
      {
          label: 'Upload image',
          command: (event: any) => this.messageService.add({severity:'info', summary:'First Step', detail: event.item.label})
      },
      {
          label: 'Processe',
          command: (event: any) => this.messageService.add({severity:'info', summary:'First Step', detail: event.item.label})
      },
      {
          label: 'Result',
          command: (event: any) => this.messageService.add({severity:'info', summary:'First Step', detail: event.item.label})
      }
  ];
  this.active = 0
  }
  

  choose(event: Event, callback: () => void) {
    callback();
  }

  onRemoveTemplatingFile(event: Event, file: File, removeFileCallback: (event: Event, index: number) => void, index: number) {
    removeFileCallback(event, index);
    this.totalSize -= file.size;
    this.totalSizePercent = (this.totalSize / 1000000) * 100;
  }

  onClearTemplatingUpload(clear: () => void) {
    clear();
    this.files = [];
    this.totalSize = 0;
    this.totalSizePercent = 0;
  }

  onTemplatedUpload() {
    this.uploadedFiles = [...this.files];
    this.files = [];
    this.totalSize = 0;
    this.totalSizePercent = 0;
    this.messageService.add({ severity: 'info', summary: 'Success', detail: 'File Uploaded', life: 3000 });
    this.startProcessing();
  }

  onSelectedFiles(event: FileSelectEvent) {
    this.files = event.files;
    this.totalSize = this.files.reduce((sum, file) => sum + file.size, 0);
    this.totalSizePercent = (this.totalSize / 1000000) * 100;
  }

  onRemoveUploadedFile(index: number) {
    this.uploadedFiles.splice(index, 1);
    this.totalSize = this.uploadedFiles.reduce((sum, file) => sum + file.size, 0);
    this.totalSizePercent = (this.totalSize / 1000000) * 100;
  }

  uploadEvent(callback: () => void) {
    callback();
  }

  formatSize(bytes: number): string {
    const k = 1024;
    const dm = 3;
    const sizes = this.config.translation.fileSizeTypes;
    if (bytes === 0) {
      return `0 ${sizes[0]}`;
    }

    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const formattedSize = parseFloat((bytes / Math.pow(k, i)).toFixed(dm));

    return `${formattedSize} ${sizes[i]}`;
  }

  save() {
    this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Data Saved' });
    this.backendResponse='';
    this.etape1 = true;
    this.etape2 = false;
    this.etape3 = false;

  }

  update() {
    this.messageService.add({ severity: 'success', summary: 'Updated', detail: 'Data Updated' });
  }

  delete() {
    this.messageService.add({ severity: 'warn', summary: 'Delete', detail: 'Data Deleted' });
    this.backendResponse='';
    this.etape1 = true;
    this.etape2 = false;
    this.etape3 = false;
  }

  startProcessing() {
    // Passer à l'étape 2
    this.etape1 = false;
    this.etape2 = true;
    this.etape3 = false;
    this.active = 1;
    
    // Simuler un traitement de 60 secondes
  setTimeout(() => {
    this.finishProcessing();
  }, 6000);
  }

  finishProcessing() {
    // Passer à l'étape 3
    this.etape1 = false;
    this.etape2 = false;
    this.etape3 = true;
    this.active = 2;
  
  }
}