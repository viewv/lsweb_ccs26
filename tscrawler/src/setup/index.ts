import { config as dotEnvConfig } from "dotenv";
dotEnvConfig(); // Load .env

import path from "path";
import fs from "fs";
import config from "../config";

import Crawler from "../crawler";
import { fill } from "./database-fill";
import { fillCsv } from "./database-fill-csv";
import { Logging } from "../utils/logging";
import { exit } from "process";

const setupCrawler = async () => {
    Logging.info(`Started setting up the crawler`);

    try {
        const crawler = new Crawler();
        await crawler.setup(config.dynamic.module);
        Logging.info(`Finished crawler module setup successfully.`);
    } catch (err: unknown) {
        Logging.error(`Crawler module setup failed. Error: ${(err as Error).toString()}`);
        exit(1);
    }

    try {
        if (config.dynamic.fill) {
            if (config.dynamic.csv) {
                Logging.info(`Filling database with CSV from arguments`);
                await fillCsv(path.join(config.dynamic.csv));
            } else {
                Logging.warn(`Filling database with stub data pointing to localhost`);
                await fill();
            }
        }
    } catch (err: unknown) {
        Logging.error(`Crawler fill failed. Error: ${(err as Error).toString()}`);
        exit(1);
    }

    Logging.info(`Crawler setup and data fill completed successfully.`);
    exit(0);
};

// Main execution
Logging.info(`Checking dataPath="${config.dataPath}"...`);

if (!fs.existsSync(config.dataPath)) {
    Logging.error(`dataPath does not exist: ${config.dataPath}`);
    exit(1);
}

if (fs.readdirSync(config.dataPath).length !== 0) {
    Logging.error(`Provided dataPath is not empty. Abort.`);
    exit(1);
} else {
    Logging.info(`Directory exists and is empty. Proceeding...`);
    setupCrawler();
}