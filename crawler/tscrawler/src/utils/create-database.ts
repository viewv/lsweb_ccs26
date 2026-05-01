import { Client } from 'pg';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import { exec } from 'child_process';
import * as fs from 'fs';

// Parse command line arguments
const argv = yargs(hideBin(process.argv))
    .option('host', {
        alias: 'h',
        description: 'Postgres host',
        type: 'string',
        default: 'localhost',
    })
    .option('user', {
        alias: 'U',
        description: 'Postgres user',
        type: 'string',
        default: 'postgres',
    })
    .option('password', {
        description: 'Postgres user password',
        type: 'string',
        demandOption: true, // Password is required
    })
    .option('port', {
        alias: 'p',
        description: 'Postgres port',
        type: 'number',
        default: 5432,
    })
    .option('pgbouncerPort', {
        description: 'PgBouncer port',
        type: 'number',
        default: 6432,
    })
    .option('pgbouncerConfig', {
        description: 'PgBouncer config file path',
        type: 'string',
        default: '/etc/pgbouncer/pgbouncer.ini',
    })
    .option('db', {
        alias: 'd',
        description: 'Database to create',
        type: 'string',
        demandOption: true, // Database name is required
    })
    .parseSync();

const POSTGRES_HOST = argv.host;
const POSTGRES_USER = argv.user;
const POSTGRES_PASSWORD = argv.password;
const POSTGRES_PORT = argv.port;
const POSTGRES_DB = argv.db;
const PGBOUNCER_PORT = argv.pgbouncerPort;
const PGBOUNCER_CONFIG = argv.pgbouncerConfig;
const UPDATE_PGBOUNCER = process.env.UPDATE_PGBOUNCER !== 'false';

// Function to update PgBouncer configuration
async function updatePgBouncer(dbName: string): Promise<boolean> {
    try {
        // Check if config file exists
        if (!fs.existsSync(PGBOUNCER_CONFIG)) {
            console.error(`PgBouncer config file not found: ${PGBOUNCER_CONFIG}`);
            return false;
        }

        // Read config file
        const configContent = fs.readFileSync(PGBOUNCER_CONFIG, 'utf8');

        // Check if database is already in config
        const dbConfigPattern = new RegExp(`${dbName}\\s*=`);
        if (dbConfigPattern.test(configContent)) {
            console.log(`Database "${dbName}" is already in PgBouncer config.`);
            return true;
        }

        // Create database config line
        const dbConfigLine = `${dbName} = host=${POSTGRES_HOST} port=${POSTGRES_PORT} dbname=${dbName} user=${POSTGRES_USER} password=${POSTGRES_PASSWORD}`;

        // Find [databases] section
        const databasesSectionIndex = configContent.indexOf('[databases]');
        if (databasesSectionIndex === -1) {
            console.error('Could not find [databases] section in PgBouncer config.');
            return false;
        }

        // Find next section
        const nextSectionIndex = configContent.indexOf('[', databasesSectionIndex + 1);

        let updatedContent;
        if (nextSectionIndex === -1) {
            // If no next section, add to end of file
            updatedContent = configContent + `\n${dbConfigLine}\n`;
        } else {
            // Add before next section
            updatedContent = configContent.substring(0, nextSectionIndex) +
                `${dbConfigLine}\n` +
                configContent.substring(nextSectionIndex);
        }

        // Write updated config
        fs.writeFileSync(PGBOUNCER_CONFIG, updatedContent);
        console.log(`Added database "${dbName}" to PgBouncer config.`);

        // Reload PgBouncer config
        return new Promise<boolean>((resolve) => {
            exec(
                `echo "RELOAD;" | PGPASSWORD=${POSTGRES_PASSWORD} psql -h ${POSTGRES_HOST} -p ${PGBOUNCER_PORT} -U ${POSTGRES_USER} pgbouncer`,
                (error, stdout, stderr) => {
                    if (error) {
                        console.error(`Failed to reload PgBouncer config: ${error.message}`);
                        console.error(stderr);
                        resolve(false);
                        return;
                    }
                    console.log(stdout);
                    console.log('PgBouncer configuration reloaded successfully.');
                    resolve(true);
                }
            );
        });
    } catch (error) {
        console.error('Error updating PgBouncer config:', error);
        return false;
    }
}

(async () => {
    const client = new Client({
        host: POSTGRES_HOST,
        user: POSTGRES_USER,
        password: POSTGRES_PASSWORD,
        port: POSTGRES_PORT,
        database: 'postgres', // Connect to default database
    });

    try {
        await client.connect();
        const checkDbExistsQuery = `SELECT 1 FROM pg_database WHERE datname='${POSTGRES_DB}'`;
        const checkDbExistsResult = await client.query(checkDbExistsQuery);

        let dbCreated = false;
        if (checkDbExistsResult.rowCount === 0) {
            const createDbQuery = `CREATE DATABASE ${POSTGRES_DB}`;
            await client.query(createDbQuery);
            console.log(`Database "${POSTGRES_DB}" created successfully.`);
            dbCreated = true;
        } else {
            console.log(`Database "${POSTGRES_DB}" already exists.`);
            dbCreated = true;
        }

        // If database created/exists and UPDATE_PGBOUNCER is true, update PgBouncer config
        if (dbCreated && UPDATE_PGBOUNCER) {
            console.log('PgBouncer update is enabled, updating PgBouncer config...');
            const updated = await updatePgBouncer(POSTGRES_DB);
            if (updated) {
                console.log(`Database "${POSTGRES_DB}" successfully added to PgBouncer config and reloaded.`);
            } else {
                console.warn(`Database "${POSTGRES_DB}" created, but failed to update PgBouncer config.`);
            }
        } else if (dbCreated && !UPDATE_PGBOUNCER) {
            console.log('PgBouncer update is disabled, skipping PgBouncer config update.');
        }
    } catch (error) {
        console.error('Error creating database:', error);
    } finally {
        await client.end();
    }
})();