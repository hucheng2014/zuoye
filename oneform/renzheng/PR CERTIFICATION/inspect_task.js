const CDP = require('chrome-remote-interface');
const fs = require('fs');

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function waitForCondition(checkFn, timeout = 30000, interval = 500) {
    const startTime = Date.now();
    while (Date.now() - startTime < timeout) {
        const result = await checkFn();
        if (result) return result;
        await sleep(interval);
    }
    throw new Error('Timeout waiting for condition');
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

        // Wait for page to be ready
        await sleep(3000);

        // Get all frames
        const framesResult = await Runtime.evaluate({
            expression: `
                (function() {
                    const frames = [];
                    frames.push({
                        location: window.location.href,
                        isTop: true
                    });

                    const iframes = document.querySelectorAll('iframe');
                    for (let i = 0; i < iframes.length; i++) {
                        frames.push({
                            id: iframes[i].id,
                            src: iframes[i].src,
                            isTop: false
                        });
                    }

                    return frames;
                })()
            `
        });

        console.log('\nFrames found:', JSON.stringify(framesResult.result.value, null, 2));

        // Try to get task content by executing in all frames
        const taskContent = await Runtime.evaluate({
            expression: `
                (function() {
                    // Try to find task content in current context
                    const findText = (selector) => {
                        const el = document.querySelector(selector);
                        return el ? el.innerText : null;
                    };

                    // Look for common task elements
                    const result = {
                        title: document.title,
                        h1: findText('h1'),
                        h2: findText('h2'),
                        buttons: Array.from(document.querySelectorAll('button')).map(b => b.textContent.trim()).filter(t => t),
                        hasAcceptButton: !!document.querySelector('button[aria-label*="Accept"], button:contains("ACCEPT")'),
                        textContent: document.body ? document.body.innerText.substring(0, 1000) : null
                    };

                    return result;
                })()
            `,
            includeCommandLineAPI: true
        });

        console.log('\nTask content:', JSON.stringify(taskContent.result.value, null, 2));

        // Take screenshot
        const screenshot = await Page.captureScreenshot({
            format: 'png',
            fromSurface: true,
            captureBeyondViewport: false
        });
        fs.writeFileSync('/tmp/task_screenshot.png', Buffer.from(screenshot.data, 'base64'));
        console.log('\nScreenshot saved to /tmp/task_screenshot.png');

        console.log('\n请打开 http://127.0.0.1:6083/vnc.html 查看页面');
        console.log('我需要你确认页面上是否有 ACCEPT 按钮，以及当前任务的具体内容。');

    } catch (error) {
        console.error('Error:', error);
    } finally {
        if (client) {
            await client.close();
        }
    }
}

main();
