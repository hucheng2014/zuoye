const fs = require('fs');
const path = require('path');

const wsUrl = "ws://127.0.0.1:9233/devtools/page/CBEF88970DD48CE74365EEA458E24C34";

console.log(`Connecting raw WebSocket to: ${wsUrl}`);
const ws = new WebSocket(wsUrl);

ws.onopen = () => {
  console.log('Connected! Capturing screenshot...');
  ws.send(JSON.stringify({
    id: 1,
    method: "Page.captureScreenshot",
    params: {
      format: "png"
    }
  }));
};

ws.onmessage = (event) => {
  const res = JSON.parse(event.data);
  if (res.id === 1) {
    if (res.error) {
      console.error('Error:', res.error);
    } else {
      const buffer = Buffer.from(res.result.data, 'base64');
      const screenshotPath = path.resolve(__dirname, '../runs/current-screenshot.png');
      fs.writeFileSync(screenshotPath, buffer);
      console.log(`Screenshot saved successfully to ${screenshotPath}`);
    }
    ws.close();
  }
};

ws.onerror = (err) => {
  console.error('WebSocket error:', err);
};

ws.onclose = () => {
  console.log('WebSocket connection closed.');
};

setTimeout(() => {
  console.log('Timeout. Closing WebSocket...');
  ws.close();
}, 5000);
