# 2. Deploy apps

**Goal:** get real code running on your server three ways: a one-click app, a Git deployment, and a PHP/Laravel app.

## A. One-click apps (WordPress and friends)

When you launch a server (or later, **Add Application** on an existing server), choose an application type. Cloudways installs and configures it. Supported types include WordPress, WooCommerce, Laravel, Magento, and PHP, among others.

After install, the app has a default Cloudways URL. Use it right away; add your own domain in [tutorial 5](../05-ops-basics/README.md).

## B. Git deployment

Cloudways can pull code from your repo into an app. Requirements to know up front:

- The repo must be reachable **over SSH** (HTTPS URLs are not supported).
- You add a Cloudways-generated **deploy key** to your repo host.

**Steps**

1. Open **Applications → your app → Deployment via Git**.
2. Click **Generate SSH Key** and copy the public key.
3. In GitHub: repo **Settings → Deploy keys → Add deploy key**, paste, save. (GitLab and Bitbucket have equivalents.)
4. Back in Cloudways, enter the SSH repo address (`git@github.com:you/repo.git`), then **Get Branches**.
5. Choose a branch and deploy path, then **Start Deployment**.
6. For later updates, click **Pull**, or add the webhook Cloudways shows to auto-deploy on push (GitHub, GitLab, and Bitbucket are supported).

You can do the same through the API: see [`scripts/git_deploy.py`](../../scripts/git_deploy.py).

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

## D. Node.js

Cloudways has announced **Cloudways Velocity**, managed Node.js hosting for apps deployed from GitHub, and publishes Node.js starter templates at [github.com/CloudwaysbyDO](https://github.com/CloudwaysbyDO/). Availability may be limited (early access was advertised), so **check the [Velocity page](https://www.cloudways.com/en/velocity.php)** before planning a hackathon around it. If Velocity isn't open to you, a PHP-centric Flexible server is the supported path today.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Git "permission denied" | Deploy key not added to the repo, or you used an HTTPS URL |
| 403 / blank page on Laravel | Webroot not set to `public` |
| `ssh: permission denied` for an app user | SSH not enabled in Application Settings |
| Files owned by wrong user after manual edits | Use **Reset File Permissions** |

**Next:** [API and automation →](../03-api-and-automation/README.md)

## References

- [Git deployment help article](https://support.cloudways.com/using-git-for-deployment/)
