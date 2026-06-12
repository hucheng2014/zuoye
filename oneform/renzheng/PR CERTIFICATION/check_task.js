const CDP = require('chrome-remote-interface');

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
    let client;
    try {
        console.log('Connecting to browser...');
        client = await CDP({ host: '127.0.0.1', port: 9235 });

        const { Network, Page, Runtime, Target } = client;

        await Network.enable();
        await Page.enable();
        await Runtime.enable();
        await Target.setDiscoverTargets({ discover: true });

        console.log('Connected successfully!');

        // Wait a bit for page to load
        await sleep(2000);

        // Get all targets (including iframes)
        const targets = await Target.getTargets();
        console.log('\nFound targets:', targets.targetInfos.length);

        for (const target of targets.targetInfos) {
            console.log(`- ${target.type}: ${target.url}`);
        }

        // Find the iframe target
        const iframeTarget = targets.targetInfos.find(t =>
            t.type === 'iframe' && t.url.includes('task-editor')
        );

        if (iframeTarget) {
            console.log('\nConnecting to iframe...');
            const iframeClient = await CDP({
                host: '127.0.0.1',
                port: 9235,
                target: iframeTarget.targetId
            });

            const { Runtime: IframeRuntime, Page: IframePage } = iframeClient;
            await IframeRuntime.enable();
            await IframePage.enable();

            await sleep(1000);

            // Get iframe content
            const htmlResult = await IframeRuntime.evaluate({
                expression: 'document.documentElement.outerHTML'
            });
            require('fs').writeFileSync('/tmp/iframe_content.html', htmlResult.result.value);
            console.log('Iframe HTML saved to /tmp/iframe_content.html');

            // Take screenshot of iframe
            const screenshot = await IframePage.captureScreenshot({ format: 'png' });
            require('fs').writeFileSync('/tmp/iframe_screenshot.png', Buffer.from(screenshot.data, 'base64'));
            console.log('Iframe screenshot saved to /tmp/iframe_screenshot.png');

            // Check for ACCEPT button
            const acceptCheck = await IframeRuntime.evaluate({
                expression: `
                    (function() {
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const acceptBtn = buttons.find(b => b.textContent.toUpperCase().includes('ACCEPT'));
                        return {
                            hasAccept: !!acceptBtn,
                            acceptText: acceptBtn ? acceptBtn.textContent : null,
                            allButtons: buttons.map(b => b.textContent).filter(t => t.trim())
                        };
                    })()
                `
            });
            console.log('\nButton check:', JSON.stringify(acceptCheck.result.value, null, 2));

            await iframeClient.close();
        } else {
            console.log('Iframe target not found');
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
