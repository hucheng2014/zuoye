const CDP = require('chrome-remote-interface');
const fs = require('fs');

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
    let client;
    try {
        console.log('Connecting to browser...');
        client = await CDP({ host: '127.0.0.1', port: 9235 });

        const { Page, Runtime, DOM } = client;

        await Page.enable();
        await Runtime.enable();
        await DOM.enable();

        console.log('Connected successfully!');
        await sleep(2000);

        // Get document
        const doc = await DOM.getDocument({ depth: -1 });
        console.log('Got document');

        // Search for buttons
        const buttonSearch = await DOM.performSearch({
            query: 'button',
            includeUserAgentShadowDOM: true
        });

        console.log(`Found ${buttonSearch.resultCount} buttons`);

        // Get button texts
        if (buttonSearch.resultCount > 0) {
            const results = await DOM.getSearchResults({
                searchId: buttonSearch.searchId,
                fromIndex: 0,
                toIndex: Math.min(buttonSearch.resultCount, 20)
            });

            console.log('\nButton node IDs:', results.nodeIds);

            for (const nodeId of results.nodeIds) {
                try {
                    const outerHTML = await DOM.getOuterHTML({ nodeId });
                    console.log('\nButton HTML:', outerHTML.outerHTML.substring(0, 200));
                } catch (e) {
                    console.log('Could not get button HTML:', e.message);
                }
            }
        }

        // Take screenshot
        const screenshot = await Page.captureScreenshot({ format: 'png' });
        fs.writeFileSync('/tmp/current_state.png', Buffer.from(screenshot.data, 'base64'));
        console.log('\nScreenshot saved');

        // Try simple evaluation
        try {
            const simpleEval = await Runtime.evaluate({
                expression: '1 + 1'
            });
            console.log('\nSimple eval result:', simpleEval.result);

            const titleEval = await Runtime.evaluate({
                expression: 'document.title'
            });
            console.log('Title:', titleEval.result);

            const bodyEval = await Runtime.evaluate({
                expression: 'document.body.innerText.substring(0, 500)'
            });
            console.log('Body text:', bodyEval.result);
        } catch (e) {
            console.log('Eval error:', e);
        }

    } catch (error) {
        console.error('Error:', error);
    } finally {
        if (client) {
            await client.close();
        }
    }
}

main();
