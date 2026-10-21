# 2. Deploy apps

**Goal:** get real code running on your server three ways: a one-click app, a Git deployment, and a PHP/Laravel app.

## A. One-click apps (WordPress and friends)

When you launch a server (or later, **Add Application** on an existing server), choose an application type. Cloudways installs and configures it. Supported types include WordPress, WooCommerce, Laravel, Magento, and PHP, among others.

After install, the app has a default Cloudways URL. Use it right away; add your own domain in [tutorial 5](../05-ops-basics/README.md).

## B. Git deployment

Cloudways can pull code from your repo into an app. Know these up front:

- The repo must be reachable **over SSH** (HTTPS URLs are not supported).
- You add a Cloudways-generated **deploy key** to your repo host.
- The keys generated in the Cloudways UI work for **console deployments only**. To run `git` yourself on the server (push, checkout, etc.) you need **master credentials** and your own key pair.

**Manual deploys (console)**

1. Open **Applications → your app → Deployment via Git**.
2. Click **Generate SSH Key** and copy the public key.
3. In GitHub: repo **Settings → Deploy keys → Add deploy key**, paste, save. (GitLab and Bitbucket have equivalents.)
4. Back in Cloudways, enter the SSH repo address (`git@github.com:you/repo.git`), then **Get Branches**.
5. Choose a branch and deploy path (empty means `public_html`), then **Start Deployment**.
6. For later updates, click **Pull**.

**Auto-deploy on push**

Cloudways documents this as a small webhook script *you* host, which calls the Git API. Prerequisites: you are the primary account owner, the app is on a Flexible server, and manual Git deployment already works. In short:

1. Create an Access Token with **Limited Access**, only the Git pull operation.
2. Put the token, server ID, app ID, SSH Git URL, and branch in a config file **outside** `public_html`, and keep it out of Git.
3. Add a small PHP endpoint that accepts **POST only**, checks a long random webhook secret, and calls the Git pull API.
4. Add the endpoint URL as a push webhook in GitHub or Bitbucket.

Cloudways' [step-by-step webhook guide](https://support.cloudways.com/en/articles/5124785-automatically-deploy-from-git-to-server-using-webhooks) includes the full hardened script. Its sample code still shows the v1 base URL; use v2 (see tutorial 3).

You can also trigger a pull from your own CI with [`scripts/git_deploy.py`](../../scripts/git_deploy.py). The pull call takes the server ID, app ID, SSH Git URL, and branch name (deploy path optional).

## C. A Laravel or custom PHP app

1. Create a **Laravel** (or **PHP**) application.
2. Deploy your code with Git as above, or upload via SFTP.
3. Laravel serves from `public/`. Point the app's **webroot** at it (Application Settings → webroot, or the `app_webroot_update` MCP tool): `/public_html/public`.
4. SSH in and run your build steps:

```bash
cd ~/applications/<app-folder>/public_html
composer install --no-dev
cp .env.example .env && php artisan key:generate
php artisan migrate --force
```

Get the database host, name, user, and password from **Application → Access Details**.

## D. Node.js with Cloudways Velocity (public preview)

**Cloudways Velocity** is managed Node.js hosting, currently labelled **Public Preview**. Per the [Velocity page](https://www.cloudways.com/en/velocity.php) (checked Oct 21, 2026):

- Connect a GitHub, GitLab, or Bitbucket repo; Velocity detects the framework and sets build and start commands.
- Presets for Next.js, Remix, React, Astro, Nuxt, Svelte, Vite, Express, Fastify, Angular, and n8n. Node.js LTS 22.x and 24.x, selectable per app.
- PostgreSQL can be provisioned from the dashboard.
- Flat monthly plans on persistent servers (no cold starts), starting at $20/month; Starter and Professional include a 3-day free trial.

Pricing and features change during previews, so confirm on the page. Starter templates live at [github.com/CloudwaysbyDO](https://github.com/CloudwaysbyDO/). Velocity is separate from the Flexible (PHP-centric) servers used in the other sections.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Git "permission denied" | Deploy key not added to the repo, or you used an HTTPS URL |
| `git` works in the console but not over SSH | UI-generated keys only work for console deploys; use master credentials and your own key |
| 403 / blank page on Laravel | Webroot not set to `public` |
| `ssh: permission denied` for an app user | SSH not enabled in Application Settings |
| Files owned by wrong user after manual edits | Use **Reset File Permissions** |

**Next:** [API and automation →](../03-api-and-automation/README.md)

## References

- [Git deployment help article](https://support.cloudways.com/using-git-for-deployment/)
- [Using Git via the command line](https://support.cloudways.com/en/articles/5124793-using-git-via-command-line)
- [Auto-deploy with webhooks](https://support.cloudways.com/en/articles/5124785-automatically-deploy-from-git-to-server-using-webhooks)
- [Cloudways Velocity](https://www.cloudways.com/en/velocity.php)
