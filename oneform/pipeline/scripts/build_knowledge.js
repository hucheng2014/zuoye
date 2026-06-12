#!/usr/bin/env node
/**
 * build_knowledge.js — Process tutorial MDs into the knowledge base.
 *
 * Usage:
 *   node build_knowledge.js                    # Rebuild all task types
 *   node build_knowledge.js --task polls       # Rebuild one task type
 *   node build_knowledge.js --validate         # Validate all indexes
 *   node build_knowledge.js --stats            # Show knowledge base stats
 *
 * This script validates the knowledge base structure, checks for missing
 * chunks, and reports stats. To add a new task type:
 *   1. Create pipeline/knowledge/<type>/index.json following _schema.json
 *   2. Create compact_sop.md, flow.md, and chunk files
 *   3. Run: node build_knowledge.js --validate
 */
const fs = require('fs');
const path = require('path');

const KNOWLEDGE_DIR = path.join(__dirname, '..', 'knowledge');
const SCHEMA_PATH = path.join(KNOWLEDGE_DIR, '_schema.json');

function arg(name, def) {
  const i = process.argv.indexOf('--' + name);
  if (i === -1) return def;
  return process.argv[i + 1] || def;
}
function flag(name) {
  return process.argv.includes('--' + name);
}

function listTaskDirs() {
  return fs.readdirSync(KNOWLEDGE_DIR)
    .filter(f => {
      const p = path.join(KNOWLEDGE_DIR, f);
      return fs.statSync(p).isDirectory() && fs.existsSync(path.join(p, 'index.json'));
    });
}

function validateIndex(taskDir, taskName) {
  const errors = [];
  const warnings = [];
  const indexPath = path.join(KNOWLEDGE_DIR, taskDir, 'index.json');

  let index;
  try {
    index = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
  } catch (e) {
    errors.push(`Failed to parse index.json: ${e.message}`);
    return { errors, warnings, stats: null };
  }

  // required fields
  for (const field of ['task_type', 'version', 'chunks', 'compact_sop', 'flow']) {
    if (!index[field]) errors.push(`Missing required field: ${field}`);
  }

  // check compact_sop exists
  const sopPath = path.join(KNOWLEDGE_DIR, taskDir, index.compact_sop || 'compact_sop.md');
  if (!fs.existsSync(sopPath)) {
    errors.push(`compact_sop file not found: ${index.compact_sop}`);
  }

  // check flow exists
  const flowPath = path.join(KNOWLEDGE_DIR, taskDir, index.flow || 'flow.md');
  if (!fs.existsSync(flowPath)) {
    errors.push(`flow file not found: ${index.flow}`);
  }

  // check chunks
  let totalSize = 0;
  const chunkIds = new Set();
  if (Array.isArray(index.chunks)) {
    for (const chunk of index.chunks) {
      if (!chunk.id) errors.push('Chunk missing id');
      if (!chunk.file) errors.push(`Chunk ${chunk.id}: missing file`);
      if (!chunk.title) warnings.push(`Chunk ${chunk.id}: missing title`);
      if (!chunk.keywords || chunk.keywords.length === 0) {
        warnings.push(`Chunk ${chunk.id}: no keywords (won't be searchable)`);
      }

      if (chunkIds.has(chunk.id)) {
        errors.push(`Duplicate chunk id: ${chunk.id}`);
      }
      chunkIds.add(chunk.id);

      if (chunk.file) {
        const chunkPath = path.join(KNOWLEDGE_DIR, taskDir, chunk.file);
        if (!fs.existsSync(chunkPath)) {
          errors.push(`Chunk file not found: ${chunk.file}`);
        } else {
          const stat = fs.statSync(chunkPath);
          totalSize += stat.size;
          if (chunk.size_bytes && Math.abs(chunk.size_bytes - stat.size) > stat.size * 0.5) {
            warnings.push(`Chunk ${chunk.id}: size_bytes (${chunk.size_bytes}) differs significantly from actual (${stat.size})`);
          }
        }
      }
    }
  }

  // check examples
  if (Array.isArray(index.examples)) {
    for (const ex of index.examples) {
      if (ex.file) {
        const exPath = path.join(KNOWLEDGE_DIR, taskDir, ex.file);
        if (!fs.existsSync(exPath)) {
          warnings.push(`Example file not found: ${ex.file}`);
        }
      }
    }
  }

  // check source files exist
  const repoRoot = path.join(__dirname, '..', '..');
  if (Array.isArray(index.source_files)) {
    for (const src of index.source_files) {
      const srcPath = path.join(repoRoot, src);
      if (!fs.existsSync(srcPath)) {
        warnings.push(`Source file not found: ${src}`);
      }
    }
  }

  // SOP size check
  if (fs.existsSync(sopPath)) {
    const sopSize = fs.statSync(sopPath).size;
    if (sopSize > 4096) {
      warnings.push(`compact_sop.md is ${sopSize} bytes (target: <2KB for token efficiency)`);
    }
  }

  const stats = {
    task_type: index.task_type,
    version: index.version,
    chunks: index.chunks ? index.chunks.length : 0,
    examples: index.examples ? index.examples.length : 0,
    total_chunk_bytes: totalSize,
    sop_bytes: fs.existsSync(sopPath) ? fs.statSync(sopPath).size : 0,
    flow_bytes: fs.existsSync(flowPath) ? fs.statSync(flowPath).size : 0
  };

  return { errors, warnings, stats };
}

function updateChunkSizes(taskDir) {
  const indexPath = path.join(KNOWLEDGE_DIR, taskDir, 'index.json');
  const index = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
  let changed = false;

  for (const chunk of index.chunks) {
    const chunkPath = path.join(KNOWLEDGE_DIR, taskDir, chunk.file);
    if (fs.existsSync(chunkPath)) {
      const actual = fs.statSync(chunkPath).size;
      if (chunk.size_bytes !== actual) {
        chunk.size_bytes = actual;
        changed = true;
      }
    }
  }

  if (changed) {
    fs.writeFileSync(indexPath, JSON.stringify(index, null, 2) + '\n');
    return true;
  }
  return false;
}

function main() {
  const taskFilter = arg('task', null);

  if (flag('stats')) {
    const dirs = taskFilter ? [resolveTaskName(taskFilter)] : listTaskDirs();
    console.log('Knowledge Base Statistics\n');
    console.log('Task Type       | Ver   | Chunks | Examples | Chunks KB | SOP KB | Flow KB');
    console.log('----------------|-------|--------|----------|-----------|--------|--------');
    for (const d of dirs) {
      const { stats } = validateIndex(d, d);
      if (!stats) continue;
      console.log(
        `${stats.task_type.padEnd(16)}| ${stats.version.padEnd(6)}| ${String(stats.chunks).padEnd(7)}| ${String(stats.examples).padEnd(9)}| ${(stats.total_chunk_bytes / 1024).toFixed(1).padStart(9)} | ${(stats.sop_bytes / 1024).toFixed(1).padStart(6)} | ${(stats.flow_bytes / 1024).toFixed(1).padStart(6)}`
      );
    }
    return;
  }

  if (flag('validate')) {
    const dirs = taskFilter ? [resolveTaskName(taskFilter)] : listTaskDirs();
    let hasErrors = false;

    for (const d of dirs) {
      const { errors, warnings, stats } = validateIndex(d, d);
      const label = stats ? stats.task_type : d;

      if (errors.length === 0 && warnings.length === 0) {
        console.log(`✓ ${label} — ${stats.chunks} chunks, valid`);
      } else {
        if (errors.length > 0) {
          hasErrors = true;
          console.log(`✗ ${label} — ${errors.length} error(s):`);
          for (const e of errors) console.log(`    ERROR: ${e}`);
        }
        if (warnings.length > 0) {
          console.log(`⚠ ${label} — ${warnings.length} warning(s):`);
          for (const w of warnings) console.log(`    WARN: ${w}`);
        }
      }

      // auto-update chunk sizes
      try {
        if (updateChunkSizes(d)) {
          console.log(`  → Updated chunk size_bytes in index.json`);
        }
      } catch {}
    }

    process.exit(hasErrors ? 1 : 0);
  }

  // Default: validate + update sizes for all or filtered
  const dirs = taskFilter ? [resolveTaskName(taskFilter)] : listTaskDirs();
  console.log(`Building knowledge base for: ${dirs.join(', ')}\n`);

  for (const d of dirs) {
    console.log(`Processing ${d}...`);

    // update sizes
    try {
      if (updateChunkSizes(d)) {
        console.log(`  Updated chunk sizes`);
      }
    } catch (e) {
      console.error(`  Failed to update sizes: ${e.message}`);
    }

    // validate
    const { errors, warnings, stats } = validateIndex(d, d);
    if (errors.length > 0) {
      console.error(`  ${errors.length} error(s):`);
      for (const e of errors) console.error(`    ${e}`);
    }
    if (warnings.length > 0) {
      console.log(`  ${warnings.length} warning(s):`);
      for (const w of warnings) console.log(`    ${w}`);
    }
    if (errors.length === 0) {
      console.log(`  ✓ Valid — ${stats.chunks} chunks, ${(stats.total_chunk_bytes / 1024).toFixed(1)}KB total`);
    }
  }
}

function resolveTaskName(name) {
  const normalized = name.toLowerCase().replace(/[_\s]+/g, '_');
  const mapping = {
    ta_polls: 'polls', polls: 'polls',
    mail: 'mail', tamessage: 'mail',
    proofread: 'proofread',
    ad: 'ad', search_ads: 'ad',
    rqoae: 'rqoae', audio: 'rqoae'
  };
  return mapping[normalized] || normalized;
}

main();
