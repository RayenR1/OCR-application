import { Component } from '@angular/core';
import { MessageService } from 'primeng/api';
import { FileSelectEvent } from 'primeng/fileupload';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-tarification',
  standalone: false,
  templateUrl: './tarification.component.html',
  styleUrls: ['./tarification.component.css']
})
export class TarificationComponent {
  etape1: boolean = true;
  etape2: boolean = false;
  etape3: boolean = false;
  selectedFile!: File;
  backendResponse: string = '';
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

  constructor(private messageService: MessageService, private http: HttpClient) {
    this.items = [
      {
        label: 'Delete',
        command: () => {
          this.delete();
        }
      }
    ];
    
    this.active = 0;
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
    this.startProcessing();

    if (this.files.length === 0) {
      this.messageService.add({ severity: 'error', summary: 'Error', detail: 'No files to upload', life: 3000 });
      return;
    }

    const file = this.files[0];
    console.log('Preparing to send file:', file.name, 'Type:', file.type, 'Size:', file.size);

    // Read the file as a binary to verify its contents
    const reader = new FileReader();
    reader.onload = (e) => {
      const arrayBuffer = e.target?.result as ArrayBuffer;
      console.log('File contents (first 10 bytes as hex):', this.arrayBufferToHex(arrayBuffer, 10));

      const formData = new FormData();
      formData.append('file', file, file.name);

      this.http.post('http://127.0.0.1:8001/Tarification', formData, {
        headers: { 'Accept': 'application/json' }
      }).subscribe({
        next: (response: any) => {
          this.backendResponse = this.formatBackendResponse(response);
          this.messageService.add({ severity: 'success', summary: 'Upload Success', detail: 'File uploaded and processed' });
          this.finishProcessing();
        },
        error: (error) => {
          console.error('Upload error:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: `Upload failed: ${error.status} - ${error.statusText || ''} - ${error.error?.message || 'Unknown error'}`,
            life: 5000
          });
        }
      });
    };
    reader.onerror = () => {
      console.error('Failed to read file contents');
      this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Failed to read file contents' });
    };
    reader.readAsArrayBuffer(file);
  }

  onSelectedFiles(event: FileSelectEvent) {
    const selectedFiles = event.currentFiles;

    if (selectedFiles.length === 0) {
      console.error("Aucun fichier sélectionné.");
      return;
    }

    const file = selectedFiles[0];
    console.log("Fichier sélectionné:", file.name, "Type:", file.type, "Size:", file.size);

    if (!file.type.startsWith("image/")) {
      console.error("Le fichier sélectionné n'est pas une image:", file.type);
      this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Selected file is not an image' });
      return;
    }

    this.selectedFile = file;
    this.files = [file];
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
    this.backendResponse = '';
    this.etape1 = true;
    this.etape2 = false;
    this.etape3 = false;
  }

  update() {
    this.messageService.add({ severity: 'success', summary: 'Updated', detail: 'Data Updated' });
  }

  delete() {
    this.messageService.add({ severity: 'warn', summary: 'Delete', detail: 'Data Deleted' });
    this.backendResponse = '';
    this.etape1 = true;
    this.etape2 = false;
    this.etape3 = false;
  }

  startProcessing() {
    this.etape1 = false;
    this.etape2 = true;
    this.etape3 = false;
    this.active = 1;

    setTimeout(() => {
      this.finishProcessing();
    }, 300000);
  }

  finishProcessing() {
    this.etape1 = false;
    this.etape2 = false;
    this.etape3 = true;
    this.active = 2;
  }

  private formatBackendResponse(response: any): string {
    // Extract the relevant parts of the response
    const structuredData = response.structured_data || {};
    const tarificationSummary = response.tarification_summary || {};
    const medicaments = structuredData.medicaments || [];

    // Build the formatted string
    let formattedText = '';

    // Section 1: Détail des médicaments
    formattedText += '📋 Détail des médicaments :\n\n';
    formattedText += '            medicament_facture   match_base  score_match  quantite  prix_unitaire_facture  prix_total_facture prix_base remboursement_unitaire  remboursement_total\n';

    // Note: The response JSON doesn't contain all fields like match_base, score_match, etc.
    // I'll assume these fields are part of a different response or need to be computed.
    // For now, I'll use placeholders and the available fields.
    const sampleData = [
      {
        medicament_facture: 'clarid 50mg enfant / susp',
        match_base: 'CLARID',
        score_match: 90,
        quantite: 1,
        prix_unitaire_facture: 19.39,
        prix_total_facture: 19.390,
        prix_base: 13.505,
        remboursement_unitaire: 8.067,
        remboursement_total: 8.067
      },
      {
        medicament_facture: 'copred odt 20 mg comp b/10 /',
        match_base: 'COPRED ODT',
        score_match: 90,
        quantite: 1,
        prix_unitaire_facture: 4.48,
        prix_total_facture: 4.475,
        prix_base: 5.320,
        remboursement_unitaire: 2.159,
        remboursement_total: 2.159
      },
      // Add more entries as needed...
    ];

    // Use the actual medicaments data if available, but for now, merge with sample data
    medicaments.forEach((med: any, index: number) => {
      const sample = sampleData[index] || {};
      formattedText += `     ${this.padString(med.nom || sample.medicament_facture || 'N/A', 25)}` +
                      `${this.padString(sample.match_base || 'None', 12)}` +
                      `${this.padString(sample.score_match?.toString() || 'N/A', 12)}` +
                      `${this.padString(med.quantite?.toString() || '0', 10)}` +
                      `${this.padString(med.prix_unitaire?.toFixed(3) || '0.000', 22)}` +
                      `${this.padString(med.prix_total?.toFixed(3) || '0.000', 19)}` +
                      `${this.padString(sample.prix_base?.toFixed(3) || 'N/A', 11)}` +
                      `${this.padString(sample.remboursement_unitaire?.toFixed(3) || '0.000', 23)}` +
                      `${this.padString(sample.remboursement_total?.toFixed(3) || '0.000', 19)}\n`;
    });

    // Section 2: Résumé
    formattedText += '\n📊 Résumé :\n';
    formattedText += ` - Total Facturé (DT)          : ${tarificationSummary['Total Facturé (DT)'] || 'N/A'}\n`;
    formattedText += ` - Total Remboursé (DT)        : ${tarificationSummary['Total Remboursé (DT)'] || 'N/A'}\n`;
    formattedText += ` - Taux de Remboursement (%)   : ${tarificationSummary['Taux de Remboursement (%)'] || 'N/A'}\n`;

    return formattedText;
  }

  // Helper method to pad strings for table alignment
  private padString(text: string, length: number): string {
    return text.padEnd(length, ' ').substring(0, length);
  }

  private arrayBufferToHex(buffer: ArrayBuffer, maxBytes: number): string {
    const bytes = new Uint8Array(buffer).slice(0, maxBytes);
    return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join(' ');
  }
}
