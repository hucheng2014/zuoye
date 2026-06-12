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

async function clickRadioInFrame(Runtime, name, value) {
    return await evaluateInFrame(Runtime, `
        (function() {
            const iframe = document.querySelector('#frm1');
            if (!iframe) return { success: false, error: 'No iframe' };

            const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
            const radio = iframeDoc.querySelector('input[name="${name}"][value="${value}"]');

            if (!radio) return { success: false, error: 'Radio not found: ${name}=${value}' };

            radio.click();
            return { success: true };
        })()
    `);
}

async function clickButtonInFrame(Runtime, selector) {
    return await evaluateInFrame(Runtime, `
        (function() {
            const iframe = document.querySelector('#frm1');
            if (!iframe) return { success: false, error: 'No iframe' };

            const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
            const button = iframeDoc.querySelector('${selector}');

            if (!button) return { success: false, error: 'Button not found: ${selector}' };

            button.click();
            return { success: true };
        })()
    `);
}

async function rateResponse(Runtime, responseName, ratings) {
    console.log(`\n=== Rating ${responseName} ===`);

    // Click on the response tab
    const tabIndex = responseName === 'A' ? 0 : responseName === 'B' ? 1 : 2;
    await clickButtonInFrame(Runtime, `#kFJO1AFNXXgERBn_HB2OV-tab-${tabIndex}`);
    await sleep(1000);

    // Get the radio button names for this response
    const radioNames = await evaluateInFrame(Runtime, `
        (function() {
            const iframe = document.querySelector('#frm1');
            const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
            const panel = iframeDoc.querySelector('#kFJO1AFNXXgERBn_HB2OV-tab-panel-${tabIndex}');

            if (!panel) return null;

            const radios = Array.from(panel.querySelectorAll('input[type="radio"]'));
            const names = {};

            radios.forEach(r => {
                const label = r.closest('.radio-buttons')?.querySelector('.legend')?.textContent || '';
                if (label.includes('follow')) names.instructionFollowing = r.name;
                else if (label.includes('concise')) names.concision = r.name;
                else if (label.includes('truthful')) names.truthfulness = r.name;
                else if (label.includes('satisfying')) names.satisfaction = r.name;
            });

            return names;
        })()
    `);

    console.log('Radio names:', radioNames);

    if (!radioNames) {
        console.log('Could not find radio names');
        return false;
    }

    // Fill in ratings
    if (ratings.instructionFollowing && radioNames.instructionFollowing) {
        console.log(`Setting IF: ${ratings.instructionFollowing}`);
        await clickRadioInFrame(Runtime, radioNames.instructionFollowing, ratings.instructionFollowing);
        await sleep(300);
    }

    if (ratings.concision && radioNames.concision) {
        console.log(`Setting Concision: ${ratings.concision}`);
        await clickRadioInFrame(Runtime, radioNames.concision, ratings.concision);
        await sleep(300);
    }

    if (ratings.truthfulness && radioNames.truthfulness) {
        console.log(`Setting Truthfulness: ${ratings.truthfulness}`);
        await clickRadioInFrame(Runtime, radioNames.truthfulness, ratings.truthfulness);
        await sleep(300);
    }

    if (ratings.satisfaction && radioNames.satisfaction) {
        console.log(`Setting Satisfaction: ${ratings.satisfaction}`);
        await clickRadioInFrame(Runtime, radioNames.satisfaction, ratings.satisfaction);
        await sleep(300);
    }

    return true;
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

        // Rate Response A
        await rateResponse(Runtime, 'A', {
            instructionFollowing: 'following_instructions',
            concision: 'acceptable',
            truthfulness: 'truthful',
            satisfaction: 'slightly_satisfying'
        });

        // Rate Response B
        await rateResponse(Runtime, 'B', {
            instructionFollowing: 'following_instructions',
            concision: 'good',
            truthfulness: 'truthful',
            satisfaction: 'slightly_satisfying'
        });

        // Rate Response C - has major factual error (Dept of Labor was 1913, not 1888)
        await rateResponse(Runtime, 'C', {
            instructionFollowing: 'partially_following_instructions',
            concision: 'good',
            truthfulness: 'not_truthful',
            satisfaction: 'not_satisfying'
        });

        console.log('\n=== All responses rated ===');

        // Take screenshot
        const screenshot = await Page.captureScreenshot({ format: 'png' });
        fs.writeFileSync('/tmp/after_rating.png', Buffer.from(screenshot.data, 'base64'));
        console.log('Screenshot saved');

    } catch (error) {
        console.error('Error:', error);
    } finally {
        if (client) {
            await client.close();
        }
    }
}

main();
