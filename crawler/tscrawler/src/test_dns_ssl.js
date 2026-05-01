const { firefox } = require('playwright');

(async () => {
    console.log('Testing DNS and SSL configuration...');

    try {
        // Import config from compiled file
        const configModule = await import('./dist/config/index.js');
        // For CommonJS modules, default export is in the .default property
        const config = configModule.default;

        console.log('Config module keys:', Object.keys(configModule));
        console.log('Config object:', config);
        console.log('DNS Servers:', config?.dns_servers);
        console.log('DNS Enabled:', config?.dns_enable);

        const browser = await firefox.launch({
            headless: true,
            args: [
                '--ignore-certificate-errors',
                '--ignore-ssl-errors',
                '--ignore-certificate-errors-spki-list',
                '--disable-web-security'
            ]
        });

        const context = await browser.newContext({
            ignoreHTTPSErrors: true,
            acceptDownloads: true,
        });

        const page = await context.newPage();

        // Test normal website
        try {
            await page.goto('https://www.google.com');
            console.log('✓ Successfully accessed Google');
        } catch (error) {
            console.log('✗ Failed to access Google:', error.message);
        }

        // Test website with SSL certificate issues
        try {
            await page.goto('https://self-signed.badssl.com/');
            console.log('✓ Successfully accessed site with self-signed certificate');
        } catch (error) {
            console.log('✗ Failed to access self-signed site:', error.message);
        }

        // Test website with expired certificate
        try {
            await page.goto('https://expired.badssl.com/');
            console.log('✓ Successfully accessed site with expired certificate');
        } catch (error) {
            console.log('✗ Failed to access expired certificate site:', error.message);
        }

        // Test certificate with mismatched hostname
        try {
            await page.goto('https://wrong.host.badssl.com/');
            console.log('✓ Successfully accessed site with wrong hostname certificate');
        } catch (error) {
            console.log('✗ Failed to access wrong hostname site:', error.message);
        }

        await browser.close();
        console.log('DNS and SSL test completed.');

    } catch (importError) {
        console.log('Failed to import config:', importError.message);
        console.log('Please check if the dist/config/index.js file exists.');
    }
})();