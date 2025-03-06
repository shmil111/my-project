import request from 'supertest';
import app from '../../app';

// Increase timeout for all tests in this file
jest.setTimeout(30000);

describe('Text Processing Endpoints', () => {
  describe('POST /text/sentiment', () => {
    it('should analyze sentiment', async () => {
      const response = await request(app)
        .post('/text/sentiment')
        .send({ text: 'I love this project!' })
        .set('Accept', 'application/json');
      
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('sentiment');
      expect(response.body).toHaveProperty('score');
    });
    
    it('should handle missing text parameter', async () => {
      const response = await request(app)
        .post('/text/sentiment')
        .send({})
        .set('Accept', 'application/json');
      
      expect(response.status).toBe(400);
    });
  });
  
  describe('POST /text/translate', () => {
    it('should translate text', async () => {
      const response = await request(app)
        .post('/text/translate')
        .send({ 
          text: 'Hello world',
          targetLanguage: 'es'
        })
        .set('Accept', 'application/json');
      
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('original', 'Hello world');
      expect(response.body).toHaveProperty('translated', 'Hola mundo');
      expect(response.body).toHaveProperty('sourceLanguage', 'en');
      expect(response.body).toHaveProperty('targetLanguage', 'es');
    });
    
    it('should handle missing text parameter', async () => {
      const response = await request(app)
        .post('/text/translate')
        .send({ targetLanguage: 'es' })
        .set('Accept', 'application/json');
      
      expect(response.status).toBe(400);
    });
    
    it('should handle missing targetLanguage parameter', async () => {
      const response = await request(app)
        .post('/text/translate')
        .send({ text: 'Hello world' })
        .set('Accept', 'application/json');
      
      expect(response.status).toBe(400);
    });
  });
  
  describe('POST /text/summarize', () => {
    it('should summarize text', async () => {
      const longText = 'This is a long text that needs to be summarized. It contains multiple sentences and ideas that should be condensed into a shorter version while maintaining the key points.';
      
      const response = await request(app)
        .post('/text/summarize')
        .send({ 
          text: longText, 
          maxLength: 50 
        })
        .set('Accept', 'application/json');
      
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('original', longText);
      expect(response.body).toHaveProperty('summary');
      expect(response.body).toHaveProperty('ratio');
      expect(response.body.summary.length).toBeLessThanOrEqual(longText.length);
    });
    
    it('should handle missing text parameter', async () => {
      const response = await request(app)
        .post('/text/summarize')
        .send({ maxLength: 50 })
        .set('Accept', 'application/json');
      
      expect(response.status).toBe(400);
    });
    
    it('should use default maxLength if not provided', async () => {
      const longText = 'This is a long text that needs to be summarized. It contains multiple sentences and ideas that should be condensed into a shorter version while maintaining the key points.';
      
      const response = await request(app)
        .post('/text/summarize')
        .send({ text: longText })
        .set('Accept', 'application/json');
      
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('summary');
    });
  });
}); 