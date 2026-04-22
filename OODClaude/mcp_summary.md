# Top 10 MCP Servers — Summary

Source: https://dev.to/fallon_jimmy/top-10-mcp-servers-for-2025-yes-githubs-included-15jg

---

## 1. GitHub MCP Server
- Manages repos, branches, commits, PRs, issues, and code scanning via AI
- Requires: Docker + GitHub Personal Access Token
- Setup:
  ```bash
  git clone https://github.com/github/github-mcp-server.git
  docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN=<token> ghcr.io/github/github-mcp-server
  ```

## 2. Apidog MCP Server
- Connects AI assistants directly to your API documentation
- Syncs OpenAPI specs and supports natural language API queries
- Setup: Add server credentials in Cursor Settings → MCP section

## 3. Brave Search MCP Server
- Privacy-focused web search for AI systems
- Free tier: 2,000 queries/month; supports `brave_web_search` and `brave_local_search`
- Requires: Brave Search API key
- Transports: stdio and SSE

## 4. Slack MCP Server
- Integrates AI into team communication workflows
- Requires: Bot OAuth Token with `chat:write`, `files:write` permissions
- Transports: SSE, HTTP, stdio

## 5. Cloudflare MCP Server
- Edge infrastructure deployment and management
- Features: DNS management, WAF rules, cache control, zone administration
- Setup: `wrangler deploy` + configure OAuth authentication

## 6. File System MCP Server
- Local file access and manipulation for AI systems
- Supports: read, create, update, search, delete files/directories
- Setup: Configure allowed directories in `claude_desktop_config.json`
- Security: Path validation + gitignore-style exclusion patterns

## 7. Vector Search MCP Server (Qdrant)
- Semantic search using embeddings
- Use `qdrant-find` for natural language similarity queries
- Setup: Set env vars `QDRANT_URL`, `QDRANT_API_KEY`, `COLLECTION_NAME`

## 8. Docker MCP Server
- Secure sandboxed code execution within containers
- Supports: Python (pip), Node.js (npm), Debian/Alpine packages
- Capabilities: container listing, creation, script execution, cleanup

## 9. Cursor MCP Integration
- IDE enhancement connecting Cursor to any MCP server
- Setup: Settings → Cursor Settings → MCP Servers → Add New
- Pass credentials via env vars: `env BRAVE_API_KEY=<key> <command>`
- Windows fix: prefix command with `cmd /c` if you get "Client Closed" error
- Transports: stdio or SSE

## 10. DeepWiki MCP Server
- Reads and searches documentation from any public GitHub repo
- No auth required, completely free
- Setup:
  ```bash
  claude mcp add --transport http --scope user deepwiki https://mcp.deepwiki.com/mcp
  ```
- Tools: `read_wiki_structure`, `read_wiki_contents`, `ask_question`
