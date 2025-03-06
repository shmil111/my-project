const { jest } = require('@jest/globals');

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
    strategy: 'eventual-consistency',
    conflictResolution: 'timestamp',
    maxLagAlertThreshold: 600
  }
};

// Before running tests, set up mocks
beforeEach(() => {
  jest.resetAllMocks();
  jest.doMock('../multi-region-config.js', () => mockConfig, { virtual: true });
  
  // Mock prompt responses
  require('inquirer').prompt
    .mockResolvedValueOnce({ confirm: true }) // First prompt confirmation
    .mockResolvedValueOnce({ databasesToSync: ['mongodb', 'redis'] }); // Database selection
});

describe('Data Synchronization Setup Script', () => {
  let setupSync;
  
  beforeEach(() => {
    // Reset module cache to ensure clean state
    jest.resetModules();
    
    // Dynamically import the module
    setupSync = require('../setup-sync');
  });
  
  test('should detect primary region from config if not specified', async () => {
    // Mock process.argv with no --primary-region flag
    const originalArgv = process.argv;
    process.argv = ['node', 'setup-sync.js', '--force'];
    
    // Call the function
    await setupSync.main();
    
    // Check if the primary region was correctly identified
    expect(setupSync.setupDatabaseSync).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ name: 'us-east' }),
      expect.anything(),
      expect.anything()
    );
    
    // Restore original argv
    process.argv = originalArgv;
  });
  
  test('should use specified primary region', async () => {
    // Mock process.argv with --primary-region flag
    const originalArgv = process.argv;
    process.argv = ['node', 'setup-sync.js', '--primary-region', 'eu-west', '--force'];
    
    // Temporarily change the primary database flag
    const originalConfig = {...mockConfig};
    mockConfig.regions[0].primaryDatabase = false;
    mockConfig.regions[1].primaryDatabase = true;
    
    // Call the function
    await setupSync.main();
    
    // Check if the specified primary region was used
    expect(setupSync.setupDatabaseSync).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ name: 'eu-west' }),
      expect.anything(),
      expect.anything()
    );
    
    // Restore original argv and config
    process.argv = originalArgv;
    mockConfig.regions = originalConfig.regions;
  });
  
  test('should use the specified synchronization strategy', async () => {
    // Mock process.argv with --strategy flag
    const originalArgv = process.argv;
    process.argv = ['node', 'setup-sync.js', '--strategy', 'strong-consistency', '--force'];
    
    // Call the function
    await setupSync.main();
    
    // Check if the specified strategy was used
    expect(setupSync.setupDatabaseSync).toHaveBeenCalledWith(
      expect.anything(),
      expect.anything(),
      expect.anything(),
      expect.objectContaining({ strategy: 'strong-consistency' })
    );
    
    // Restore original argv
    process.argv = originalArgv;
  });
  
  test('should set up synchronization for all selected databases', async () => {
    // Mock process.argv
    const originalArgv = process.argv;
    process.argv = ['node', 'setup-sync.js', '--force'];
    
    // Call the function
    await setupSync.main();
    
    // Check if setupDatabaseSync was called for both MongoDB and Redis
    expect(setupSync.setupDatabaseSync).toHaveBeenCalledTimes(2);
    expect(setupSync.setupDatabaseSync).toHaveBeenCalledWith(
      'mongodb',
      expect.anything(),
      expect.anything(),
      expect.anything()
    );
    expect(setupSync.setupDatabaseSync).toHaveBeenCalledWith(
      'redis',
      expect.anything(),
      expect.anything(),
      expect.anything()
    );
    
    // Restore original argv
    process.argv = originalArgv;
  });
  
  test('should update configuration file with new settings', async () => {
    // Mock process.argv
    const originalArgv = process.argv;
    process.argv = [
      'node', 
      'setup-sync.js', 
      '--strategy', 'strong-consistency',
      '--conflict-resolution', 'primary-wins',
      '--max-lag', '300',
      '--force'
    ];
    
    // Call the function
    await setupSync.main();
    
    // Check if updateConfigFile was called with correct parameters
    expect(setupSync.updateConfigFile).toHaveBeenCalledWith(
      mockConfig,
      expect.objectContaining({
        strategy: 'strong-consistency',
        conflictResolution: 'primary-wins',
        maxLagAlertThreshold: 300
      })
    );
    
    // Restore original argv
    process.argv = originalArgv;
  });
  
  test('should handle errors gracefully', async () => {
    // Mock setupDatabaseSync to throw an error
    setupSync.setupDatabaseSync = jest.fn().mockRejectedValue(new Error('Sync setup failed'));
    
    // Mock console.error
    console.error = jest.fn();
    
    // Call the function
    await setupSync.main();
    
    // Check error handling
    expect(console.error).toHaveBeenCalledWith(expect.stringContaining('Sync setup failed'));
  });
});

// Note: Similar to the previous test file, you'd need to modify setup-sync.js
// to export its internal functions for testing purposes. 