import { Car } from './carModel'; 
export interface Penalty {
  penaltyId?: string;  // optionnel car généré automatiquement
  penaltyType: string;
  penaltyAmount: number;
  penaltyDate: string; // LocalDate sera une string en format "YYYY-MM-DD"
  penaltyPlace: string;
  penaltyReason: string;
  penaltyPaymentStatus: boolean;
  carInformations?: Car[];
    
}