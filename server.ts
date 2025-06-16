import express, { Request, Response } from 'express';
import { Customer, Device, toTimestamp } from './interfaces'; // Assuming interfaces.ts is in the same directory
import { initializeFirebase, getDb } from './src/config/firebase'; // Adjust path if needed

// Initialize Firebase Admin SDK
// This should be one of the first things your application does.
initializeFirebase();

const db = getDb(); // Get the initialized Firestore instance
const customersCollection = db.collection('customers');

const app = express();
app.use(express.json()); // Middleware to parse JSON bodies

// Cloud Run injects the PORT environment variable.
const port = process.env.PORT || 8080;

// --- Original Hello World Route ---
app.get('/', (req: Request, res: Response) => {
  console.log(`Handling request: ${req.path}`);
  res.send('Hello World from Cloud Run!\n');
});

// --- Customers CRUD ---

// Create Customer
app.post('/customers', async (req: Request, res: Response) => {
  try {
    const customerData = req.body as Omit<Customer, 'id'>;
    // Convert date strings/Date objects to Firestore Timestamps
    if (customerData.dob) customerData.dob = toTimestamp(customerData.dob);
    if (customerData.setupDate) customerData.setupDate = toTimestamp(customerData.setupDate);

    const docRef = await customersCollection.add(customerData);
    res.status(201).send({ id: docRef.id, ...customerData });
  } catch (error: any) {
    console.error('Error creating customer:', error);
    res.status(500).send({ error: 'Failed to create customer', details: error.message });
  }
});

// Get all Customers (consider pagination for large datasets)
app.get('/customers', async (req: Request, res: Response) => {
  try {
    const snapshot = await customersCollection.get();
    const customers: Customer[] = [];
    snapshot.forEach(doc => customers.push({ id: doc.id, ...doc.data() } as Customer));
    res.status(200).send(customers);
  } catch (error: any) {
    console.error('Error getting customers:', error);
    res.status(500).send({ error: 'Failed to get customers', details: error.message });
  }
});

// Get Customer by ID
app.get('/customers/:patientId', async (req: Request, res: Response) => {
  try {
    const patientId = req.params.patientId;
    const doc = await customersCollection.doc(patientId).get();
    if (!doc.exists) {
      return res.status(404).send({ error: 'Customer not found' });
    }
    res.status(200).send({ id: doc.id, ...doc.data() } as Customer);
  } catch (error: any) {
    console.error('Error getting customer by ID:', error);
    res.status(500).send({ error: 'Failed to get customer', details: error.message });
  }
});

// Update Customer
app.put('/customers/:patientId', async (req: Request, res: Response) => {
  try {
    const patientId = req.params.patientId;
    const customerData = req.body as Partial<Omit<Customer, 'id'>>;

    // Convert date strings/Date objects to Firestore Timestamps if present
    if (customerData.dob) customerData.dob = toTimestamp(customerData.dob);
    if (customerData.setupDate) customerData.setupDate = toTimestamp(customerData.setupDate);

    await customersCollection.doc(patientId).update(customerData);
    res.status(200).send({ id: patientId, message: 'Customer updated successfully' });
  } catch (error: any) {
    console.error('Error updating customer:', error);
    if (error.code === 5) { // Firestore 'NOT_FOUND' error code
        return res.status(404).send({ error: 'Customer not found to update' });
    }
    res.status(500).send({ error: 'Failed to update customer', details: error.message });
  }
});

// Delete Customer
app.delete('/customers/:patientId', async (req: Request, res: Response) => {
  try {
    const patientId = req.params.patientId;
    // Note: Deleting a document does not delete its subcollections automatically.
    // You'd need to implement recursive deletion if required.
    await customersCollection.doc(patientId).delete();
    res.status(200).send({ id: patientId, message: 'Customer deleted successfully' });
  } catch (error: any) {
    console.error('Error deleting customer:', error);
     if (error.code === 5) { // Firestore 'NOT_FOUND' error code
        return res.status(404).send({ error: 'Customer not found to delete' });
    }
    res.status(500).send({ error: 'Failed to delete customer', details: error.message });
  }
});

// --- Devices Sub-collection CRUD (Example for one sub-collection) ---
// Path: /customers/{patientId}/devices

// Add a device to a customer
app.post('/customers/:patientId/devices', async (req: Request, res: Response) => {
  try {
    const patientId = req.params.patientId;
    const deviceData = req.body as Omit<Device, 'id'>;
    if (deviceData.addedDate) deviceData.addedDate = toTimestamp(deviceData.addedDate);

    const deviceRef = await customersCollection.doc(patientId).collection('devices').add(deviceData);
    res.status(201).send({ id: deviceRef.id, ...deviceData });
  } catch (error: any)
 {
    console.error(`Error adding device to customer ${patientId}:`, error);
    res.status(500).send({ error: 'Failed to add device', details: error.message });
  }
});

// Get all devices for a customer
app.get('/customers/:patientId/devices', async (req: Request, res: Response) => {
  try {
    const patientId = req.params.patientId;
    const snapshot = await customersCollection.doc(patientId).collection('devices').get();
    const devices: Device[] = [];
    snapshot.forEach(doc => devices.push({ id: doc.id, ...doc.data() } as Device));
    res.status(200).send(devices);
  } catch (error: any) {
    console.error(`Error getting devices for customer ${patientId}:`, error);
    res.status(500).send({ error: 'Failed to get devices', details: error.message });
  }
});

// You would continue this pattern for GET by ID, PUT, and DELETE for devices,
// and then replicate for masks, airTubing, and dailyReports sub-collections.

app.listen(port, '0.0.0.0', () => { // Explicitly listen on all IPv4 interfaces
  console.log(`Server listening on host 0.0.0.0 and port ${port}`);
}).on('error', (err) => {
  console.error(`Error starting server: ${err.message}`);
  process.exit(1);
});
export default app; // Export for testing purposes