const wsUrl = "ws://127.0.0.1:9233/devtools/page/CBEF88970DD48CE74365EEA458E24C34";

console.log(`Connecting raw WebSocket to: ${wsUrl}`);
const ws = new WebSocket(wsUrl);

ws.onopen = () => {
  console.log('Connected! Enabling Console and Log domains...');
  ws.send(JSON.stringify({ id: 1, method: "Log.enable" }));
  ws.send(JSON.stringify({ id: 2, method: "Runtime.enable" }));
  ws.send(JSON.stringify({ id: 3, method: "Runtime.evaluate", params: { expression: "console.error" } }));
};

const logs = [];

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.method === "Runtime.consoleAPICalled") {
    console.log('[Console]', msg.params.type, msg.params.args.map(a => a.value).join(' '));
  } else if (msg.method === "Log.entryAdded") {
    console.log('[Log]', msg.params.entry.level, msg.params.entry.text);
  } else if (msg.id === 3) {
    console.log('Runtime evaluation result:', JSON.stringify(msg.result, null, 2));
    // Close after getting evaluation
    setTimeout(() => ws.close(), 1000);
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
}, 4000);
