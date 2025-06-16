import { Request, Response, NextFunction } from 'express';
import { getFirestoreInstance } from '../config/firebase';
import { Device } from '../interfaces';
import { toTimestamp } from '../utils/timestamp';

const db = getFirestoreInstance();

export const addDeviceToCustomer = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const patientId = req.params.patientId;
    const deviceData = req.body as Omit<Device, 'id'>;
    if (deviceData.addedDate) deviceData.addedDate = toTimestamp(deviceData.addedDate);

    const customerDocRef = db.collection('customers').doc(patientId);
    // You might want to check if the customer exists first
    // const customerDoc = await customerDocRef.get();
    // if (!customerDoc.exists) {
    //   return res.status(404).json({ status: 'error', message: 'Customer not found' });
    // }

    const deviceRef = await customerDocRef.collection('devices').add(deviceData);
    res.status(201).json({ id: deviceRef.id, ...deviceData });
  } catch (error) {
    next(error);
  }
};

export const getDevicesForCustomer = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const patientId = req.params.patientId;
    const snapshot = await db.collection('customers').doc(patientId).collection('devices').get();
    const devices: Device[] = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as Device));
    res.status(200).json(devices);
  } catch (error) {
    next(error);
  }
};