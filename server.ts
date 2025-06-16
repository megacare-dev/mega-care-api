import express, { Request, Response } from 'express';

const app = express();

// Cloud Run injects the PORT environment variable.
const port = process.env.PORT || 8080;

app.get('/', (req: Request, res: Response) => {
  console.log(`Handling request: ${req.path}`);
  res.send('Hello World from Cloud Run!\n');
});

app.listen(port, () => {
  console.log(`Listening on port ${port}`);
}).on('error', (err) => {
  console.error(`Error starting server: ${err.message}`);
  process.exit(1);
});

export default app; // Export for testing purposes