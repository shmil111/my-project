/**
 * Logger Utility
 * 
 * This module provides standardized logging functionality for the application.
 */

// Define log levels
export enum LogLevel {
  ERROR = 0,
  WARN = 1,
  INFO = 2,
  DEBUG = 3
}

// Configuration for logger
export interface LoggerConfig {
  level: LogLevel;
  useTimestamp: boolean;
  useColors: boolean;
}

// Default configuration
const DEFAULT_CONFIG: LoggerConfig = {
  level: LogLevel.INFO,
  useTimestamp: true,
  useColors: true
};

// Colors for different log levels
const COLORS = {
  RESET: '\x1b[0m',
  ERROR: '\x1b[31m', // Red
  WARN: '\x1b[33m',  // Yellow
  INFO: '\x1b[36m',  // Cyan
  DEBUG: '\x1b[90m'  // Gray
};

// Logger class
export class Logger {
  private config: LoggerConfig;
  private moduleName: string;
  
  constructor(moduleName: string, config?: Partial<LoggerConfig>) {
    this.moduleName = moduleName;
    this.config = { ...DEFAULT_CONFIG, ...config };
  }
  
  // Format log message
  private format(level: string, message: string): string {
    const parts: string[] = [];
    
    if (this.config.useColors) {
      parts.push(COLORS[level as keyof typeof COLORS] || '');
    }
    
    if (this.config.useTimestamp) {
      parts.push(`[${new Date().toISOString()}]`);
    }
    
    parts.push(`[${level}]`);
    parts.push(`[${this.moduleName}]`);
    parts.push(message);
    
    if (this.config.useColors) {
      parts.push(COLORS.RESET);
    }
    
    return parts.join(' ');
  }
  
  // Log an error message
  public error(message: string, error?: any): void {
    if (this.config.level >= LogLevel.ERROR) {
      const formattedMessage = this.format('ERROR', message);
      console.error(formattedMessage);
      
      if (error) {
        if (error instanceof Error) {
          console.error(error.stack || error.message);
        } else {
          console.error(error);
        }
      }
    }
  }
  
  // Log a warning message
  public warn(message: string): void {
    if (this.config.level >= LogLevel.WARN) {
      console.warn(this.format('WARN', message));
    }
  }
  
  // Log an info message
  public info(message: string): void {
    if (this.config.level >= LogLevel.INFO) {
      console.info(this.format('INFO', message));
    }
  }
  
  // Log a debug message
  public debug(message: string): void {
    if (this.config.level >= LogLevel.DEBUG) {
      console.debug(this.format('DEBUG', message));
    }
  }
  
  // Update logger configuration
  public setConfig(config: Partial<LoggerConfig>): void {
    this.config = { ...this.config, ...config };
  }
}

// Create a logger factory for consistent creation
export function createLogger(moduleName: string, config?: Partial<LoggerConfig>): Logger {
  return new Logger(moduleName, config);
}

// Export a default logger
export default createLogger('App'); 