"use strict";

const fs = require("fs");
const path = require("path");
const vscode = require("vscode");

const EXTENSION_ID = "local.trae-trial-bridge";

function writeJson(filePath, data) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), "utf8");
}

function readPayload(uri) {
  const params = new URLSearchParams(uri.query || "");
  const payloadFile = params.get("payloadFile");
  if (!payloadFile) {
    throw new Error("Missing payloadFile query parameter.");
  }
  const raw = fs.readFileSync(payloadFile, "utf8");
  const payload = JSON.parse(raw);
  if (!payload || typeof payload !== "object") {
    throw new Error("Payload must be an object.");
  }
  return payload;
}

async function executeWithRetry(command, args, attempts = 20) {
  let lastError;
  for (let i = 0; i < attempts; i += 1) {
    try {
      return await vscode.commands.executeCommand(command, ...args);
    } catch (error) {
      lastError = error;
      const message = error instanceof Error ? error.message : String(error);
      if (!/not found|not registered|command/i.test(message)) {
        throw error;
      }
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
  }
  throw lastError || new Error(`Command did not become available: ${command}`);
}

async function getCurrentSessionId() {
  try {
    return await executeWithRetry("icube.chat.getCurrentSessionId", [], 6);
  } catch {
    return undefined;
  }
}

async function runPayload(payload) {
  const action = payload.action || "ping";
  if (action === "ping") {
    return {
      ok: true,
      extensionId: EXTENSION_ID,
      workspaceFolders: (vscode.workspace.workspaceFolders || []).map((folder) => folder.uri.toString())
    };
  }

  if (action === "currentSession") {
    return {
      ok: true,
      sessionId: await getCurrentSessionId()
    };
  }

  if (action === "send") {
    const inputs = Array.isArray(payload.inputs) ? payload.inputs : [String(payload.input || "")];
    if (!inputs.length || inputs.every((item) => !item)) {
      throw new Error("send requires non-empty inputs.");
    }
    const options = payload.options && typeof payload.options === "object" ? payload.options : {};
    const beforeSessionId = await getCurrentSessionId();
    const result = await executeWithRetry("icube.chat.sendToAgentNonBlocking", [inputs, options], 30);
    const sessionId = result && result.sessionId ? result.sessionId : await getCurrentSessionId();
    return {
      ok: true,
      beforeSessionId,
      sessionId,
      result
    };
  }

  throw new Error(`Unknown bridge action: ${action}`);
}

async function handlePayload(payload) {
  const startedAt = new Date().toISOString();
  try {
    const data = await runPayload(payload);
    return {
      requestId: payload.requestId,
      startedAt,
      completedAt: new Date().toISOString(),
      ...data
    };
  } catch (error) {
    return {
      requestId: payload.requestId,
      startedAt,
      completedAt: new Date().toISOString(),
      ok: false,
      error: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined
    };
  }
}

async function handleUri(uri) {
  const payload = readPayload(uri);
  const result = await handlePayload(payload);
  if (!payload.resultFile) {
    throw new Error("Missing resultFile in payload.");
  }
  writeJson(payload.resultFile, result);
}

function activate(context) {
  const output = vscode.window.createOutputChannel("Trae Trial Bridge");
  output.appendLine(`Activated ${EXTENSION_ID}`);

  context.subscriptions.push(output);
  context.subscriptions.push(vscode.window.registerUriHandler({ handleUri }));
  context.subscriptions.push(vscode.commands.registerCommand("trae-trial-bridge.ping", async () => runPayload({ action: "ping" })));
  context.subscriptions.push(vscode.commands.registerCommand("trae-trial-bridge.currentSession", async () => runPayload({ action: "currentSession" })));
  context.subscriptions.push(vscode.commands.registerCommand("trae-trial-bridge.send", async (payload) => runPayload({ ...payload, action: "send" })));
}

function deactivate() {}

module.exports = {
  activate,
  deactivate
};
