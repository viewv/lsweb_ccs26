const { firefox } = require('playwright');

(async () => {
    console.log('Testing DNS and SSL configuration with headful browser...');

    try {
        // 直接使用require导入编译后的配置文件
        const config = require('./dist/config/index.js').default;

        console.log('DNS Servers:', config.dns_servers);
        console.log('DNS Enabled:', config.dns_enable);

        const browser = await firefox.launch({
            headless: false, // 设置为false显示浏览器界面
            slowMo: 2000,    // 每个操作之间延迟2秒，方便观察
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
        // console.log('\n=== 测试访问 Google ===');
        // try {
        //     await page.goto('https://www.google.com', { waitUntil: 'networkidle' });
        //     console.log('✓ Successfully accessed Google');
        //     await page.waitForTimeout(3000); // 等待3秒让你观察
        // } catch (error) {
        //     console.log('✗ Failed to access Google:', error.message);
        // }

        // // Test website with SSL certificate issues
        // console.log('\n=== 测试访问自签名证书网站 ===');
        // try {
        //     await page.goto('https://self-signed.badssl.com/', { waitUntil: 'networkidle' });
        //     console.log('✓ Successfully accessed site with self-signed certificate');
        //     await page.waitForTimeout(3000); // 等待3秒让你观察
        // } catch (error) {
        //     console.log('✗ Failed to access self-signed site:', error.message);
        // }

        // // Test website with expired certificate
        // console.log('\n=== 测试访问过期证书网站 ===');
        // try {
        //     await page.goto('https://expired.badssl.com/', { waitUntil: 'networkidle' });
        //     console.log('✓ Successfully accessed site with expired certificate');
        //     await page.waitForTimeout(3000); // 等待3秒让你观察
        // } catch (error) {
        //     console.log('✗ Failed to access expired certificate site:', error.message);
        // }

        // // Test certificate with mismatched hostname
        // console.log('\n=== 测试访问域名不匹配证书网站 ===');
        // try {
        //     await page.goto('https://wrong.host.badssl.com/', { waitUntil: 'networkidle' });
        //     console.log('✓ Successfully accessed site with wrong hostname certificate');
        //     await page.waitForTimeout(3000); // 等待3秒让你观察
        // } catch (error) {
        //     console.log('✗ Failed to access wrong hostname site:', error.message);
        // }

        // // 测试更多SSL问题网站
        // console.log('\n=== 测试访问不受信任的根证书网站 ===');
        // try {
        //     await page.goto('https://untrusted-root.badssl.com/', { waitUntil: 'networkidle' });
        //     console.log('✓ Successfully accessed site with untrusted root certificate');
        //     await page.waitForTimeout(3000);
        // } catch (error) {
        //     console.log('✗ Failed to access untrusted root site:', error.message);
        // }

        //  real world http://8855betpay.com/
        console.log('\n=== 测试访问真实网站 ===');
        try {
            await page.goto('http://mobi7.io', { waitUntil: 'networkidle' });
            console.log('✓ Successfully accessed real world site');
            await page.waitForTimeout(3000); // 等待3秒让你观察
        } catch (error) {
            console.log('✗ Failed to access real world site:', error.message);
        }

        console.log('\n=== 测试完成，浏览器将在10秒后关闭 ===');
        console.log('你可以在浏览器中查看各个网站的SSL证书状态');

        // 等待10秒让用户观察
        await page.waitForTimeout(10000);

        await browser.close();
        console.log('DNS and SSL test completed.');

    } catch (importError) {
        console.log('Failed to import config:', importError.message);
    }
})();