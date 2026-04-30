
import parser from "./parser";

const args = parser.parse_args()

type CrawlMode = "test" | "connected";

// Redis config
const REDIS_ENABLE = process.env.REDIS_ENABLE ? process.env.REDIS_ENABLE === 'true' : false;
const REDIS_HOST = process.env.REDIS_HOST ? process.env.REDIS_HOST : "127.0.0.1";
const REDIS_PORT = process.env.REDIS_PORT ? parseInt(process.env.REDIS_PORT, 10) : 6379;
const REDIS_DB = process.env.REDIS_DB ? parseInt(process.env.REDIS_DB, 10) : 0;

// Proxy config
const PROXY_ENABLE = process.env.PROXY_ENABLE ? process.env.PROXY_ENABLE === 'true' : false;
const PROXY_URL = process.env.PROXY_URL ? process.env.PROXY_URL : "http://localhost:8080";

type LinkMaximum = {
    domain?: number;
    page?: number;
    depth?: number;
}

export type Config = {
    mode: CrawlMode,
    flags: string[],
    headfull: boolean,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    dynamic: any,
    links: {
        collect: boolean,
        maximum: LinkMaximum
    },
    goto: {
        timeout: number,
        waitUntil: "load" | "domcontentloaded" | "networkidle" | "commit"
    },
    timeouts: {
        restart: number,
        sameSite: number,
        moduleExec: number
    },
    sessions: {
        screenshotMaxDepth: number,
        screenshotBefore: boolean,
        screenshotAfterwards: boolean,
        includeLoginpages: boolean,
    },
    screenshotEndTreshold: number,
    maxTime: {
        session: number,
        domain: number,
        url: number,
        subject: number
    },
    dataPath: string,
    // redis_enable
    redis_enable: boolean,
    redis_host: string,
    redis_port: number,
    redis_db: number,
    // proxy_config
    proxy_enable: boolean,
    proxy_url: string
}

const flags: string[] = [

];

const config: Config = {
    mode: args.test ? "test" : "connected",
    headfull: args.headfull,
    flags,
    // config about the depth
    links: {
        collect: true,
        maximum: {
            domain: 250,
            page: 250,
            depth: 2
        }
    },
    goto: {
        // Note: time out All values are in Milliseconds, so * 1000
        timeout: 30 * 1000,
        waitUntil: "load",
    },
    timeouts: {
        // All values are in Milliseconds, so * 1000
        restart: 120 * 1000,
        sameSite: 2 * 1000,
        moduleExec: 10 * 1000
    },
    sessions: {
        screenshotMaxDepth: 0,
        screenshotBefore: false,
        screenshotAfterwards: false,
        includeLoginpages: false
    },
    maxTime: {
        // All values are in Milliseconds, so * 1000
        session: 86400 * 1000,
        domain: 86400 * 1000,
        url: 86400 * 1000,
        subject: 1200 * 1000
    },
    screenshotEndTreshold: 1800 * 1000,
    dataPath: args.datapath,
    dynamic: args,
    // redis
    redis_enable: REDIS_ENABLE,
    redis_host: REDIS_HOST,
    redis_port: REDIS_PORT,
    redis_db: REDIS_DB,
    // proxy
    proxy_enable: PROXY_ENABLE,
    proxy_url: PROXY_URL
};

export default config;