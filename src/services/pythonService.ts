import { executePythonScript, PythonResult } from '../utils/pythonIntegration';
import path from 'path';
import { config } from '../utils/env';

/**
 * Service for Python module integration
 * Provides simplified access to Python modules
 */
export class PythonService {
  private pythonPath: string;
  private modulesPath: string;

  constructor() {
    this.pythonPath = config.PYTHON_PATH || 'python';
    this.modulesPath = path.resolve(__dirname, '../../python_modules');
  }

  /**
   * Clean and preprocess text
   * 
   * @param text Text to clean
   * @param options Cleaning options
   * @returns Cleaned text result
   */
  async cleanText(text: string, options?: Record<string, any>): Promise<PythonResult<any>> {
    const scriptPath = path.join(this.modulesPath, 'text_processor.py');
    const args = ['clean', text];
    
    if (options) {
      args.push(JSON.stringify(options));
    }
    
    return executePythonScript({
      scriptPath,
      args,
      pythonPath: this.pythonPath
    });
  }

  /**
   * Analyze sentiment in text
   * 
   * @param text Text to analyze
   * @returns Sentiment analysis result
   */
  async analyzeSentiment(text: string): Promise<PythonResult<any>> {
    const scriptPath = path.join(this.modulesPath, 'text_processor.py');
    
    return executePythonScript({
      scriptPath,
      args: ['sentiment', text],
      pythonPath: this.pythonPath
    });
  }

  /**
   * Extract named entities from text
   * 
   * @param text Text to analyze
   * @returns Named entities result
   */
  async extractEntities(text: string): Promise<PythonResult<any>> {
    const scriptPath = path.join(this.modulesPath, 'text_processor.py');
    
    return executePythonScript({
      scriptPath,
      args: ['entities', text],
      pythonPath: this.pythonPath
    });
  }

  /**
   * Generate a summary of text
   * 
   * @param text Text to summarize
   * @param reductionTarget Target reduction ratio (0-1)
   * @returns Summary result
   */
  async summarizeText(text: string, reductionTarget = 0.3): Promise<PythonResult<any>> {
    const scriptPath = path.join(this.modulesPath, 'text_processor.py');
    
    return executePythonScript({
      scriptPath,
      args: ['summarize', text, reductionTarget.toString()],
      pythonPath: this.pythonPath
    });
  }

  /**
   * Translate text from one language to another
   * 
   * @param text Text to translate
   * @param sourceLang Source language code
   * @param targetLang Target language code
   * @returns Translation result
   */
  async translateText(
    text: string,
    sourceLang = 'en',
    targetLang = 'es'
  ): Promise<PythonResult<any>> {
    const scriptPath = path.join(this.modulesPath, 'text_processor.py');
    
    return executePythonScript({
      scriptPath,
      args: ['translate', text, sourceLang, targetLang],
      pythonPath: this.pythonPath
    });
  }
}

// Export singleton instance
export const pythonService = new PythonService(); 