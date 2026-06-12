const CDP = require('chrome-remote-interface');

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
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

        await sleep(2000);

        // Try to access iframe content
        const iframeCheck = await Runtime.evaluate({
            expression: `
                (function() {
                    const iframe = document.querySelector('#frm1');
                    if (!iframe) return { error: 'iframe not found' };

                    try {
                        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
                        const buttons = Array.from(iframeDoc.querySelectorAll('button'));
                        const acceptBtn = buttons.find(b => b.textContent.toUpperCase().includes('ACCEPT'));

                        return {
                            hasIframe: true,
                            hasAccept: !!acceptBtn,
                            acceptText: acceptBtn ? acceptBtn.textContent : null,
                            allButtons: buttons.map(b => ({
                                text: b.textContent.trim(),
                                visible: b.offsetParent !== null
                            })).filter(b => b.text),
                            bodyText: iframeDoc.body ? iframeDoc.body.innerText.substring(0, 500) : 'no body'
                        };
                    } catch (e) {
                        return { error: 'Cannot access iframe: ' + e.message };
                    }
                })()
            `
        });

        console.log('\nIframe check result:', JSON.stringify(iframeCheck.result.value, null, 2));

        // Take a full page screenshot
        const screenshot = await Page.captureScreenshot({ format: 'png', fromSurface: true });
        require('fs').writeFileSync('/tmp/full_page.png', Buffer.from(screenshot.data, 'base64'));
        console.log('Full page screenshot saved to /tmp/full_page.png');

    } catch (error) {
        console.error('Error:', error);
    } finally {
        if (client) {
            await client.close();
        }
    }
}

main();
