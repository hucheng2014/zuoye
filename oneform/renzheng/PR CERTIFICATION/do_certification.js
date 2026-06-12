const CDP = require('chrome-remote-interface');

const CDP_URL = 'http://127.0.0.1:9235';

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function waitForElement(Runtime, selector, timeout = 10000) {
    const startTime = Date.now();
    while (Date.now() - startTime < timeout) {
        const result = await Runtime.evaluate({
            expression: `document.querySelector('${selector}') !== null`
        });
        if (result.result.value) {
            return true;
        }
        await sleep(500);
    }
    return false;
}

async function clickElement(Runtime, selector) {
    await Runtime.evaluate({
        expression: `
            (function() {
                const el = document.querySelector('${selector}');
                if (el) {
                    el.click();
                    return true;
                }
                return false;
            })()
        `
    });
}

async function getPageInfo(Runtime) {
    const result = await Runtime.evaluate({
        expression: `
            (function() {
                // Get task type and content
                const taskInfo = {
                    url: window.location.href,
                    title: document.title,
                    hasAcceptButton: !!document.querySelector('button:contains("ACCEPT"), button:contains("Accept")'),
                    hasSubmitButton: !!document.querySelector('button:contains("SUBMIT"), button:contains("Submit")'),
                    hasNextButton: !!document.querySelector('button:contains("NEXT"), button:contains("Next")'),
                };
                return taskInfo;
            })()
        `
    });
    return result.result.value;
}

async function main() {
    let client;
    try {
        console.log('Connecting to browser...');
        client = await CDP({ host: '127.0.0.1', port: 9235 });

        const { Network, Page, Runtime, DOM } = client;

        await Network.enable();
        await Page.enable();
        await Runtime.enable();
        await DOM.enable();

        console.log('Connected successfully!');

        // Get current page info
        const pageInfo = await getPageInfo(Runtime);
        console.log('Page info:', JSON.stringify(pageInfo, null, 2));

        // Take a screenshot to see current state
        const screenshot = await Page.captureScreenshot({ format: 'png' });
        require('fs').writeFileSync('/tmp/current_page.png', Buffer.from(screenshot.data, 'base64'));
        console.log('Screenshot saved to /tmp/current_page.png');

        // Get page HTML for analysis
        const htmlResult = await Runtime.evaluate({
            expression: 'document.documentElement.outerHTML'
        });
        require('fs').writeFileSync('/tmp/page_content.html', htmlResult.result.value);
        console.log('Page HTML saved to /tmp/page_content.html');

    } catch (error) {
        console.error('Error:', error);
    } finally {
        if (client) {
            await client.close();
        }
    }
}

main();
