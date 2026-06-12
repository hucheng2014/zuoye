const wsUrl = "ws://127.0.0.1:9233/devtools/page/CBEF88970DD48CE74365EEA458E24C34";

console.log(`Connecting raw WebSocket to: ${wsUrl}`);
const ws = new WebSocket(wsUrl);

ws.onopen = () => {
  console.log('Connected! Enabling Page domain...');
  ws.send(JSON.stringify({ id: 1, method: "Page.enable" }));
  ws.send(JSON.stringify({ id: 2, method: "Page.getNavigationHistory" }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received message:', JSON.stringify(data, null, 2));
  if (data.id === 2) {
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
}, 6000);
