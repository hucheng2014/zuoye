const CDP = require('chrome-remote-interface');

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
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
        await sleep(1000);

        const structure = await Runtime.evaluate({
            expression: `
                (function() {
                    const result = [];
                    
                    // User Request
                    const userRequestHeader = document.querySelector('h1, h2, .user-request-header');
                    const userRequestText = document.querySelector('.user-request, blockquote, [class*="user-request"]') || document.body;
                    
                    // Look for tabs
                    const tabs = Array.from(document.querySelectorAll('[role="tab"]')).map(t => ({
                        id: t.id,
                        text: t.textContent.trim(),
                        selected: t.getAttribute('aria-selected') === 'true'
                    }));

                    // Look for all radio buttons and their surrounding text/legend
                    const radios = Array.from(document.querySelectorAll('input[type="radio"]'));
                    const radioData = radios.map(r => {
                        const container = r.closest('div, fieldset, [role="radiogroup"]');
                        const legend = container ? (container.querySelector('.legend, legend, [class*="legend"]') || container) : null;
                        const label = r.closest('label') || document.querySelector(\`label[for="\${r.id}"]\`);
                        return {
                            name: r.name,
                            id: r.id,
                            value: r.value,
                            checked: r.checked,
                            labelText: label ? label.textContent.trim() : '',
                            legendText: legend ? legend.textContent.substring(0, 100).trim() : ''
                        };
                    });

                    // Look for buttons
                    const buttons = Array.from(document.querySelectorAll('button')).map(b => ({
                        id: b.id,
                        text: b.textContent.trim(),
                        visible: b.offsetParent !== null
                    })).filter(b => b.text);

                    return {
                        title: document.title,
                        tabs: tabs,
                        radioCount: radios.length,
                        radioData: radioData,
                        buttons: buttons
                    };
                })()
            `,
            returnByValue: true
        });

        console.log(JSON.stringify(structure.result.value, null, 2));

    } catch (error) {
        console.error('Error:', error);
    } finally {
        if (client) {
            await client.close();
        }
    }
}

main();
