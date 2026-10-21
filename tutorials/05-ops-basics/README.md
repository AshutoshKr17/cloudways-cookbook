# 5. Ops basics

**Goal:** make your app production-shaped: your own domain, HTTPS, backups, a staging copy, visibility, and room to scale.

Menu names shift as the dashboard evolves; use search in the [Help Center](https://support.cloudways.com) if something has moved.

## Domains

1. In the app's **Domain Management**, set your **primary domain**.
2. At your DNS provider, point the domain at the server's public IP (an `A` record), or use the app URL via a `CNAME` for subdomains.
3. Wait for DNS to propagate. Extra domains go in as **aliases**.

API/MCP equivalents: `app_cname_update`, `app_aliases_update`. Cloudways also offers **DNS Made Easy** as an add-on.

## SSL

In **SSL Certificate**, install a Let's Encrypt certificate for your domain (it must already resolve to the server). Then enable **Force HTTPS** (`app_enforce_https_update`).

## Backups

- Open **Backups** on the server for automatic backup settings (frequency, retention, local vs. off-server).
- Take an **on-demand backup** before every deploy: `scripts/app_backup.py`, or MCP "Back up app 67890 on server 12345".
- Practice a **restore** once, on a test app. A backup you have never restored is a hope, not a backup.

## Staging

Clone your app to a staging copy (**Staging Management** or `app_clone`), test there, then push changes back. Protect staging with **password protection** (HTTP basic auth) so search engines and strangers stay out.

## Monitoring

- **Monitoring** graphs on each server: CPU, memory, disk, and more.
- App-level analytics for traffic, slow PHP pages, and slow MySQL queries.
- **CloudwaysBot** sends alerts to Slack, email, and other channels.
- **Copilot** provides AI-assisted troubleshooting suggestions (a paid add-on; check current pricing).

## Scaling

- **Vertical scaling**: resize the server's CPU/RAM in **Server Management → Vertical Scaling** (brief downtime is possible). Disk scaling support varies by provider.
- **Caching**: Varnish, Redis/Memcached and object cache can dramatically cut load; use *Purge Cache* after deploys.
- **CDN**: the **Cloudflare Enterprise CDN** add-on can offload static assets and add security.

## Security quick wins

- Turn **SSH off** for apps that don't need it.
- Use **application credentials** instead of master credentials for deploy bots.
- Disable **XML-RPC** on WordPress sites that don't need it.
- Rotate passwords and revoke tokens after the hackathon.

## Clean up

When you're done, delete servers you won't keep (**Server → Delete Server**, or `server_delete`). Deletion is permanent.

## Pre-demo checklist

- [ ] Domain resolves, HTTPS valid, Force HTTPS on
- [ ] A fresh backup exists
- [ ] Staging password-protected
- [ ] Monitoring tab open on a second screen
- [ ] You know how to roll back (restore, or `git pull` a known-good branch)
