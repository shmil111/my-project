/**
 * Swagger Documentation Utility
 * 
 * Generates OpenAPI documentation for the API
 */

import swaggerJSDoc from 'swagger-jsdoc';
import { version } from '../../package.json';
import { config } from '../config';

/**
 * Generate Swagger specification
 * @returns Swagger specification object
 */
export function generateSwaggerSpec() {
  const swaggerOptions: swaggerJSDoc.Options = {
    definition: {
      openapi: '3.0.0',
      info: {
        title: 'My Project API',
        version,
        description: 'A comprehensive hybrid project combining Python and TypeScript/Node.js capabilities',
        license: {
          name: 'MIT',
          url: 'https://opensource.org/licenses/MIT',
        },
        contact: {
          name: 'API Support',
          email: 'support@example.com',
          url: 'https://example.com/support',
        },
      },
      servers: [
        {
          url: `http://localhost:${config.port}`,
          description: 'Local Development Server',
        },
      ],
      components: {
        securitySchemes: {
          bearerAuth: {
            type: 'http',
            scheme: 'bearer',
            bearerFormat: 'JWT',
          },
        },
        schemas: {
          Error: {
            type: 'object',
            properties: {
              success: {
                type: 'boolean',
                example: false,
              },
              message: {
                type: 'string',
                example: 'An error occurred',
              },
              error: {
                type: 'string',
                example: 'Error details',
              },
            },
          },
          User: {
            type: 'object',
            properties: {
              id: {
                type: 'string',
                example: '123e4567-e89b-12d3-a456-426614174000',
              },
              username: {
                type: 'string',
                example: 'johndoe',
              },
              email: {
                type: 'string',
                example: 'john.doe@example.com',
              },
              roles: {
                type: 'array',
                items: {
                  type: 'string',
                },
                example: ['user', 'admin'],
              },
            },
          },
          DataItem: {
            type: 'object',
            properties: {
              id: {
                type: 'string',
                example: '1',
              },
              name: {
                type: 'string',
                example: 'Example Item',
              },
              description: {
                type: 'string',
                example: 'This is an example item',
              },
              createdAt: {
                type: 'string',
                format: 'date-time',
              },
              updatedAt: {
                type: 'string',
                format: 'date-time',
              },
            },
          },
          SentimentResponse: {
            type: 'object',
            properties: {
              success: {
                type: 'boolean',
                example: true,
              },
              sentiment: {
                type: 'object',
                properties: {
                  label: {
                    type: 'string',
                    example: 'positive',
                  },
                  score: {
                    type: 'number',
                    format: 'float',
                    example: 0.92,
                  },
                },
              },
            },
          },
          TranslationResponse: {
            type: 'object',
            properties: {
              success: {
                type: 'boolean',
                example: true,
              },
              translation: {
                type: 'string',
                example: 'Hola mundo',
              },
              sourceLang: {
                type: 'string',
                example: 'en',
              },
              targetLang: {
                type: 'string',
                example: 'es',
              },
            },
          },
          SummaryResponse: {
            type: 'object',
            properties: {
              success: {
                type: 'boolean',
                example: true,
              },
              summary: {
                type: 'string',
                example: 'This is a concise summary of the provided text.',
              },
              originalLength: {
                type: 'number',
                example: 256,
              },
              summaryLength: {
                type: 'number',
                example: 32,
              },
            },
          },
        },
      },
    },
    apis: ['./src/routes.ts'], // Path to the API routes
  };

  return swaggerJSDoc(swaggerOptions);
}

export default generateSwaggerSpec; 