import { Component } from '@angular/core';
import Swal from 'sweetalert2';

@Component({
  selector: 'app-contact',
  standalone: false,
  templateUrl: './contact.component.html',
  styleUrl: './contact.component.css'
})
export class ContactComponent {
  contact = {
    name: '',
    email: '',
    message: ''
  };

  formSubmitted = false;

  onSubmit() {
    if (this.contact.name && this.contact.email && this.contact.message) {
      // Handle form submission logic (e.g., send to API)

      // Show SweetAlert when the form is successfully submitted
      Swal.fire({
        title: 'Success!',
        text: 'Your message has been sent successfully!',
        icon: 'success',
        confirmButtonText: 'OK',
        confirmButtonColor: '#6b46c1'  // Custom color (optional)
      });

      this.formSubmitted = true;

      // Reset form after submission
      this.contact = {
        name: '',
        email: '',
        message: ''
      };
    } else {
      // Optional: Show an alert if the form is incomplete
      Swal.fire({
        title: 'Error!',
        text: 'Please fill in all the required fields.',
        icon: 'error',
        confirmButtonText: 'OK',
        confirmButtonColor: '#e3342f'  // Custom color (optional)
      });
    }
  }

}
