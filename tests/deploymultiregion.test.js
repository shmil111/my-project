const { jest } = require('@jest/globals');
const path = require('path');
const fs = require('fs');

// Mock dependencies
jest.mock('child_process', () => ({
  execSync: jest.fn()
}));
jest.mock('ora', () => () => ({
  start: jest.fn().mockReturnThis(),
  succeed: jest.fn().mockReturnThis(),
  fail: jest.fn().mockReturnThis(),
  info: jest.fn().mockReturnThis()
}));
jest.mock('inquirer', () => ({
  prompt: jest.fn()
}));

// Mock config file
const mockConfig = {
  regions: [
    {
      name: 'us-east',
      provider: 'aws',
      region: 'us-east-1',
      primaryDatabase: true
    },
    {
      name: 'eu-west',
      provider: 'aws',
      region: 'eu-west-1',
      primaryDatabase: false
    }
  ],
  synchronization: {
    interval: 300,
    strategy: 'eventual-consistency'
  },
  domains: {
    global: 'test.example.com',
    regions: {
      'us-east': 'us.test.example.com',
      'eu-west': 'eu.test.example.com'
    }
  },
  trafficManagement: {
    method: 'latency-based',
    healthCheckInterval: 60,
    failoverThreshold: 3
  }
};

// Mock file system
jest.mock('fs', () => ({
  writeFileSync: jest.fn(),
  readFileSync: jest.fn()
}));

// Before running tests, set up mocks
beforeEach(() => {
  jest.resetAllMocks();
  jest.doMock('../multi-region-config.js', () => mockConfig, { virtual: true });
  
  // Mock prompt responses
  require('inquirer').prompt.mockResolvedValue({ confirm: true });
});

describe('Multi-Region Deployment Script', () => {
  let deployMultiRegion;
  
  beforeEach(() => {
    // Reset module cache to ensure clean state
    jest.resetModules();
    
    // We need to dynamically import the module to allow mocking
    // Note: In actual implementation, you'd need to make the module more testable
    // by exporting its functions
    deployMultiRegion = require('../deploy-multi-region');
  });
  
  test('should load configuration correctly', async () => {
    // Set up mocks for this test
    const mockRequire = jest.fn().mockReturnValue(mockConfig);
    jest.mock('../multi-region-config.js', () => mockRequire(), { virtual: true });
    
    // Call the function (assuming main is exported - you may need to modify your script)
    await deployMultiRegion.main();
    
    // Assertions
    expect(mockRequire).toHaveBeenCalled();
  });
  
  test('should deploy to all regions when no specific regions are specified', async () => {
    // Mock process.argv to simulate no --regions flag
    const originalArgv = process.argv;
    process.argv = ['node', 'deploy-multi-region.js', '--force'];
    
    // Call the function
    await deployMultiRegion.main();
    
    // Check if deployToRegion was called for both regions
    // Note: This assumes your code exports or exposes deployToRegion function
    expect(deployMultiRegion.deployToRegion).toHaveBeenCalledTimes(2);
    
    // Restore original argv
    process.argv = originalArgv;
  });
  
  test('should only deploy to specified regions', async () => {
    // Mock process.argv to simulate --regions flag
    const originalArgv = process.argv;
    process.argv = ['node', 'deploy-multi-region.js', '--regions', 'us-east', '--force'];
    
    // Call the function
    await deployMultiRegion.main();
    
    // Check if deployToRegion was called only for the specified region
    expect(deployMultiRegion.deployToRegion).toHaveBeenCalledTimes(1);
    expect(deployMultiRegion.deployToRegion).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'us-east' }),
      expect.anything(),
      expect.anything()
    );
    
    // Restore original argv
    process.argv = originalArgv;
  });
  
  test('should set up DNS and data sync when specified', async () => {
    // Mock process.argv
    const originalArgv = process.argv;
    process.argv = ['node', 'deploy-multi-region.js', '--setup-dns', '--setup-sync', '--force'];
    
    // Call the function
    await deployMultiRegion.main();
    
    // Check if setupDns and setupDataSync were called
    expect(deployMultiRegion.setupDns).toHaveBeenCalled();
    expect(deployMultiRegion.setupDataSync).toHaveBeenCalled();
    
    // Restore original argv
    process.argv = originalArgv;
  });
  
  test('should handle deployment errors gracefully', async () => {
    // Mock deployToRegion to throw an error
    deployMultiRegion.deployToRegion = jest.fn().mockRejectedValue(new Error('Deployment failed'));
    
    // Call the function
    await deployMultiRegion.main();
    
    // Check error handling (this would depend on your implementation)
    // For example, you might check if a certain error message was logged
    expect(console.error).toHaveBeenCalledWith(expect.stringContaining('Deployment failed'));
  });
});

// Note: To make this test file work, you'd need to modify your deploy-multi-region.js
// to export the internal functions for testing, or refactor it to be more testable
// by separating pure logic from side effects and CLI interactions. 