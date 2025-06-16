import request from 'supertest';
import app from '../src/server'; // Adjusted import path

describe('GET /api/v1/', () => { // Path updated due to router prefix
  it('should respond with Hello World from Cloud Run!', async () => {
    const response = await request(app).get('/api/v1/');
    expect(response.status).toBe(200);
    expect(response.text).toBe('Hello World from Cloud Run! API is running.\n');
  });
});

// Optional: Close server after tests if it was started explicitly for tests
// For this setup, supertest handles server lifecycle per request.
// If you had a global server start/stop, you'd manage it here.
// afterAll((done) => {
//   // Close server if needed
// });