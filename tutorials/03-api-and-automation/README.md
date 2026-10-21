# 3. API and automation

**Goal:** authenticate with an Access Token and script your Cloudways account.

## The 2026 auth model

- **Legacy email + API key (`/oauth/access_token`)**: scheduled end of life October 15, 2026 (passed); keys are revoked afterward. Cloudways says not to build new integrations on it.
- **Access Tokens**: create many, each with a name, expiry, and scope. Send as `Authorization: Bearer <token>`.
- **API v2** is current; v1 is sunset. Cloudways' migration note: replace `v1` with `v2` in URL paths.
- **Rate limit:** 100 requests per minute (per Cloudways' API article).
- Only the **primary account owner** can create tokens.

## Step 1: Create a token

1. Log in at [unified.cloudways.com](https://unified.cloudways.com).
2. Top-right profile menu → **API Integration** → **Create Access Token**.
3. Name it (e.g. `hackathon-dev`), pick a short expiry (**1 day** is plenty for a hackathon), and choose a scope:
   - **Read-Only**: GET calls only. Start here.
   - **Limited Access** (beta): pick endpoint groups (Server, Application, Git, Lists, Monitoring, ...).
   - **Full Access**: everything. Avoid unless needed.
4. Copy the token immediately. **It's shown once** and can't be recovered.

```bash
export CLOUDWAYS_TOKEN="<paste here>"   # never commit this
```

## Step 2: Try the Playground

Open the [API Playground](https://developers.cloudways.com/play), click **Authorize**, choose the **Access Token** tab, paste your token. Run `GET /server` (list servers). The Playground shows request and response shapes for every endpoint. It acts on your **real account**, so test on a throwaway server.

## Step 3: Call it from code

Base URL (confirmed by Cloudways' MCP 2.0 announcement, which lists `https://api.cloudways.com/api/v2/providers`):

```
https://api.cloudways.com/api/v2
```

Override with `CLOUDWAYS_API_BASE` if it ever changes. Note: some help articles (e.g. the Git webhook guide) still show `/api/v1` in sample code; that's stale.

```bash
curl -s -H "Authorization: Bearer $CLOUDWAYS_TOKEN" \
  https://api.cloudways.com/api/v2/server | head -c 600

# reference data (providers, regions, sizes) lives under the Lists endpoints:
curl -s -H "Authorization: Bearer $CLOUDWAYS_TOKEN" \
  https://api.cloudways.com/api/v2/providers | head -c 600
```

Or use the helper scripts (standard library only, Python 3.8+):

| Script | What it does |
|---|---|
| [`scripts/cw.py`](../../scripts/cw.py) | Tiny client: auth, errors, and operation polling |
| [`scripts/list_servers.py`](../../scripts/list_servers.py) | List servers and their apps (read-only) |
| [`scripts/create_server.py`](../../scripts/create_server.py) | Launch a server. **Dry run by default**; needs `--yes` to spend money |
| [`scripts/git_deploy.py`](../../scripts/git_deploy.py) | Clone or pull a Git repo into an app |
| [`scripts/app_backup.py`](../../scripts/app_backup.py) | Back up an app before you deploy |

```bash
python3 scripts/list_servers.py
python3 scripts/create_server.py --provider do --region nyc3 --size 1GB --app wordpress
python3 scripts/git_deploy.py pull --server 123 --app 456 --url git@github.com:me/repo.git --branch main
```

## Things to know

- **Creation is asynchronous.** `POST /server` returns an operation ID; poll the operation endpoint until it completes. `cw.wait_for_operation()` does this.
- **Provider matters.** Valid regions, sizes, and options differ per provider; wrong combinations return `422`. Discover valid values from the **Lists** endpoints (providers, regions, sizes, apps) rather than guessing.
- **Request bodies for `POST /server` and backups are marked (verify).** Check each against the Playground's request schema. The Git pull body (`server_id`, `app_id`, `git_url`, `branch_name`, optional `deploy_path`) matches Cloudways' current webhook guide. That guide sends **form-encoded** bodies, and `cw.py` does the same.
- **API groups** in the docs: Lists, Server, Server Management, Service, Application, Authentication, Projects, Git, CloudwaysBot, App Management, Security, Operation.

## Ideas to build

- Spin up a per-PR preview app, clone from production, post the URL to Slack, delete on merge.
- A cron that backs up apps and ships a summary to Discord.
- A dashboard pulling monitoring graphs for all servers.

**Next:** [MCP and AI agents →](../04-mcp-ai-agents/README.md) or open the [notebook](../../notebooks/cloudways_api_quickstart.ipynb).

## References

- [Access Tokens help article](https://support.cloudways.com/en/articles/5136065-how-to-create-and-manage-cloudways-api-access-tokens)
- [API v2 announcement](https://www.cloudways.com/blog/introducing-cloudways-api-v2/)
- [API docs](https://developers.cloudways.com/docs)
- [Git webhook guide (shows Git pull API usage)](https://support.cloudways.com/en/articles/5124785-automatically-deploy-from-git-to-server-using-webhooks)
