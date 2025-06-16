import { Request, Response, NextFunction } from 'express';
import { getFirestoreInstance } from '../config/firebase';
import { Customer } from '../interfaces';
import { toTimestamp } from '../utils/timestamp';

const db = getFirestoreInstance();
const customersCollection = db.collection('customers');

export const createCustomer = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const customerData = req.body as Omit<Customer, 'id'>;
    if (customerData.dob) customerData.dob = toTimestamp(customerData.dob);
    if (customerData.setupDate) customerData.setupDate = toTimestamp(customerData.setupDate);

    const docRef = await customersCollection.add(customerData);
    res.status(201).json({ id: docRef.id, ...customerData });
  } catch (error) {
    next(error);
  }
};

export const getAllCustomers = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const snapshot = await customersCollection.get();
    const customers: Customer[] = [];
    snapshot.forEach(doc => customers.push({ id: doc.id, ...doc.data() } as Customer));
    res.status(200).json(customers);
  } catch (error) {
    next(error);
  }
};

export const getCustomerById = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const patientId = req.params.patientId;
    const doc = await customersCollection.doc(patientId).get();
    if (!doc.exists) {
      return res.status(404).json({ status: 'error', message: 'Customer not found' });
    }
    res.status(200).json({ id: doc.id, ...doc.data() } as Customer);
  } catch (error) {
    next(error);
  }
};

export const updateCustomer = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const patientId = req.params.patientId;
    const customerData = req.body as Partial<Omit<Customer, 'id'>>;

    if (customerData.dob) customerData.dob = toTimestamp(customerData.dob);
    if (customerData.setupDate) customerData.setupDate = toTimestamp(customerData.setupDate);

    const docRef = customersCollection.doc(patientId);
    const doc = await docRef.get();
    if (!doc.exists) {
        return res.status(404).json({ status: 'error', message: 'Customer not found to update' });
    }

    await docRef.update(customerData);
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
    const docRef = customersCollection.doc(patientId);
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