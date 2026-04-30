import { firefox } from 'playwright';

(async () => {
    const proxy_url = process.env.PROXY_URL ? process.env.PROXY_URL : "http://localhost:8080";

    const browser = await firefox.launch({
        headless: true
    });

    const context = await browser.newContext({
        proxy: {
            server: proxy_url,
        },
        ignoreHTTPSErrors: true,
    });

    const page = await context.newPage();

    await page.goto('https://stackoverflow.com/questions');

    const title = await page.title();
    console.log('Page Title:', title);

    const sLinkElements = await page.$$eval('.s-link', elements => {
        return elements.map(element => element.textContent.trim());
    });

    console.log(sLinkElements);

    await browser.close();
})();
