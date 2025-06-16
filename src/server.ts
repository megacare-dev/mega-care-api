import express from 'express';
import { initializeFirebase } from './config/firebase';
import mainRouter from './routes';
import { errorHandler } from './middlewares/errorHandler';

// Initialize Firebase Admin SDK
initializeFirebase();

const app = express();
app.use(express.json()); // Middleware to parse JSON bodies

// Cloud Run injects the PORT environment variable.
const port = process.env.PORT || '8080';

// Mount main router
app.use('/api/v1', mainRouter); // Prefix all routes with /api/v1

// Global error handler - should be the last middleware
app.use(errorHandler);

app.listen(port, () => {
  console.log(`Listening on port ${port}`);
}).on('error', (err) => {
  console.error(`Error starting server: ${err.message}`);
  process.exit(1);
});

export default app; // Export for testing purposes