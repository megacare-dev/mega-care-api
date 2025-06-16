import express, { Request, Response } from 'express';
import { Customer, Device, toTimestamp } from './interfaces'; // Assuming interfaces.ts is in the same directory
import { initializeFirebase, db, CustomerDoc, DeviceDoc } from './src/config/firebase'; // Adjust path and import db, CustomerDoc, DeviceDoc

// Initialize Firebase Admin SDK
// This should be one of the first things your application does.
initializeFirebase();

// const oldDb = getDb(); // No longer needed

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
    const customerDocData = req.body as CustomerDoc;
    // Convert date strings/Date objects to Firestore Timestamps
    if (customerDocData.dob) customerDocData.dob = toTimestamp(customerDocData.dob);
    if (customerDocData.setupDate) customerDocData.setupDate = toTimestamp(customerDocData.setupDate);

    const docRef = await db.customers.add(customerDocData);
    const newCustomer: Customer = { id: docRef.id, ...customerDocData };
    res.status(201).send(newCustomer);
  } catch (error: any) {
    console.error('Error creating customer:', error);
    res.status(500).send({ error: 'Failed to create customer', details: error.message });
  }
});

// Get all Customers (consider pagination for large datasets)
app.get('/customers', async (req: Request, res: Response) => {
  try {
    const snapshot = await db.customers.get();
    const customers: Customer[] = [];
    snapshot.forEach(doc => { // doc.data() is CustomerDoc
      customers.push({ id: doc.id, ...doc.data() });
    });
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
    const doc = await db.customers.doc(patientId).get();
    if (!doc.exists) {
      return res.status(404).send({ error: 'Customer not found' });
    }
    const customerDocData = doc.data(); // customerDocData is CustomerDoc | undefined
    if (customerDocData) {
      const customer: Customer = { id: doc.id, ...customerDocData };
      res.status(200).send(customer);
    } else {
      // Should be caught by !doc.exists, but as a safeguard
      return res.status(404).send({ error: 'Customer data not found' });
    }
  } catch (error: any) {
    console.error('Error getting customer by ID:', error);
    res.status(500).send({ error: 'Failed to get customer', details: error.message });
  }
});

// Update Customer
app.put('/customers/:patientId', async (req: Request, res: Response) => {
  try {
    const patientId = req.params.patientId;
    const customerUpdateData = req.body as Partial<CustomerDoc>;

    if (customerUpdateData.dob) customerUpdateData.dob = toTimestamp(customerUpdateData.dob);
    if (customerUpdateData.setupDate) customerUpdateData.setupDate = toTimestamp(customerUpdateData.setupDate);

    // For converters, using set with merge:true is often more straightforward for partial updates
    await db.customers.doc(patientId).set(customerUpdateData, { merge: true });
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
    await db.customers.doc(patientId).delete();
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
    const deviceDocData = req.body as DeviceDoc;
    if (deviceDocData.addedDate) deviceDocData.addedDate = toTimestamp(deviceDocData.addedDate);

    const deviceRef = await db.customerDevices(patientId).add(deviceDocData);
    const newDevice: Device = { id: deviceRef.id, ...deviceDocData };
    res.status(201).send(newDevice);
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
    const snapshot = await db.customerDevices(patientId).get();
    const devices: Device[] = [];
    snapshot.forEach(doc => { // doc.data() is DeviceDoc
      devices.push({ id: doc.id, ...doc.data() });
    });
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