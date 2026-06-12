const wsUrl = "ws://127.0.0.1:9233/devtools/page/CBEF88970DD48CE74365EEA458E24C34";

console.log(`Connecting raw WebSocket to: ${wsUrl}`);
const ws = new WebSocket(wsUrl);

ws.onopen = () => {
  console.log('Connected! Evaluating document.body.innerText...');
  const msg = JSON.stringify({
    id: 2,
    method: "Runtime.evaluate",
    params: {
      expression: "document.body.innerText",
      returnByValue: true
    }
  });
  ws.send(msg);
};

ws.onmessage = (event) => {
  const res = JSON.parse(event.data);
  if (res.id === 2) {
    if (res.error) {
      console.error('Evaluation error:', res.error);
    } else {
      console.log('--- Page text preview ---');
      console.log(res.result.result.value);
      console.log('-------------------------');
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
  console.log('Timeout reached. Closing WebSocket...');
  ws.close();
}, 5000);
