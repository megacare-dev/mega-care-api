import { Timestamp } from 'firebase-admin/firestore';

export interface Organisation {
  name: string;
  // Add other organisation fields if any
}

export interface ClinicalUser {
  name: string;
  // Add other clinical user fields if any
}

export interface Compliance {
  status: string; // e.g., "Compliant", "Non-Compliant"
  usagePercentage: number; // e.g., 85 for 85%
  // Add other compliance fields if any
}

export interface DataAccess {
  type: string; // e.g., "Full", "Limited"
  durationDays?: number; // Optional duration
  // Add other data access fields if any
}

export interface Customer {
  id?: string; // Document ID, usually not stored in the document itself
  lineId: string;
  displayName: string;
  title: string;
  firstName: string;
  lastName: string;
  dob: Timestamp | Date | string; // Store as Timestamp, allow Date/string for input
  location: string;
  status: string;
  setupDate: Timestamp | Date | string; // Store as Timestamp
  airViewNumber: string;
  monitoringType: string;
  availableData: string;
  dealerPatientId: string;
  organisation: Organisation | Record<string, any>;
  clinicalUser: ClinicalUser | Record<string, any>;
  compliance: Compliance | Record<string, any>;
  dataAccess: DataAccess | Record<string, any>;
}

export interface DeviceSettings {
  // Define specific device settings fields here
  // Example:
  // mode: string;
  // pressureMin: number;
  // pressureMax: number;
  [key: string]: any; // Allow other dynamic settings
}

export interface Device {
  id?: string; // Document ID
  deviceName: string;
  serialNumber: string;
  addedDate: Timestamp | Date | string; // Store as Timestamp
  status: string;
  settings: DeviceSettings | Record<string, any>;
}

export interface Mask {
  id?: string; // Document ID
  maskName: string;
  size: string;
  addedDate: Timestamp | Date | string; // Store as Timestamp
}

export interface AirTubing {
  id?: string; // Document ID
  tubingName: string;
  addedDate: Timestamp | Date | string; // Store as Timestamp
}

export interface DailyReport {
  id?: string; // Document ID (reportDate in YYYY-MM-DD)
  reportDate: Timestamp | Date | string; // Store as Timestamp
  usageHours: string;
  cheyneStokesRespiration: string;
  rera: number;
  leak: Record<string, any>; // e.g., { median: number, percentile95: number }
  pressure: Record<string, any>; // e.g., { median: number, percentile95: number }
  eventsPerHour: Record<string, any>; // e.g., { ahi: number, centralApneas: number }
  deviceSnapshot: Record<string, any>; // Snapshot of device settings
}