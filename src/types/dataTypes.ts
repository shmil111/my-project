/**
 * Data types and interfaces for the application
 */

/**
 * Represents a generic data item with an ID and name
 */
export interface MyDataType {
  id: number;
  name: string;
  description?: string;
  created?: Date;
  updated?: Date;
  tags?: string[];
}

/**
 * Response for successful operations
 */
export interface SuccessResponse<T> {
  success: true;
  data: T;
  message?: string;
}

/**
 * Response for failed operations
 */
export interface ErrorResponse {
  success: false;
  error: string;
  code?: number;
}

/**
 * Generic API response
 */
export type ApiResponse<T> = SuccessResponse<T> | ErrorResponse;

/**
 * Parameters for filtering data
 */
export interface FilterParams {
  search?: string;
  limit?: number;
  offset?: number;
  sortBy?: string;
  sortDirection?: 'asc' | 'desc';
} 