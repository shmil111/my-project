import { program } from 'commander';
import { autoUpdate } from './autoupdate';
import { createLearningModule } from './create-learning-module';
import { listLearningModules } from './list-learning-modules';
import { runLearningModule } from './run-learning-module';
import { initProject } from './init';
import { testLearningModule } from './test-learning-module';
import { updateLearningModule } from './update-learning-module';
import { publishLearningModule } from './publish-learning-module';
import { log, setLogLevel } from './logger';
import { loadConfig } from './config';
import { applyLearningModule } from './apply-learning-module';
import { generateLearningModule } from './generate-learning-module';
import { getPackageVersion } from './utils';
import chalk from 'chalk';

async function main() {
    process.on('uncaughtException', (error) => {
        log.error(`Uncaught Exception: ${error.message}`);
        log.error(`Stack Trace: ${error.stack}`);
        process.exit(1);
    });

    process.on('unhandledRejection', (reason, promise) => {
        log.error('Unhandled Rejection at:', promise, 'reason:', reason);
        if (reason instanceof Error) {
            log.error(`Stack Trace: ${reason.stack}`);
        }
        process.exit(1);
    });

    const config = loadConfig();
    setLogLevel(config.logLevel);

    program
        .name('devnotebook')
        .description('CLI to manage DevNotebook learning modules')
        .version(await getPackageVersion(), '-v, --version', 'Output the current version');

    program
        .command('init')
        .description('Initialize a new DevNotebook project')
        .option('-f, --force', 'Overwrite existing project files', false)
        .action(async (options) => {
            if (await initProject(options.force)) {
                log.info('Project initialized successfully.');
            } else {
                log.error('Project initialization failed.');
            }
        });

    program
        .command('create <moduleName>')
        .description('Create a new learning module')
        .option('-d, --description <description>', 'Description of the learning module')
        .option('-t, --tags <tags>', 'Comma-separated list of tags')
        .action(async (moduleName, options) => {
            const tags = options.tags ? options.tags.split(',').map((tag: string) => tag.trim()) : [];
            if (await createLearningModule(moduleName, options.description, tags)) {
                log.info(`Learning module "${moduleName}" created successfully.`);
            } else {
                log.error(`Failed to create learning module "${moduleName}".`);
            }
        });

    program
        .command('list')
        .description('List all available learning modules')
        .action(async () => {
            const modules = await listLearningModules();
            if (modules) {
                console.table(modules);
            }
        });

    program
        .command('run <moduleName>')
        .description('Run a specified learning module')
        .option('-s, --step <stepNumber>', 'Run a specific step within the module')
        .action(async (moduleName, options) => {
            if (await runLearningModule(moduleName, options.step)) {
                log.info(`Learning module "${moduleName}" executed successfully.`);
            } else {
                log.error(`Failed to run learning module "${moduleName}".`);
            }
        });

    program
        .command('test <moduleName>')
        .description('Test a specified learning module')
        .action(async (moduleName) => {
            if (await testLearningModule(moduleName)) {
                log.info(`Learning module "${moduleName}" tested successfully.`);
            } else {
                log.error(`Failed to test learning module "${moduleName}".`);
            }
        });

    program
        .command('update <moduleName>')
        .description('Update a specified learning module')
        .option('-d, --description <description>', 'New description of the learning module')
        .option('-t, --tags <tags>', 'New comma-separated list of tags')
        .action(async (moduleName, options) => {
            const tags = options.tags ? options.tags.split(',').map((tag: string) => tag.trim()) : [];
            if (await updateLearningModule(moduleName, options.description, tags)) {
                log.info(`Learning module "${moduleName}" updated successfully.`);
            } else {
                log.error(`Failed to update learning module "${moduleName}".`);
            }
        });

    program
        .command('publish <moduleName>')
        .description('Publish a specified learning module')
        .action(async (moduleName) => {
            if (await publishLearningModule(moduleName)) {
                log.info(`Learning module "${moduleName}" published successfully.`);
            } else {
                log.error(`Failed to publish learning module "${moduleName}".`);
            }
        });

    program
        .command('autoupdate')
        .description('Automatically update dependencies and apply best practices')
        .action(async () => {
            if (await autoUpdate()) {
                log.info('Project updated successfully.');
            } else {
                log.error('Project update failed.');
            }
        });

    program
        .command('apply <moduleName>')
        .description('Apply a learning module to the current project')
        .action(async (moduleName) => {
            if (await applyLearningModule(moduleName)) {
                log.info(`Learning module "${moduleName}" applied successfully.`);
            } else {
                log.error(`Failed to apply learning module "${moduleName}".`);
            }
        });

    program
        .command('generate <moduleName>')
        .description('Generate files and code for a learning module')
        .action(async (moduleName) => {
            if(await generateLearningModule(moduleName)) {
                log.info(`Learning module "${moduleName}" generated successfully.`);
            } else {
                log.error(`Failed to generate learning module "${moduleName}".`);
            }
        });

    program.parse(process.argv);
}

main(); 