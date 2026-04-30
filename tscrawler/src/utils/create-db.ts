import { Client } from 'pg';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';

// Use parseSync() to synchronously parse arguments
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
    .option('db', {
        alias: 'd',
        description: 'Database to create',
        type: 'string',
        demandOption: true, // Database name is required
    })
    .parseSync(); // Using parseSync() here

const POSTGRES_HOST = argv.host;
const POSTGRES_USER = argv.user;
const POSTGRES_PASSWORD = argv.password;
const POSTGRES_PORT = argv.port;
const POSTGRES_DB = argv.db;

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

        if (checkDbExistsResult.rowCount === 0) {
            const createDbQuery = `CREATE DATABASE ${POSTGRES_DB}`;
            await client.query(createDbQuery);
            console.log(`Database "${POSTGRES_DB}" created successfully.`);
        } else {
            console.log(`Database "${POSTGRES_DB}" already exists.`);
        }
    } catch (error) {
        console.error('Error creating database:', error);
    } finally {
        await client.end();
    }
})();
