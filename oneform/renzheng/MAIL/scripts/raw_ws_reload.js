const wsUrl = "ws://127.0.0.1:9233/devtools/page/CBEF88970DD48CE74365EEA458E24C34";

console.log(`Connecting raw WebSocket to: ${wsUrl}`);
const ws = new WebSocket(wsUrl);

ws.onopen = () => {
  console.log('Connected! Sending Page.reload command...');
  const msg = JSON.stringify({
    id: 1,
    method: "Page.reload",
    params: {
      ignoreCache: true
    }
  });
  ws.send(msg);
};

ws.onmessage = (event) => {
  console.log('Received response:', event.data);
  ws.close();
};

ws.onerror = (err) => {
  console.error('WebSocket error:', err);
};

ws.onclose = () => {
  console.log('WebSocket connection closed.');
};

setTimeout(() => {
  console.log('Timeout reached. Closing WebSocket...');
  ws.close();
}, 5000);
