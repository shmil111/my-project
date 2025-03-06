import request from 'supertest';
import app from '../../app';
import { TestContext } from '../../../testHelpers';

// Increase timeout for all tests in this file
jest.setTimeout(30000);

describe('Data API Endpoints', () => {
  const testContext = new TestContext();
  
  beforeEach(() => {
    // Reset the test context
    testContext.clear();
  });

  describe('POST /data', () => {
    it('should accept valid data', async () => {
      const validData = { name: 'Test Item' };
      const response = await request(app)
        .post('/data')
        .send(validData)
        .set('Accept', 'application/json');
      
      expect(response.status).toBe(201);
      expect(response.body).toHaveProperty('id');
      
      // Store the created item for later tests
      testContext.set('createdItem', response.body);
    });

    it('should reject invalid data', async () => {
      const invalidData = { name: 123 };
      const response = await request(app)
        .post('/data')
        .send(invalidData)
        .set('Accept', 'application/json');
      
      expect(response.status).toBe(400);
    });
  });

  describe('GET /data', () => {
    it('should return array of items', async () => {
      // First create an item if not already created
      if (!testContext.has('createdItem')) {
        const createResponse = await request(app)
          .post('/data')
          .send({ name: 'Test Item for GET' })
          .set('Accept', 'application/json');
          
        testContext.set('createdItem', createResponse.body);
      }
        
      const response = await request(app).get('/data');
      
      expect(response.status).toBe(200);
      expect(Array.isArray(response.body)).toBe(true);
    });
  });
  
  describe('GET /data/:id', () => {
    it('should return item by ID', async () => {
      // First create an item if not already created
      if (!testContext.has('createdItem')) {
        const createResponse = await request(app)
          .post('/data')
          .send({ name: 'Test Item for GET by ID' })
          .set('Accept', 'application/json');
          
        testContext.set('createdItem', createResponse.body);
      }
        
      const id = testContext.get<any>('createdItem').id;
      
      // Then get it by ID
      const response = await request(app).get(`/data/${id}`);
      
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('id', id);
    });
    
    it('should return 404 for non-existent ID', async () => {
      const response = await request(app).get('/data/9999');
      
      expect(response.status).toBe(404);
    });
  });
  
  describe('PUT /data/:id', () => {
    it('should update existing item', async () => {
      // First create an item if not already created
      if (!testContext.has('createdItem')) {
        const createResponse = await request(app)
          .post('/data')
          .send({ name: 'Test Item for PUT' })
          .set('Accept', 'application/json');
          
        testContext.set('createdItem', createResponse.body);
      }
        
      const id = testContext.get<any>('createdItem').id;
      
      // Then update it
      const updateData = { name: 'Updated Test Item' };
      const response = await request(app)
        .put(`/data/${id}`)
        .send(updateData)
        .set('Accept', 'application/json');
      
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('name', updateData.name);
      
      // Update the stored item
      testContext.set('createdItem', response.body);
    });
    
    it('should return 404 for non-existent ID', async () => {
      const response = await request(app)
        .put('/data/9999')
        .send({ name: 'Not Found' })
        .set('Accept', 'application/json');
      
      expect(response.status).toBe(404);
    });
  });
  
  describe('DELETE /data/:id', () => {
    it('should delete existing item', async () => {
      // First create an item if not already created
      if (!testContext.has('createdItem')) {
        const createResponse = await request(app)
          .post('/data')
          .send({ name: 'Test Item for DELETE' })
          .set('Accept', 'application/json');
          
        testContext.set('createdItem', createResponse.body);
      }
        
      const id = testContext.get<any>('createdItem').id;
      
      // Then delete it
      const response = await request(app).delete(`/data/${id}`);
      
      expect(response.status).toBe(200);
      
      // Verify it's gone
      const getResponse = await request(app).get(`/data/${id}`);
      expect(getResponse.status).toBe(404);
      
      // Clear the stored item
      testContext.clear();
    });
    
    it('should return 404 for non-existent ID', async () => {
      const response = await request(app).delete('/data/9999');
      
      expect(response.status).toBe(404);
    });
  });
}); 