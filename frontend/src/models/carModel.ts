export interface Car {
  carId: string;
  carModel: string;
  carPlate: string;
  carColor: string | null;
  carType: string | null;
  insurance: boolean | null;
  technicalVisit: boolean | null;  // Assuming dates in proper format from API
  vignette: boolean | null;       // You might want to handle date formatting
  isStolen: boolean | null;
  isWanted: boolean | null;
  
}