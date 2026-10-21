# 4. MCP and AI agents

**Goal:** manage Cloudways in plain English from an AI client such as Claude, Cursor, or VS Code.

The Cloudways **MCP server** exposes 240+ tools (servers, apps, backups, Git, DNS, monitoring, security, and more) to any [Model Context Protocol](https://modelcontextprotocol.io) client. To keep your context window small, a client initially sees 65 tools; the rest are reached through three meta-tools: `list_available_toolsets`, `get_toolset_tools`, and `execute_tool`.

## Prerequisites

- A Cloudways **Access Token** ([tutorial 3](../03-api-and-automation/README.md)). For safety, create a **Read-Only** token first.
- Node.js for clients that connect through `mcp-remote`. The setup article asks for **v24.14.1+**, though its troubleshooting table says v18+; use a current LTS to be safe.
- An MCP client.

## Endpoint and headers

- URL: `https://mcp.cloudways.com/mcp/` (the trailing slash matters)
- Required headers:

| Header | Value |
|---|---|
| `X-Access-Token` | your token |
| `X-Mcp-Host` | your client: `cursor`, `claude-desktop`, `claude-code`, `vs-code`, `gemini-cli`, `codex`, `codex-cli`, or `Devin` |

> The older `X-CW-Email` / `X-CW-Api-Key` headers (still mentioned in parts of the FAQ) belong to the retired API key flow.

## Client configs

### Claude Code

```bash
claude mcp add --transport http \
  --header "X-Access-Token: <your-token>" \
  --header "X-Mcp-Host: claude-code" \
  -s user \
  cloudways https://mcp.cloudways.com/mcp/
claude mcp list
```

### Claude Desktop

Config file on macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`. Uses the `mcp-remote` bridge. No spaces after the colon in `--header` values:

```json
{
  "mcpServers": {
    "cloudways": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://mcp.cloudways.com/mcp/",
        "--header", "X-Access-Token:<your-token>",
        "--header", "X-Mcp-Host:claude-desktop"
      ]
    }
  }
}
```

Fully quit and reopen Claude Desktop afterward.

### Cursor

Config file: `~/.cursor/mcp.json`

```json
{
  "mcpServers": {
    "cloudways": {
      "url": "https://mcp.cloudways.com/mcp/",
      "headers": {
        "X-Access-Token": "<your-token>",
        "X-Mcp-Host": "cursor"
      }
    }
  }
}
```

### VS Code

Note `servers` (not `mcpServers`) and `type: http`:

```json
{
  "servers": {
    "cloudways": {
      "type": "http",
      "url": "https://mcp.cloudways.com/mcp/",
      "headers": {
        "X-Access-Token": "<your-token>",
        "X-Mcp-Host": "vs-code"
      }
    }
  },
  "inputs": []
}
```

### Gemini CLI and Codex

Gemini CLI uses `httpUrl`; Codex uses TOML (`[mcp_servers.cloudways]` with `http_headers`). See the [official setup article](https://support.cloudways.com/en/articles/14654372-how-to-use-cloudways-mcp-server-for-ai-based-server-management) for those.

## Verify

Prompt: `Show me all my servers`. You should see names, providers, regions, and IPs.

## Prompts to try (read-only first)

| Intent | Prompt |
|---|---|
| Inventory | "Show me all my running servers." |
| Health | "Are all services healthy on server 12345?" |
| Performance | "Show CPU usage for server 12345 over the last 24 hours." |
| Slow code | "Which PHP pages are slowest on app 67890?" |

**Then, with a Full or Limited token:**

| Intent | Prompt |
|---|---|
| Provision | "Create a 2GB DigitalOcean server in NYC with WordPress." |
| Safe deploys | "Back up app 67890 on server 12345, then pull the latest from main." |
| Staging | "Clone app 67890 on server 12345 as 'Staging Copy'." |

## Guardrails (read this)

- MCP can run **destructive, irreversible actions** such as deleting servers and apps. Include IDs in prompts; ambiguous prompts can resolve to the wrong target.
- Prefer scoped tokens. Passwords for SSH/SFTP are **hidden from MCP results by default**; the per-token **Reveal Credentials** toggle turns that on. Leave it off unless you need it.
- There is no per-user access control at the MCP layer; don't share a token across people.
- If the agent says new tools don't exist, your client cached an old tool list: fully quit (not just close) and reopen, or toggle the server off and on.

**Next:** [Ops basics →](../05-ops-basics/README.md)

## References

- [MCP server setup](https://support.cloudways.com/en/articles/14654372-how-to-use-cloudways-mcp-server-for-ai-based-server-management)
- [Full MCP tool list](https://support.cloudways.com/en/articles/15798823-cloudways-mcp-server-tools)
- [MCP 2.0 announcement](https://www.cloudways.com/blog/cloudways-mcp-2-0_logs-wordpress-management/)
