/**
 * Data item interface
 */
export interface DataItem {
    id?: number | string; // Allow optional ID for creation
    key: string;
    value: any;
    createdAt: string;
    updatedAt?: string;
    metadata?: Record<string, any>;
} 