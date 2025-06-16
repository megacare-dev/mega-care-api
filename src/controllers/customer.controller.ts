import { Request, Response, NextFunction } from 'express';
import { db, CustomerDoc } from '../config/firebase'; // Import db and CustomerDoc
import { Customer } from '../interfaces';
import { toTimestamp } from '../utils/timestamp';
// No longer need QueryDocumentSnapshot, DocumentData for basic doc.data() typing if using the converter fully.
// However, QueryDocumentSnapshot might still be useful if directly working with snapshot properties.
import { QueryDocumentSnapshot } from 'firebase-admin/firestore';
export const createCustomer = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const customerData = req.body as Omit<Customer, 'id'>;
    if (customerData.dob) customerData.dob = toTimestamp(customerData.dob);
    if (customerData.setupDate) customerData.setupDate = toTimestamp(customerData.setupDate);

    const docRef = await customersCollection.add(customerData);
    // Construct the full customer object to return, including the new ID
    const newCustomer: Customer = { id: docRef.id, ...customerData };
    res.status(201).json(newCustomer);
  } catch (error) {
    next(error);
  }
};

export const getAllCustomers = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const snapshot = await db.customers.get();
    const customers: Customer[] = [];
    snapshot.forEach((doc: QueryDocumentSnapshot<CustomerDoc>) => { // doc.data() is now CustomerDoc
      customers.push({ id: doc.id, ...doc.data() });
    });
    res.status(200).json(customers);
  } catch (error) {
    next(error);
  }
};

export const getCustomerById = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const patientId = req.params.patientId;
    const doc = await db.customers.doc(patientId).get();
    if (!doc.exists) {
      return res.status(404).json({ status: 'error', message: 'Customer not found' });
    }
    const customerData = doc.data(); // customerData is CustomerDoc | undefined
    res.status(200).json({ id: doc.id, ...customerData });
  } catch (error) {
    next(error);
  }
};

export const updateCustomer = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const patientId = req.params.patientId;
    const customerUpdateData = req.body as Partial<CustomerDoc>;

    // Ensure toTimestamp is applied to date fields if they are present in the update
    if (customerUpdateData.dob) customerUpdateData.dob = toTimestamp(customerUpdateData.dob);
    if (customerUpdateData.setupDate) customerUpdateData.setupDate = toTimestamp(customerUpdateData.setupDate);

    const docRef = db.customers.doc(patientId);
    const doc = await docRef.get();
    if (!doc.exists) {
        return res.status(404).json({ status: 'error', message: 'Customer not found to update' });
    }

    await docRef.set(customerUpdateData, { merge: true }); // Use set with merge for partial updates with converters
    res.status(200).json({ id: patientId, message: 'Customer updated successfully' });
  } catch (error) {
    next(error);
  }
};

export const deleteCustomer = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const patientId = req.params.patientId;
    // Note: Deleting a document does not delete its subcollections automatically.
    // You'd need to implement recursive deletion if required.
    const docRef = db.customers.doc(patientId);
    const doc = await docRef.get();
    if (!doc.exists) {
        return res.status(404).json({ status: 'error', message: 'Customer not found to delete' });
    }

    await docRef.delete();
    res.status(200).json({ id: patientId, message: 'Customer deleted successfully' });
  } catch (error) {
    next(error);
  }
};