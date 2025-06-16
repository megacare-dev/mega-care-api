import * as admin from 'firebase-admin';

let db: admin.firestore.Firestore;

export const initializeFirebase = () => {
  try {
    admin.initializeApp({
      projectId: process.env.GCP_PROJECT_ID || 'mega-care-dev', // Use env var or default
    });
    db = admin.firestore();
    console.log('Firebase Admin SDK initialized successfully.');
  } catch (error: any) {
    console.error('Firebase Admin SDK initialization error:', error.message);
    process.exit(1);
  }
};

export const getFirestoreInstance = (): admin.firestore.Firestore => {
  if (!db) {
    throw new Error('Firestore has not been initialized. Call initializeFirebase first.');
  }
  return db;
};