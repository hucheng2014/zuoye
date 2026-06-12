const wsUrl = "ws://127.0.0.1:9233/devtools/page/CBEF88970DD48CE74365EEA458E24C34";

console.log(`Connecting raw WebSocket to: ${wsUrl}`);
const ws = new WebSocket(wsUrl);

ws.onopen = () => {
  console.log('Connected! Fetching HTML...');
  ws.send(JSON.stringify({
    id: 1,
    method: "Runtime.evaluate",
    params: {
      expression: "document.documentElement.outerHTML",
      returnByValue: true
    }
  }));
};

ws.onmessage = (event) => {
  const res = JSON.parse(event.data);
  if (res.id === 1) {
    if (res.error) {
      console.error('Error:', res.error);
    } else {
      console.log('HTML Length:', res.result.result.value.length);
      console.log('--- HTML Start ---');
      console.log(res.result.result.value.slice(0, 1000));
      console.log('--- HTML End ---');
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
