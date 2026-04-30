# tsCrawler

This repository contains `tsCrawler`, a robust TypeScript-based web crawler module designed for the paper artifact to crawl websites and perform deep security analysis.

## Overview

The `tsCrawler` component connects to the `crawlerServer` (ZMQ Server) to request target websites, navigates to the target URLs using headless browsers, and executes various security analysis modules (e.g., detecting client-side XSS, measuring security headers, analyzing script inclusions). 

## Features

- **Security Analysis:** Built-in modules to detect vulnerabilities and collect security-related metrics.
- **Distributed Crawling:** Integrates seamlessly with the ZMQ-based `crawlerServer` to fetch jobs dynamically.
- **Artifact Ready:** Stripped of personal identifiers and hardcoded paths to ensure a smooth, double-blind artifact review process.

## Getting Started

### Prerequisites

- Node.js (v18+ recommended)
- npm or yarn
- PM2 (for process management)
- A running instance of the `crawlerServer` (and its PostgreSQL database)

### Installation

1. Navigate to the `src` directory:
   ```bash
   cd src
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build the TypeScript project:
   ```bash
   npm run build
   ```

### Configuration

Copy `.env.example` to `.env` and configure your environment variables. 
Make sure `ZMQ_HOST` points to the `crawlerServer` (e.g., `tcp://127.0.0.1:5555`) and `EXPERIMENT` is set to the analysis you want to run (e.g., `cxss`).

### Running the Crawler

You can run the crawler manually for debugging:
```bash
npm start
```

Or start multiple instances using the provided bash scripts (which use PM2):
```bash
bash experiment.sh
```

