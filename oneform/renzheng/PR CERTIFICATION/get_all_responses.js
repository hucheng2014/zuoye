const CDP = require('chrome-remote-interface');
const fs = require('fs');

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function evaluateInFrame(Runtime, expression) {
    try {
        const result = await Runtime.evaluate({
            expression: expression,
            awaitPromise: true,
            returnByValue: true
        });
        return result.result.value;
    } catch (e) {
        console.error('Evaluation error:', e.message);
        return null;
    }
}

async function clickInFrame(Runtime, selector) {
    return await evaluateInFrame(Runtime, `
        (function() {
            const iframe = document.querySelector('#frm1');
            if (!iframe) return { success: false, error: 'No iframe' };

            const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
            const element = iframeDoc.querySelector('${selector}');

            if (!element) return { success: false, error: 'Element not found: ${selector}' };

            element.click();
            return { success: true };
        })()
    `);
}

async function getAllResponses(Runtime) {
    return await evaluateInFrame(Runtime, `
        (function() {
            const iframe = document.querySelector('#frm1');
            if (!iframe) return { error: 'No iframe' };

            const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;

            // Get all response tabs
            const tabs = ['Response A', 'Response B', 'Response C'];
            const responses = {};

            tabs.forEach((tabName, index) => {
                const tabButton = iframeDoc.querySelector('#kFJO1AFNXXgERBn_HB2OV-tab-' + index);
                if (tabButton) {
                    // Click to activate
                    tabButton.click();

                    // Wait a bit for content to load
                    const panel = iframeDoc.querySelector('#kFJO1AFNXXgERBn_HB2OV-tab-panel-' + index);
                    if (panel) {
                        responses[tabName] = panel.innerText.substring(0, 2000);
                    }
                }
            });

            return responses;
        })()
    `);
}

async function main() {
    let client;
    try {
        console.log('Connecting to browser...');
        client = await CDP({ host: '127.0.0.1', port: 9235 });

        const { Page, Runtime } = client;

        await Page.enable();
        await Runtime.enable();

        console.log('Connected successfully!');
        await sleep(2000);

        // Get user request
        const userRequest = await evaluateInFrame(Runtime, `
            (function() {
                const iframe = document.querySelector('#frm1');
                if (!iframe) return null;

                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                const bodyText = iframeDoc.body ? iframeDoc.body.innerText : '';

                // Extract user request
                const lines = bodyText.split('\\n');
                let userLine = '';
                for (let i = 0; i < lines.length; i++) {
                    if (lines[i].includes('User') && i + 1 < lines.length) {
                        userLine = lines[i + 2] || lines[i + 1];
                        break;
                    }
                }

                return userLine;
            })()
        `);

        console.log('\n=== USER REQUEST ===');
        console.log(userRequest);

        // Click on Response A tab
        console.log('\n=== Getting Response A ===');
        await clickInFrame(Runtime, '#kFJO1AFNXXgERBn_HB2OV-tab-0');
        await sleep(500);

        const responseA = await evaluateInFrame(Runtime, `
            (function() {
                const iframe = document.querySelector('#frm1');
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                const panel = iframeDoc.querySelector('#kFJO1AFNXXgERBn_HB2OV-tab-panel-0');
                return panel ? panel.innerText : 'Not found';
            })()
        `);
        console.log(responseA.substring(0, 500));

        // Click on Response B tab
        console.log('\n=== Getting Response B ===');
        await clickInFrame(Runtime, '#kFJO1AFNXXgERBn_HB2OV-tab-1');
        await sleep(500);

        const responseB = await evaluateInFrame(Runtime, `
            (function() {
                const iframe = document.querySelector('#frm1');
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                const panel = iframeDoc.querySelector('#kFJO1AFNXXgERBn_HB2OV-tab-panel-1');
                return panel ? panel.innerText : 'Not found';
            })()
        `);
        console.log(responseB.substring(0, 500));

        // Click on Response C tab
        console.log('\n=== Getting Response C ===');
        await clickInFrame(Runtime, '#kFJO1AFNXXgERBn_HB2OV-tab-2');
        await sleep(500);

        const responseC = await evaluateInFrame(Runtime, `
            (function() {
                const iframe = document.querySelector('#frm1');
                const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                const panel = iframeDoc.querySelector('#kFJO1AFNXXgERBn_HB2OV-tab-panel-2');
                return panel ? panel.innerText : 'Not found';
            })()
        `);
        console.log(responseC.substring(0, 500));

        // Save all responses
        const allData = {
            userRequest,
            responseA,
            responseB,
            responseC
        };
        fs.writeFileSync('/tmp/all_responses.json', JSON.stringify(allData, null, 2));
        console.log('\n=== Saved all responses to /tmp/all_responses.json ===');

    } catch (error) {
        console.error('Error:', error);
    } finally {
        if (client) {
            await client.close();
        }
    }
}

main();
