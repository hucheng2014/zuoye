/** TAMESSAGE 单题目标活跃时长（秒）。默认 9 分钟。 */
const SUBMIT_AT_SEC = parseInt(process.env.TAMESSAGE_SUBMIT_AT || '540', 10);
const KEEPALIVE_MS = parseInt(
  process.env.TAMESSAGE_KEEPALIVE_MS || String(SUBMIT_AT_SEC * 1000),
  10
);

module.exports = { SUBMIT_AT_SEC, KEEPALIVE_MS };
