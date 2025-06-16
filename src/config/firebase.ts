import * as admin from 'firebase-admin';

let dbInstance: admin.firestore.Firestore;

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
      dbInstance = admin.firestore();
    } catch (error: any) {
      console.error('Firebase Admin SDK initialization error:', error.message);
      process.exit(1); // Exit if critical initialization fails
    }
  }
  dbInstance = admin.app().firestore(); // Get firestore instance from default app
};

export const getDb = (): admin.firestore.Firestore => {
  if (!dbInstance) {
    // This might happen if initializeFirebase() wasn't called at startup
    // or if initialization failed and process didn't exit (if process.exit was removed).
    throw new Error('Firestore has not been initialized. Call initializeFirebase() first.');
  }
  return dbInstance;
};