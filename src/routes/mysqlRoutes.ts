import express from 'express';
import { getMySQLData, insertMySQLData, updateMySQLData, deleteMySQLData, getMySQLDataById } from '../controllers/mysqlController';

const router = express.Router();

router.get('/data', getMySQLData);
router.get('/data/:id', getMySQLDataById);
router.post('/data', insertMySQLData);
router.put('/data/:id', updateMySQLData);
router.delete('/data/:id', deleteMySQLData);

export default router; 