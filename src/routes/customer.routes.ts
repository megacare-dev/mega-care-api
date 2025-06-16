import { Router } from 'express';
import * as customerController from '../controllers/customer.controller';
import * as deviceController from '../controllers/device.controller';

const router = Router();

// Customer routes
router.post('/', customerController.createCustomer);
router.get('/', customerController.getAllCustomers);
router.get('/:patientId', customerController.getCustomerById);
router.put('/:patientId', customerController.updateCustomer);
router.delete('/:patientId', customerController.deleteCustomer);

// --- Devices Sub-collection Routes ---
// Mounted under /customers/:patientId/devices
const deviceRouter = Router({ mergeParams: true }); // mergeParams allows access to :patientId

deviceRouter.post('/', deviceController.addDeviceToCustomer);
deviceRouter.get('/', deviceController.getDevicesForCustomer);
// TODO: Add GET /:deviceId, PUT /:deviceId, DELETE /:deviceId for devices

// Mount the device router
router.use('/:patientId/devices', deviceRouter);

// You would continue this pattern for masks, airTubing, and dailyReports sub-collections,
// potentially creating separate controller and router files for them if they become complex.

export default router;