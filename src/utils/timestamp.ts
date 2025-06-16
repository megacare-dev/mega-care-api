import { Timestamp } from 'firebase-admin/firestore';

// Helper to convert input dates to Firestore Timestamps
export const toTimestamp = (date: Date | string | Timestamp): Timestamp => {
  if (date instanceof Timestamp) return date;
  return Timestamp.fromDate(new Date(date));
};