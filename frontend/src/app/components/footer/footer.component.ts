import { Component } from '@angular/core';
import Swal from 'sweetalert2';

@Component({
  selector: 'app-footer',
  standalone: false,
  templateUrl: './footer.component.html',
  styleUrl: './footer.component.css'
})
export class FooterComponent {
  email: string = '';

  subscribe() {
    if (this.email.trim() !== '') {
      Swal.fire({
        title: 'Success!',
        text: 'Thank you for subscribing to our newsletter!',
        icon: 'success',
        confirmButtonText: 'OK',
      });
      this.email = ''; // Réinitialiser le champ
    } else {
      Swal.fire({
        title: 'Error!',
        text: 'Please enter a valid email address.',
        icon: 'error',
        confirmButtonText: 'OK',
      });
    }
  }
}
