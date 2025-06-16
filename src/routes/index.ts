import { Router, Request, Response } from 'express';
import customerRoutes from './customer.routes';

const router = Router();

// --- Original Hello World Route ---
router.get('/', (req: Request, res: Response) => {
  // In a real app, this might be a health check or API info endpoint
  console.log(`Handling request: ${req.path}`);
  res.send('Hello World from Cloud Run! API is running.\n');
});

// Mount other resource routers
router.use('/customers', customerRoutes);

export default router;