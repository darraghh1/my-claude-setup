# Plugins

Claude Code supports optional plugins that extend its capabilities with language server features like go-to-definition, diagnostics, and code intelligence.

**Plugins are optional.** This setup works fully without any plugins installed. The hooks, skills, agents, and rules all function independently.

---

## Built-in Functionality (No Plugin Needed)

The **explanatory-output-style** plugin (available in the official plugins cache) provides educational insights during sessions. This functionality is **already built into this setup** via the `session_start.py` hook and the `settings.local.json` output style configuration:

```json
{
  "outputStyle": "Explanatory"
}
```

You do **not** need to install the explanatory-output-style plugin separately.

---

## Recommended Optional Plugins

### typescript-lsp

Provides TypeScript and JavaScript language server integration for code intelligence features (go-to-definition, error checking, hover information, auto-completion context).

**Install the required global dependency:**

```bash
npm install -g typescript-language-server typescript
```

**When to use:** Recommended for projects with complex TypeScript types or large codebases where real-time type checking supplements the regex-based TypeScript validator included in this setup.

### pyright-lsp

Provides Python language server integration via Pyright for Python code intelligence.

**Install the required global dependency (pick one):**

```bash
npm install -g pyright
```

or

```bash
pip install pyright
```

**When to use:** Useful if you are modifying the Python hook scripts in `.claude/hooks/` and want type checking and diagnostics for the hook code itself.

---

## Enabling and Disabling Plugins

Plugins are managed through Claude Code's plugin system. After installing the required global dependencies, plugins can be enabled or disabled in your Claude Code settings. Refer to the [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code) for current instructions on plugin management.

---

## Summary

| Plugin | Status | Notes |
|--------|--------|-------|
| explanatory-output-style | **Built-in** | Already provided by `session_start.py` + `settings.local.json` |
| typescript-lsp | Optional | Requires `npm install -g typescript-language-server typescript` |
| pyright-lsp | Optional | Requires `npm install -g pyright` or `pip install pyright` |

For the main setup documentation, see [README.md](README.md).
