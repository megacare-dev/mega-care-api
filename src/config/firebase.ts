import * as admin from 'firebase-admin';
// Assuming your Customer and Device interfaces (from '../interfaces') include an 'id' field.
// T in dataPoint<T> will represent the data structure within the Firestore document (i.e., without the 'id').
import { Customer, Device } from '../interfaces'; // Adjust path as necessary
import { WithFieldValue, PartialWithFieldValue, SetOptions, DocumentData, QueryDocumentSnapshot, FirestoreDataConverter, SnapshotOptions } from 'firebase-admin/firestore';
// Define types for Firestore document data (without id)
export type CustomerDoc = Omit<Customer, 'id'>;
export type DeviceDoc = Omit<Device, 'id'>;
// Define other Doc types here as needed, e.g., MaskDoc, AirTubingDoc, DailyReportDoc

/**
 * Initializes the Firebase Admin SDK and Firestore.
 * This function should be called once at application startup.
 */
export const initializeFirebase = () => {
  if (admin.apps.length === 0) { // Check if already initialized
    try {
      admin.initializeApp({
        projectId: process.env.GCLOUD_PROJECT || 'mega-care-dev', // Prefer environment variable
      });
      console.log('Firebase Admin SDK initialized successfully.');
    } catch (error: any) {
      console.error('Firebase Admin SDK initialization error:', error.message);
      process.exit(1); // Exit if critical initialization fails
    }
  }
};

// This helper function pipes your types through a firestore converter
const converter = <AppModelType extends DocumentData>(): FirestoreDataConverter<AppModelType, DocumentData> => ({
  toFirestore(
    modelObject: WithFieldValue<AppModelType> | PartialWithFieldValue<AppModelType>,
    options?: SetOptions // options is present for the partial update overload
  ): DocumentData { // Return type is DocumentData
    // The Firestore SDK handles how to apply this data based on the operation (add, set, update).
    // We just need to return the data in a format Firestore understands.
    return modelObject as DocumentData;
  },
  fromFirestore(
    snapshot: QueryDocumentSnapshot<DocumentData>, // Firestore stores DocumentData
    options?: SnapshotOptions // options is optional for fromFirestore
  ): AppModelType {
    // snapshot.data() returns DocumentData. We assert it to our AppModelType.
    return snapshot.data() as AppModelType; // snapshot.data() typically takes no args when a converter is used
  }
});

// This helper function exposes a 'typed' version of firestore().collection(collectionPath)
const dataPoint = <AppModelType extends DocumentData>(collectionPath: string) => {
  if (admin.apps.length === 0) {
    // This should ideally be prevented by calling initializeFirebase() at application startup.
    throw new Error("Firebase not initialized. Call initializeFirebase() first.");
  }
  return admin.firestore().collection(collectionPath).withConverter(converter<AppModelType>());
};

// Construct a database helper object
export const db = {
  customers: dataPoint<CustomerDoc>('customers'),
  customerDevices: (customerId: string) => dataPoint<DeviceDoc>(`customers/${customerId}/devices`),
  // Define other collections similarly:
  // customerMasks: (customerId: string) => dataPoint<MaskDoc>(`customers/${customerId}/masks`),
};