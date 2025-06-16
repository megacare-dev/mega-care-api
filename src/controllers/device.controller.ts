import { Request, Response, NextFunction } from 'express';
import { db, DeviceDoc } from '../config/firebase'; // Import db and DeviceDoc
import { Device } from '../interfaces';
import { toTimestamp } from '../utils/timestamp';
import { QueryDocumentSnapshot } from 'firebase-admin/firestore';

export const addDeviceToCustomer = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const patientId = req.params.patientId;
    const deviceData = req.body as DeviceDoc; // Data from body is DeviceDoc
    if (deviceData.addedDate) deviceData.addedDate = toTimestamp(deviceData.addedDate);

    // Optional: Check if customer exists
    const customerDoc = await db.customers.doc(patientId).get();
    if (!customerDoc.exists) {
      return res.status(404).json({ status: 'error', message: 'Customer not found' });
    }

    // You might want to check if the customer exists first
    // const customerDoc = await customerDocRef.get();
    // if (!customerDoc.exists) {
    //   return res.status(404).json({ status: 'error', message: 'Customer not found' });
    // }
    const deviceCollectionRef = db.customerDevices(patientId);
    const deviceRef = await deviceCollectionRef.add(deviceData);
    const newDevice: Device = { id: deviceRef.id, ...deviceData };
    res.status(201).json(newDevice);
  } catch (error) {
    next(error);
  }
};

export const getDevicesForCustomer = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const patientId = req.params.patientId;
    const deviceCollectionRef = db.customerDevices(patientId);
    const snapshot = await deviceCollectionRef.get();
    const devices: Device[] = snapshot.docs.map((doc: QueryDocumentSnapshot<DeviceDoc>) => { // doc.data() is DeviceDoc
      return { id: doc.id, ...doc.data() };
    });
    res.status(200).json(devices);
  } catch (error) {
    next(error);
  }
};