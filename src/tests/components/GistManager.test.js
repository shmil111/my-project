/**
 * Gist Manager Component Tests
 * 
 * Tests for the Gist Manager UI component, which integrates with GitHub Gists
 */

// Import testing libraries
import { jest } from '@jest/globals';
import { JSDOM } from 'jsdom';

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn(key => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn(key => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    })
  };
})();

// Mock fetch API
global.fetch = jest.fn();

describe('GistManager Component', () => {
  let dom;
  let window;
  let document;
  let GistManager;
  let container;
  
  beforeEach(async () => {
    // Set up a DOM environment
    dom = new JSDOM(`
      <!DOCTYPE html>
      <html>
        <head></head>
        <body>
          <div id="gist-manager-container"></div>
        </body>
      </html>
    `, { url: 'http://localhost/' });
    
    window = dom.window;
    document = window.document;
    
    // Mock DOM globals
    global.window = window;
    global.document = document;
    global.HTMLElement = window.HTMLElement;
    global.localStorage = localStorageMock;
    
    // Mock window.showNotification
    window.showNotification = jest.fn();
    
    // Import GistManager class dynamically
    const gistManagerModule = await import('@public/js/components/gistManager.js');
    GistManager = gistManagerModule.GistManager;
    
    // Create a container for testing
    container = document.getElementById('gist-manager-container');
    
    // Reset mocks
    jest.clearAllMocks();
    localStorage.getItem.mockReturnValue(null);
    fetch.mockReset();
  });
  
  afterEach(() => {
    dom.window.close();
    delete global.window;
    delete global.document;
    delete global.HTMLElement;
  });
  
  test('should initialize the UI with correct structure', () => {
    // Arrange
    // Mock profile API response
    fetch.mockImplementationOnce(() => 
      Promise.reject(new Error('Failed to load profile'))
    );
    
    // Mock gists API response
    fetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      })
    );
    
    // Act
    const gistManager = new GistManager('gist-manager-container');
    
    // Assert
    expect(container.classList.contains('gist-manager')).toBeTruthy();
    expect(container.querySelector('.gist-manager__header')).not.toBeNull();
    expect(container.querySelector('.gist-manager__filter-bar')).not.toBeNull();
    expect(container.querySelector('.gist-manager__content')).not.toBeNull();
    expect(container.querySelector('.gist-manager__pagination')).not.toBeNull();
    expect(container.querySelector('.gist-manager__modal')).not.toBeNull();
  });
  
  test('should render gists correctly when loaded', async () => {
    // Arrange
    const mockGists = [
      {
        id: 'gist1',
        description: 'Test Gist 1',
        public: true,
        files: {
          'file1.js': { content: 'console.log("hello");' }
        },
        updated_at: '2023-01-01T00:00:00Z'
      },
      {
        id: 'gist2',
        description: 'Test Gist 2',
        public: false,
        files: {
          'file2.py': { content: 'print("hello")' }
        },
        updated_at: '2023-01-02T00:00:00Z'
      }
    ];
    
    // Mock profile API response
    fetch.mockImplementationOnce(() => 
      Promise.reject(new Error('Failed to load profile'))
    );
    
    // Mock gists API response
    fetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockGists)
      })
    );
    
    // Act
    const gistManager = new GistManager('gist-manager-container');
    
    // Wait for async operations to complete
    await new Promise(resolve => setTimeout(resolve, 0));
    
    // Assert
    const gistCards = container.querySelectorAll('.gist-card');
    expect(gistCards.length).toBe(2);
    
    // Check first gist card
    expect(gistCards[0].querySelector('.gist-card__title').textContent).toBe('Test Gist 1');
    expect(gistCards[0].querySelector('.gist-card__visibility').textContent.trim()).toBe('Public');
    expect(gistCards[0].querySelector('.gist-card__files').textContent.trim()).toContain('1 file');
    
    // Check second gist card
    expect(gistCards[1].querySelector('.gist-card__title').textContent).toBe('Test Gist 2');
    expect(gistCards[1].querySelector('.gist-card__visibility').textContent.trim()).toBe('Private');
    expect(gistCards[1].querySelector('.gist-card__files').textContent.trim()).toContain('1 file');
  });
  
  test('should show empty message when no gists are found', async () => {
    // Arrange
    // Mock profile API response
    fetch.mockImplementationOnce(() => 
      Promise.reject(new Error('Failed to load profile'))
    );
    
    // Mock gists API response with empty array
    fetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      })
    );
    
    // Act
    const gistManager = new GistManager('gist-manager-container');
    
    // Wait for async operations to complete
    await new Promise(resolve => setTimeout(resolve, 0));
    
    // Assert
    const emptyMessage = container.querySelector('.gist-manager__empty');
    expect(emptyMessage.classList.contains('hidden')).toBeFalsy();
    expect(emptyMessage.querySelector('h3').textContent).toBe('No gists found');
  });
  
  test('should handle filter change', async () => {
    // Arrange
    // Mock profile API response
    fetch.mockImplementationOnce(() => 
      Promise.reject(new Error('Failed to load profile'))
    );
    
    // Mock initial gists API response
    fetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([{ id: 'gist1' }])
      })
    );
    
    // Mock filtered gists API response
    fetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([{ id: 'gist2' }])
      })
    );
    
    // Act
    const gistManager = new GistManager('gist-manager-container');
    
    // Wait for async operations to complete
    await new Promise(resolve => setTimeout(resolve, 0));
    
    // Click the public filter button
    const publicFilterButton = container.querySelector('[data-filter="public"]');
    publicFilterButton.click();
    
    // Wait for async operations to complete
    await new Promise(resolve => setTimeout(resolve, 0));
    
    // Assert
    expect(fetch).toHaveBeenCalledTimes(3);
    expect(publicFilterButton.classList.contains('active')).toBeTruthy();
    
    // The original "all" button should no longer be active
    const allFilterButton = container.querySelector('[data-filter="all"]');
    expect(allFilterButton.classList.contains('active')).toBeFalsy();
  });
  
  test('should handle pagination', async () => {
    // Arrange
    // Mock profile API response
    fetch.mockImplementationOnce(() => 
      Promise.reject(new Error('Failed to load profile'))
    );
    
    // Mock initial gists API response with 20 items and pagination info
    const mockGists = Array(9).fill().map((_, i) => ({ id: `gist${i}` }));
    fetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          gists: mockGists,
          total: 20
        })
      })
    );
    
    // Mock next page API response
    const mockNextPageGists = Array(9).fill().map((_, i) => ({ id: `gist${i + 9}` }));
    fetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          gists: mockNextPageGists,
          total: 20
        })
      })
    );
    
    // Act
    const gistManager = new GistManager('gist-manager-container');
    
    // Wait for async operations to complete
    await new Promise(resolve => setTimeout(resolve, 0));
    
    // Get pagination info before clicking next
    const currentPageBefore = container.querySelector('.current-page').textContent;
    const totalPages = container.querySelector('.total-pages').textContent;
    
    // Click the next page button
    const nextButton = container.querySelector('[data-action="next"]');
    nextButton.click();
    
    // Wait for async operations to complete
    await new Promise(resolve => setTimeout(resolve, 0));
    
    // Get pagination info after clicking next
    const currentPageAfter = container.querySelector('.current-page').textContent;
    
    // Assert
    expect(currentPageBefore).toBe('1');
    expect(totalPages).toBe('3'); // 20 items / 9 per page = 3 pages (rounded up)
    expect(currentPageAfter).toBe('2');
    expect(fetch).toHaveBeenCalledTimes(3);
  });
  
  test('should open and close create gist modal', () => {
    // Arrange
    // Mock profile API response
    fetch.mockImplementationOnce(() => 
      Promise.reject(new Error('Failed to load profile'))
    );
    
    // Mock gists API response
    fetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      })
    );
    
    // Act
    const gistManager = new GistManager('gist-manager-container');
    
    // Get modal elements
    const modal = container.querySelector('.gist-manager__modal');
    const newGistButton = container.querySelector('.gist-manager__new-gist');
    const closeButton = container.querySelector('.gist-manager__modal-close');
    
    // Check initial state
    expect(modal.classList.contains('hidden')).toBeTruthy();
    
    // Open modal
    newGistButton.click();
    expect(modal.classList.contains('hidden')).toBeFalsy();
    
    // Close modal
    closeButton.click();
    expect(modal.classList.contains('hidden')).toBeTruthy();
  });
  
  test('should add and remove file inputs in create gist modal', () => {
    // Arrange
    // Mock profile API response
    fetch.mockImplementationOnce(() => 
      Promise.reject(new Error('Failed to load profile'))
    );
    
    // Mock gists API response
    fetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      })
    );
    
    // Act
    const gistManager = new GistManager('gist-manager-container');
    
    // Open modal
    container.querySelector('.gist-manager__new-gist').click();
    
    // Get file container
    const filesContainer = container.querySelector('.gist-manager__files-container');
    const addFileButton = container.querySelector('.gist-manager__add-file');
    
    // Check initial state
    const initialFileCount = filesContainer.querySelectorAll('.gist-manager__file').length;
    expect(initialFileCount).toBe(1);
    
    // Add a new file
    addFileButton.click();
    const afterAddFileCount = filesContainer.querySelectorAll('.gist-manager__file').length;
    expect(afterAddFileCount).toBe(2);
    
    // Get the remove button for the second file
    const removeFileButton = filesContainer.querySelectorAll('.gist-manager__file')[1].querySelector('.gist-manager__remove-file');
    
    // Remove the second file
    removeFileButton.click();
    const afterRemoveFileCount = filesContainer.querySelectorAll('.gist-manager__file').length;
    expect(afterRemoveFileCount).toBe(1);
  });
  
  test('should attempt to create a gist when save button is clicked', async () => {
    // Arrange
    // Mock profile API response
    fetch.mockImplementationOnce(() => 
      Promise.reject(new Error('Failed to load profile'))
    );
    
    // Mock gists API response
    fetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      })
    );
    
    // Mock create gist API response
    fetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ id: 'new-gist-id' })
      })
    );
    
    // Mock gists API response after creation
    fetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([{ id: 'new-gist-id' }])
      })
    );
    
    // Act
    const gistManager = new GistManager('gist-manager-container');
    
    // Wait for async operations to complete
    await new Promise(resolve => setTimeout(resolve, 0));
    
    // Open modal
    container.querySelector('.gist-manager__new-gist').click();
    
    // Fill in the form
    const descInput = container.querySelector('#gist-description');
    const filenameInput = container.querySelector('.gist-manager__filename');
    const contentInput = container.querySelector('.gist-manager__file-content');
    const saveButton = container.querySelector('.gist-manager__save');
    
    descInput.value = 'Test Gist';
    filenameInput.value = 'test.js';
    contentInput.value = 'console.log("Hello, world!");';
    
    // Submit the form
    saveButton.click();
    
    // Wait for async operations to complete
    await new Promise(resolve => setTimeout(resolve, 0));
    
    // Assert
    expect(fetch).toHaveBeenCalledTimes(4);
    
    // Check the third call which should be the create gist API call
    const createCallArgs = fetch.mock.calls[2];
    expect(createCallArgs[0]).toBe('/gists');
    expect(createCallArgs[1].method).toBe('POST');
    
    // Parse the request body
    const requestBody = JSON.parse(createCallArgs[1].body);
    expect(requestBody.description).toBe('Test Gist');
    expect(requestBody.public).toBeTruthy();
    expect(requestBody.files['test.js']).toBeDefined();
    expect(requestBody.files['test.js'].content).toBe('console.log("Hello, world!");');
    
    // Check if notification was shown
    expect(window.showNotification).toHaveBeenCalled();
  });
  
  test('should validate gist creation form', async () => {
    // Arrange
    // Mock profile API response
    fetch.mockImplementationOnce(() => 
      Promise.reject(new Error('Failed to load profile'))
    );
    
    // Mock gists API response
    fetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      })
    );
    
    // Act
    const gistManager = new GistManager('gist-manager-container');
    
    // Wait for async operations to complete
    await new Promise(resolve => setTimeout(resolve, 0));
    
    // Open modal
    container.querySelector('.gist-manager__new-gist').click();
    
    // Get form elements
    const saveButton = container.querySelector('.gist-manager__save');
    
    // Don't fill the form (to test validation)
    
    // Submit the form
    saveButton.click();
    
    // Assert
    expect(fetch).toHaveBeenCalledTimes(2); // Only the initial API calls, not the create call
    expect(window.showNotification).toHaveBeenCalled();
    expect(window.showNotification.mock.calls[0][0]).toContain('Please provide a filename');
  });
}); 