/**
 * Python Integration Utility
 * 
 * This module provides utilities for calling Python scripts and processing their output.
 */

import { spawn } from 'child_process';
import path from 'path';

/**
 * Result of a Python script execution
 */
export interface PythonResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}

/**
 * Options for executing a Python script
 */
export interface PythonOptions {
  scriptPath: string;
  args?: string[];
  timeout?: number;
  pythonPath?: string;
}

/**
 * Execute a Python script and return the result
 * 
 * @param options Configuration options for executing the script
 * @returns Promise with the result
 */
export async function executePythonScript<T>(options: PythonOptions): Promise<PythonResult<T>> {
  return new Promise((resolve) => {
    const {
      scriptPath,
      args = [],
      timeout = 30000,
      pythonPath = 'python'
    } = options;

    // Create a timeout for long-running scripts
    const timeoutId = setTimeout(() => {
      if (pythonProcess && !pythonProcess.killed) {
        pythonProcess.kill();
        resolve({
          success: false,
          error: 'Script execution timed out'
        });
      }
    }, timeout);

    // Spawn the Python process
    const pythonProcess = spawn(pythonPath, [scriptPath, ...args]);
    
    let stdout = '';
    let stderr = '';

    // Collect stdout data
    pythonProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    // Collect stderr data
    pythonProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    // Handle process completion
    pythonProcess.on('close', (code) => {
      clearTimeout(timeoutId);
      
      if (code !== 0) {
        resolve({
          success: false,
          error: stderr || `Process exited with code ${code}`
        });
        return;
      }

      try {
        // Try to parse the output as JSON
        const data = JSON.parse(stdout);
        resolve({
          success: true,
          data
        });
      } catch (error) {
        resolve({
          success: true,
          data: stdout as unknown as T
        });
      }
    });

    // Handle process errors
    pythonProcess.on('error', (error) => {
      clearTimeout(timeoutId);
      resolve({
        success: false,
        error: error.message
      });
    });
  });
}

/**
 * Run the sentiment analyzer on text
 * 
 * @param text Text to analyze
 * @returns Analysis result
 */
export async function analyzeSentiment(text: string): Promise<PythonResult<any>> {
  return executePythonScript({
    scriptPath: path.resolve(__dirname, '../../JestIntegration.py'),
    args: ['--function', 'process_text', '--input', JSON.stringify({ text })],
  });
}

/**
 * Translate text using the translator module
 * 
 * @param text Text to translate
 * @param sourceLang Source language code
 * @param targetLang Target language code
 * @returns Translated text result
 */
export async function translateText(
  text: string,
  sourceLang: string = 'en',
  targetLang: string = 'es'
): Promise<PythonResult<any>> {
  return executePythonScript({
    scriptPath: path.resolve(__dirname, '../../JestIntegration.py'),
    args: [
      '--function',
      'translate',
      '--input',
      JSON.stringify({ text, source_lang: sourceLang, target_lang: targetLang })
    ],
  });
} 