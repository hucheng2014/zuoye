#!/usr/bin/env node
/**
 * lane.js — Single-lane orchestrator for claw-code agent pipeline.
 *
 * One lane = one browser + one task type + one claw session.
 *
 * Lifecycle:
 *   1. Probe browser CDP → healthy?
 *   2. Detect task type on page
 *   3. Load SOP for that task type
 *   4. Run claw prompt with task context (extract → grade → fill → submit)
 *   5. Track session guard (hours, inactive %)
 *   6. Loop: next task or wait
 *
 * Usage:
 *   node lane.js --browser work-a [--max-tasks 10] [--dry-run]
 *   node lane.js --browser work-b --task-type PROOFREAD [--max-tasks 5]
 */
const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const http = require('http');

const SCRIPTS = __dirname;
const BROWSERS = JSON.parse(fs.readFileSync(path.join(SCRIPTS, 'browsers.json'), 'utf8')).browsers;
const TASK_TYPES = JSON.parse(fs.readFileSync(path.join(SCRIPTS, 'task_types.json'), 'utf8')).task_types;

// ──────────────────────── CLI args ────────────────────────
const args = process.argv.slice(2);
function arg(name, def) {
  const i = args.indexOf(`--${name}`);
  return i >= 0 && args[i + 1] ? args[i + 1] : def;
}
const flag = name => args.includes(`--${name}`);

const browserId = arg('browser', 'work-a');
const forcedType = arg('task-type', null);
const maxTasks = parseInt(arg('max-tasks', '999'), 10);
const dryRun = flag('dry-run');
const clawBin = arg('claw', `${process.env.HOME}/.cargo/bin/claw`);

const browser = BROWSERS.find(b => b.id === browserId);
if (!browser) { console.error(`Unknown browser: ${browserId}`); process.exit(1); }

const RUNS_DIR = path.join(SCRIPTS, '..', 'runs', `${browserId}-${new Date().toISOString().slice(0, 10)}`);
fs.mkdirSync(RUNS_DIR, { recursive: true });

// ──────────────────────── Helpers ────────────────────────
function log(msg) {
  const ts = new Date().toISOString().replace('T', ' ').slice(0, 19);
  const line = `[${ts}] [lane:${browserId}] ${msg}`;
  console.log(line);
  fs.appendFileSync(path.join(RUNS_DIR, 'lane.log'), line + '\n');
}

function httpGet(url, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, { timeout, headers: { Host: 'localhost:9222' } }, res => {
      let d = ''; res.on('data', c => d += c);
      res.on('end', () => { try { resolve(JSON.parse(d)); } catch { resolve(d); } });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
  });
}

async function isBrowserUp() {
  try { await httpGet(`${browser.cdp}/json/version`); return true; } catch { return false; }
}

async function detectTaskType() {
  if (forcedType) return forcedType;
  try {
    const out = execSync(`node ${path.join(SCRIPTS, 'detect_task.js')} --browser ${browserId} --json`, {
      encoding: 'utf8', timeout: 15000
    });
    const results = JSON.parse(out);
    const best = results.filter(r => r.task_type && r.task_type !== 'UNKNOWN')
      .sort((a, b) => b.confidence - a.confidence)[0];
    return best?.task_type || null;
  } catch { return null; }
}

function loadSOP(taskType) {
  const def = TASK_TYPES[taskType];
  if (!def?.sop) return null;
  const sopPath = path.resolve(SCRIPTS, def.sop);
  if (!fs.existsSync(sopPath)) return null;
  return fs.readFileSync(sopPath, 'utf8');
}

function buildClawPrompt(taskType, taskNum) {
  const def = TASK_TYPES[taskType];
  const sopRef = def.sop ? path.resolve(SCRIPTS, def.sop) : null;
  const scriptsDir = def.scripts_dir ? path.resolve(SCRIPTS, def.scripts_dir) : null;

  return `你是 ${def.label} 做题 Agent。当前是第 ${taskNum} 题。

## 环境
- CDP 端点: ${def.cdp}
- 脚本目录: ${scriptsDir}
- VNC: ${browser.vnc}
- 每题时间: ≥${def.time_per_task_min} 分钟
- 每日上限: ${def.daily_max_tasks} 题, ${def.daily_max_hours} 小时
- Inactive 上限: ${def.inactive_max_pct}%

## 做题流程
1. 运行 extract 脚本抓取当前题目: cd "${scriptsDir}" && ${def.extract_cmd || 'echo no-extract'}
2. 仔细阅读 SOP (${sopRef}) 分析题目
3. 根据 SOP 独立判断各评分维度
4. 生成答案 JSON
5. 运行 fill 脚本填写: cd "${scriptsDir}" && ${def.fill_cmd || 'echo no-fill'}
6. 确认后运行 submit: cd "${scriptsDir}" && ${def.submit_cmd || 'echo no-submit'}

## 铁律
- 禁止跳题，必须做当前页面显示的题目
- 各维度必须独立评估
- 填写前必须运行 keepalive 保活
- 做完后等待 Next Task 至少 4 秒
- 遇到登录/验证码/权限阻断，立即停止并通知用户打开 VNC: ${browser.vnc}

开始做第 ${taskNum} 题。先运行 extract 脚本获取当前题目数据。`;
}

// ──────────────────────── Main loop ────────────────────────
async function main() {
  log(`Starting lane: browser=${browserId} forced=${forcedType || 'auto'} max=${maxTasks} dry=${dryRun}`);

  // 1. Health check
  if (!(await isBrowserUp())) {
    log('ERROR: Browser CDP not reachable. Aborting.');
    process.exit(1);
  }
  log('Browser CDP is healthy.');

  let tasksDone = 0;

  while (tasksDone < maxTasks) {
    // 2. Detect task type
    const taskType = await detectTaskType();
    if (!taskType) {
      log('No task detected on page. Waiting 60s before retry...');
      await new Promise(r => setTimeout(r, 60000));
      continue;
    }

    const def = TASK_TYPES[taskType];
    if (!def) {
      log(`Unknown task type: ${taskType}. Waiting 60s...`);
      await new Promise(r => setTimeout(r, 60000));
      continue;
    }

    tasksDone++;
    const taskLabel = `${taskType}#${tasksDone}`;
    log(`Task detected: ${taskType} (${def.label}). Starting ${taskLabel}.`);

    // 3. Build prompt
    const prompt = buildClawPrompt(taskType, tasksDone);
    const promptFile = path.join(RUNS_DIR, `task-${String(tasksDone).padStart(3, '0')}-prompt.txt`);
    fs.writeFileSync(promptFile, prompt);

    if (dryRun) {
      log(`[DRY-RUN] Would invoke claw with prompt for ${taskLabel}. Skipping.`);
      continue;
    }

    // 4. Invoke claw
    log(`Invoking claw for ${taskLabel}...`);
    const outputFile = path.join(RUNS_DIR, `task-${String(tasksDone).padStart(3, '0')}-output.txt`);
    try {
      const clawArgs = [
        '--model', 'sonnet',
        '--permission-mode', 'danger-full-access',
        '--dangerously-skip-permissions',
        '--output-format', 'text',
        'prompt', prompt
      ];
      const result = execSync(`"${clawBin}" ${clawArgs.map(a => `"${a}"`).join(' ')}`, {
        encoding: 'utf8',
        timeout: def.time_per_task_min * 60 * 1000 * 3, // 3x the min time
        cwd: path.resolve(SCRIPTS, def.scripts_dir || '.'),
        env: {
          ...process.env,
          CDP_ENDPOINT: def.cdp,
        },
        maxBuffer: 10 * 1024 * 1024,
      });
      fs.writeFileSync(outputFile, result);
      log(`${taskLabel} completed. Output: ${outputFile}`);
    } catch (e) {
      log(`${taskLabel} FAILED: ${e.message?.slice(0, 200)}`);
      fs.writeFileSync(outputFile, `ERROR:\n${e.message}\n\n${e.stdout || ''}\n\n${e.stderr || ''}`);
    }

    // 5. Inter-task cooldown (respect min time)
    const cooldown = Math.max(5, def.time_per_task_min * 60 * 0.1); // 10% of min time
    log(`Cooldown ${cooldown}s before next task...`);
    await new Promise(r => setTimeout(r, cooldown * 1000));
  }

  log(`Lane finished. Tasks done: ${tasksDone}/${maxTasks}.`);
}

main().catch(e => { log(`FATAL: ${e.message}`); process.exit(1); });
