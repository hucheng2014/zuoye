const wsUrl = "ws://127.0.0.1:9233/devtools/page/CBEF88970DD48CE74365EEA458E24C34";

console.log(`Connecting raw WebSocket to: ${wsUrl}`);
const ws = new WebSocket(wsUrl);

ws.onopen = () => {
  console.log('Connected! Fetching Frame Tree...');
  ws.send(JSON.stringify({ id: 1, method: "Page.enable" }));
  ws.send(JSON.stringify({ id: 2, method: "Page.getFrameTree" }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.id === 2) {
    console.log('--- Simplified Frame Tree ---');
    function printFrame(node, indent = '') {
      const f = node.frame;
      console.log(`${indent}- Frame ID: ${f.id}, URL: "${f.url}"`);
      if (node.childFrames) {
        for (const child of node.childFrames) {
          printFrame(child, indent + '  ');
        }
      }
    }
    if (data.result && data.result.frameTree) {
      printFrame(data.result.frameTree);
    }
    console.log('------------------------------');
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
