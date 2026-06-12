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

        // Get iframe content
        const iframeContent = await evaluateInFrame(Runtime, `
            (function() {
                const iframe = document.querySelector('#frm1');
                if (!iframe) return { error: 'No iframe found' };

                try {
                    const iframeWindow = iframe.contentWindow;
                    const iframeDoc = iframe.contentDocument || iframeWindow.document;

                    // Get all text content
                    const bodyText = iframeDoc.body ? iframeDoc.body.innerText : '';

                    // Get all buttons
                    const buttons = Array.from(iframeDoc.querySelectorAll('button')).map(b => ({
                        text: b.innerText.trim(),
                        className: b.className,
                        id: b.id,
                        ariaLabel: b.getAttribute('aria-label')
                    })).filter(b => b.text || b.ariaLabel);

                    // Look for ACCEPT button
                    const acceptButton = buttons.find(b =>
                        (b.text && b.text.toUpperCase().includes('ACCEPT')) ||
                        (b.ariaLabel && b.ariaLabel.toUpperCase().includes('ACCEPT'))
                    );

                    // Get form fields
                    const inputs = Array.from(iframeDoc.querySelectorAll('input, textarea, select')).map(el => ({
                        type: el.type,
                        name: el.name,
                        id: el.id,
                        value: el.value
                    }));

                    return {
                        hasIframe: true,
                        bodyText: bodyText.substring(0, 2000),
                        buttons: buttons.slice(0, 20),
                        hasAcceptButton: !!acceptButton,
                        acceptButton: acceptButton,
                        inputCount: inputs.length,
                        inputs: inputs.slice(0, 10)
                    };
                } catch (e) {
                    return { error: 'Cannot access iframe content: ' + e.message };
                }
            })()
        `);

        console.log('\n=== IFRAME CONTENT ===');
        console.log(JSON.stringify(iframeContent, null, 2));

        // Save to file for analysis
        fs.writeFileSync('/tmp/iframe_analysis.json', JSON.stringify(iframeContent, null, 2));
        console.log('\nSaved to /tmp/iframe_analysis.json');

        // Take screenshot
        const screenshot = await Page.captureScreenshot({ format: 'png' });
        fs.writeFileSync('/tmp/task_view.png', Buffer.from(screenshot.data, 'base64'));
        console.log('Screenshot saved to /tmp/task_view.png');

    } catch (error) {
        console.error('Error:', error);
    } finally {
        if (client) {
            await client.close();
        }
    }
}

main();
