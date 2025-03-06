/**
 * Test Helpers
 * 
 * This file contains helper functions and utilities for tests to reduce code duplication.
 */

import { Request, Response } from 'express';

/**
 * Creates a mock Express request object for testing
 * 
 * @param options - Optional properties to add to the request
 * @returns A mock Request object
 */
export function createMockRequest(options: Partial<Request> = {}): Partial<Request> {
  return {
    body: {},
    params: {},
    query: {},
    headers: {},
    ...options
  };
}

/**
 * Creates a mock Express response object for testing
 * 
 * @returns A mock Response object with jest spy functions
 */
export function createMockResponse(): Partial<Response> {
  const responseJson = jest.fn();
  const responseStatus = jest.fn().mockReturnValue({ json: responseJson });
  const responseSend = jest.fn();
  const responseEnd = jest.fn();
  const responseSetHeader = jest.fn();
  
  return {
    status: responseStatus,
    json: responseJson,
    send: responseSend,
    end: responseEnd,
    setHeader: responseSetHeader
  };
}

/**
 * Creates a standard test setup with mock request and response objects
 * 
 * @param requestOptions - Optional properties to add to the request
 * @returns An object containing mock request, response, and response spy functions
 */
export function setupControllerTest(requestOptions: Partial<Request> = {}) {
  const mockRequest = createMockRequest(requestOptions);
  const mockResponse = createMockResponse();
  
  return {
    mockRequest,
    mockResponse,
    responseJson: mockResponse.json as jest.Mock,
    responseStatus: mockResponse.status as jest.Mock,
    responseSend: mockResponse.send as jest.Mock,
    responseEnd: mockResponse.end as jest.Mock
  };
}

/**
 * Asserts that a successful response was sent with the expected data
 * 
 * @param responseStatus - The status spy function
 * @param responseJson - The json spy function
 * @param expectedStatus - The expected HTTP status code
 * @param expectedData - The expected response data
 */
export function assertSuccessResponse(
  responseStatus: jest.Mock,
  responseJson: jest.Mock,
  expectedStatus: number,
  expectedData: any
) {
  expect(responseStatus).toHaveBeenCalledWith(expectedStatus);
  expect(responseJson).toHaveBeenCalledWith(expectedData);
}

/**
 * Asserts that an error response was sent
 * 
 * @param responseStatus - The status spy function
 * @param responseJson - The json spy function
 * @param expectedStatus - The expected HTTP status code
 * @param errorMessage - The expected error message (optional)
 */
export function assertErrorResponse(
  responseStatus: jest.Mock,
  responseJson: jest.Mock,
  expectedStatus: number,
  errorMessage?: string
) {
  expect(responseStatus).toHaveBeenCalledWith(expectedStatus);
  
  if (errorMessage) {
    expect(responseJson).toHaveBeenCalledWith(
      expect.objectContaining({
        success: false,
        error: expect.objectContaining({
          message: errorMessage
        })
      })
    );
  } else {
    expect(responseJson).toHaveBeenCalledWith(
      expect.objectContaining({
        success: false
      })
    );
  }
} 