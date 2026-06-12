#!/usr/bin/env node
/**
 * query_knowledge.js — Retrieve relevant knowledge chunks for a task type.
 *
 * Usage:
 *   node query_knowledge.js --task polls --query "how to score relevance"
 *   node query_knowledge.js --task proofread --query "CJK locale rules" --top 3
 *   node query_knowledge.js --task mail --list
 *   node query_knowledge.js --task ad --chunk excellent
 *   node query_knowledge.js --task polls --sop
 *   node query_knowledge.js --task proofread --flow
 *
 * Modes:
 *   --query <text>    Search chunks by relevance (keyword + TF-IDF scoring)
 *   --chunk <id>      Load a specific chunk by ID
 *   --list            List all available chunks for a task type
 *   --sop             Output the compact SOP
 *   --flow            Output the operation flow
 *   --json            Output results as JSON instead of markdown
 *   --top <n>         Number of results to return (default: 3)
 */
const fs = require('fs');
const path = require('path');

const KNOWLEDGE_DIR = path.join(__dirname, '..', 'knowledge');

function arg(name, def) {
  const i = process.argv.indexOf('--' + name);
  if (i === -1) return def;
  return process.argv[i + 1] || def;
}
function flag(name) {
  return process.argv.includes('--' + name);
}

function loadIndex(taskType) {
  const taskDir = resolveTaskDir(taskType);
  const indexPath = path.join(taskDir, 'index.json');
  if (!fs.existsSync(indexPath)) {
    console.error(`No knowledge base found for task type: ${taskType}`);
    console.error(`Available: ${listTaskTypes().join(', ')}`);
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(indexPath, 'utf8'));
}

function resolveTaskDir(taskType) {
  const normalized = taskType.toLowerCase().replace(/[_\s]+/g, '_');
  const mapping = {
    ta_polls: 'polls', polls: 'polls',
    mail: 'mail', tamessage: 'mail',
    proofread: 'proofread',
    ad: 'ad', search_ads: 'ad',
    rqoae: 'rqoae', audio: 'rqoae'
  };
  const dir = mapping[normalized] || normalized;
  return path.join(KNOWLEDGE_DIR, dir);
}

function listTaskTypes() {
  try {
    return fs.readdirSync(KNOWLEDGE_DIR)
      .filter(f => {
        const p = path.join(KNOWLEDGE_DIR, f);
        return fs.statSync(p).isDirectory() && fs.existsSync(path.join(p, 'index.json'));
      });
  } catch { return []; }
}

function readChunk(taskDir, chunkFile) {
  const p = path.join(taskDir, chunkFile);
  if (!fs.existsSync(p)) return null;
  return fs.readFileSync(p, 'utf8');
}

// --- TF-IDF keyword scoring ---

function tokenize(text) {
  return text.toLowerCase()
    .replace(/[^\w\s一-鿿]/g, ' ')
    .split(/\s+/)
    .filter(t => t.length > 1);
}

function termFrequency(tokens) {
  const tf = {};
  for (const t of tokens) tf[t] = (tf[t] || 0) + 1;
  const max = Math.max(...Object.values(tf), 1);
  for (const t in tf) tf[t] /= max;
  return tf;
}

function scoreChunk(query, chunk) {
  const queryTokens = tokenize(query);
  if (queryTokens.length === 0) return 0;

  const keywordTokens = chunk.keywords.flatMap(k => tokenize(k));
  const titleTokens = tokenize(chunk.title);
  const descTokens = tokenize(chunk.description);

  const allChunkTokens = [...keywordTokens, ...titleTokens, ...descTokens];
  const chunkTF = termFrequency(allChunkTokens);

  let score = 0;
  for (const qt of queryTokens) {
    // exact keyword match (highest weight)
    if (chunk.keywords.some(k => k.toLowerCase() === qt)) {
      score += 5;
    }
    // keyword substring match
    else if (chunk.keywords.some(k => k.toLowerCase().includes(qt) || qt.includes(k.toLowerCase()))) {
      score += 3;
    }
    // title match
    if (titleTokens.includes(qt)) {
      score += 2;
    }
    // description match
    if (descTokens.includes(qt)) {
      score += 1;
    }
    // TF-based match
    if (chunkTF[qt]) {
      score += chunkTF[qt] * 1.5;
    }
  }

  // priority bonus (priority 1 = +2, priority 5 = +0)
  const priorityBonus = (6 - (chunk.priority || 3)) * 0.3;
  score += priorityBonus;

  // normalize by query length
  return score / queryTokens.length;
}

function searchChunks(index, query, topN) {
  const scored = index.chunks.map(chunk => ({
    chunk,
    score: scoreChunk(query, chunk)
  }));

  scored.sort((a, b) => b.score - a.score);
  return scored.filter(s => s.score > 0.5).slice(0, topN);
}

// --- Output formatting ---

function formatMarkdown(results, taskDir) {
  const lines = [];
  for (const { chunk, score } of results) {
    const content = readChunk(taskDir, chunk.file);
    if (!content) continue;
    lines.push(`## ${chunk.title} (relevance: ${score.toFixed(1)})`);
    lines.push('');
    lines.push(content.trim());
    lines.push('');
    lines.push('---');
    lines.push('');
  }
  return lines.join('\n');
}

function formatJSON(results, taskDir) {
  return results.map(({ chunk, score }) => ({
    id: chunk.id,
    title: chunk.title,
    score: Math.round(score * 100) / 100,
    content: readChunk(taskDir, chunk.file)
  }));
}

// --- Main ---

function main() {
  const taskType = arg('task', null);
  if (!taskType) {
    console.error('Usage: node query_knowledge.js --task <type> [--query <text>|--chunk <id>|--list|--sop|--flow]');
    console.error(`Available task types: ${listTaskTypes().join(', ')}`);
    process.exit(1);
  }

  const taskDir = resolveTaskDir(taskType);
  const index = loadIndex(taskType);
  const asJSON = flag('json');

  // --sop: output compact SOP
  if (flag('sop')) {
    const content = readChunk(taskDir, index.compact_sop || 'compact_sop.md');
    if (!content) { console.error('No compact SOP found'); process.exit(1); }
    if (asJSON) {
      console.log(JSON.stringify({ task_type: index.task_type, type: 'compact_sop', content }));
    } else {
      console.log(content);
    }
    return;
  }

  // --flow: output operation flow
  if (flag('flow')) {
    const content = readChunk(taskDir, index.flow || 'flow.md');
    if (!content) { console.error('No flow file found'); process.exit(1); }
    if (asJSON) {
      console.log(JSON.stringify({ task_type: index.task_type, type: 'flow', content }));
    } else {
      console.log(content);
    }
    return;
  }

  // --list: list all chunks
  if (flag('list')) {
    if (asJSON) {
      console.log(JSON.stringify(index.chunks.map(c => ({
        id: c.id, title: c.title, description: c.description,
        keywords: c.keywords, priority: c.priority
      })), null, 2));
    } else {
      console.log(`Knowledge chunks for ${index.display_name || index.task_type}:\n`);
      for (const c of index.chunks) {
        const prio = c.priority ? ` [P${c.priority}]` : '';
        console.log(`  ${c.id}${prio} — ${c.title}`);
        console.log(`    ${c.description}`);
        console.log(`    keywords: ${c.keywords.join(', ')}`);
        console.log('');
      }
    }
    return;
  }

  // --chunk <id>: load specific chunk
  const chunkId = arg('chunk', null);
  if (chunkId) {
    const chunk = index.chunks.find(c => c.id === chunkId);
    if (!chunk) {
      console.error(`Chunk "${chunkId}" not found. Available: ${index.chunks.map(c => c.id).join(', ')}`);
      process.exit(1);
    }
    const content = readChunk(taskDir, chunk.file);
    if (!content) { console.error(`Chunk file not found: ${chunk.file}`); process.exit(1); }
    if (asJSON) {
      console.log(JSON.stringify({ id: chunk.id, title: chunk.title, content }));
    } else {
      console.log(`# ${chunk.title}\n\n${content}`);
    }
    return;
  }

  // --query <text>: search chunks
  const query = arg('query', null);
  if (!query) {
    console.error('Specify --query, --chunk, --list, --sop, or --flow');
    process.exit(1);
  }

  const topN = parseInt(arg('top', '3'), 10);
  const results = searchChunks(index, query, topN);

  if (results.length === 0) {
    if (asJSON) {
      console.log(JSON.stringify({ query, results: [] }));
    } else {
      console.log(`No relevant chunks found for: "${query}"`);
      console.log(`Try: node query_knowledge.js --task ${taskType} --list`);
    }
    return;
  }

  if (asJSON) {
    console.log(JSON.stringify({
      query,
      task_type: index.task_type,
      results: formatJSON(results, taskDir)
    }, null, 2));
  } else {
    console.log(`Found ${results.length} relevant chunks for "${query}":\n`);
    console.log(formatMarkdown(results, taskDir));
  }
}

main();
