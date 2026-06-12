# Workspace Browser Automation

This workspace intentionally uses a hybrid browser setup:

- Production task automation stays in code with Playwright/CDP scripts and project-specific safe-submit validators.
- `agent-browser` is available for interactive inspection, screenshots, selector discovery, and one-off debugging.

Use the root helper instead of remembering CDP ports:

```bash
/Users/xaa/zuoye/tools/agent-browser.sh list
/Users/xaa/zuoye/tools/agent-browser.sh <target> snapshot -i
/Users/xaa/zuoye/tools/agent-browser.sh <target> screenshot /tmp/current.png
```

Do not replace safe submit scripts with ad hoc `agent-browser click` commands.

Full policy: `/Users/xaa/zuoye/docs/agent-browser-integration.md`.
