# Repository Guidelines

## Project Structure & Module Organization
This repository is document-first. The main inputs are `source.pdf` and `source.txt`. The derived deliverables are the two Markdown summaries:
`Writing_Tools_0_to_1_Composition_Guidelines_V1_中文详细总结.md` and
`Writing_Tools_0_to_1_Composition_Guidelines_V1_中文评分操作手册.md`.

Lightweight browser-control tooling is configured through `package.json` and `package-lock.json`. Generated runtime artifacts should stay out of version control, especially `node_modules/`, `.playwright-mcp-output/`, and `.chrome-cdp-profile/`.

## Build, Test, and Development Commands
- `npm install`: installs the local Playwright MCP dependency.
- `npm run mcp:playwright`: starts a Playwright MCP session that opens Chrome.
- `npm run mcp:playwright:headless`: runs the same MCP server without a visible browser.
- `npm run mcp:playwright:cdp`: connects Playwright MCP to an existing Chrome debugging port at `127.0.0.1:9222`.
- `npm run chrome:cdp`: launches Google Chrome with remote debugging enabled for manual browser control.

There is no formal build pipeline or automated test suite in this repository.

## Coding Style & Naming Conventions
Use concise, direct Markdown. Keep headings short and descriptive. Preserve the existing Chinese filenames for derived documents. For JSON and shell commands, use standard two-space formatting and avoid introducing unnecessary keys or wrappers.

## Testing Guidelines
Validation is mostly manual:
- Open or regenerate the document outputs and confirm the content matches the source PDF/TXT.
- For browser tooling changes, verify `codex mcp list` shows the expected server and that the chosen command starts cleanly.

## Commit & Pull Request Guidelines
No git history is available in this checkout, so there is no repo-specific commit convention to inherit. Use short imperative commit subjects such as `Add Playwright MCP scripts` or `Document repository workflow`.

Pull requests should describe what changed, list the files touched, and note any manual verification commands run. Include screenshots only when a browser workflow or rendered document behavior changed.

## Security & Configuration Tips
Do not commit local browser profiles, output folders, or installed packages. If you add new MCP servers or browser flags, keep them scoped to this repo and document the exact launch command in `package.json`.
