# 1. Your first server and app

**Goal:** a running Cloudways server with one app, reachable over SSH and SFTP.

## Concepts in 60 seconds

- **Server**: a VM on a cloud provider (DigitalOcean, Vultr, Linode, AWS, or Google Cloud) that Cloudways provisions and manages.
- **Application**: a site or app on a server (WordPress, WooCommerce, Laravel, Magento, PHP, and others). One server can host many apps.
- **Project**: an optional grouping of servers and apps.
- **Credentials**: *master* credentials reach every app on the server; *application* credentials reach one app.

## Step 1: Start the free trial

Cloudways offers a **3-day Flexible trial with no credit card**. To keep your server afterward you must add a card (a small temporary verification charge, reversed automatically, may appear).

**Hackathon paths:** sign up only via [unified.cloudways.com/signup?coupon=CWFEST20](https://unified.cloudways.com/signup?coupon=CWFEST20) (promo `CWFEST20`). Without a card you can trial Flexible/Autonomous on a 2 GB or 4 GB server, or Velocity Starter (2 GB). Add a card if you want the **$20 credits**. All winners get a **Velocity Starter pack for 3 months**.

1. Sign up at [unified.cloudways.com/signup?coupon=CWFEST20](https://unified.cloudways.com/signup?coupon=CWFEST20) and log in.
2. In the left menu choose **Cloudways Flexible**, then **Get Started**, then **3-days free trial**.
3. Pick your app, server, and project names.
4. Choose a provider, server size (2 GB or 4 GB for the no-card trial), and location.
5. Click **Launch Now**.

> **Hackathon tip:** DigitalOcean at 2 GB is a solid default for the no-card trial. Pick the region closest to your judges or users.

Provisioning takes a few minutes. The dashboard shows progress.

## Step 2: Find your credentials

Menu labels shift over time, so look for the equivalents if yours differ. Open **Servers → your server → Master Credentials** for the public IP, master username, and password. For a single app, open **Applications → your app → Access Details**.

## Step 3: Enable SSH for the app

SSH is **not enabled by default** for application users. Open the app's **Application Settings** and toggle **Enable SSH Access**. Master credentials work without this.

## Step 4: Connect

```bash
ssh <username>@<server-ip>
```

For SFTP use the same host, user, and password with any client (`sftp`, Cyberduck, FileZilla).

**Prefer keys:** add your public key under the server's SSH key settings so you can skip passwords. (You can also do this by API or MCP; see tutorials 3 and 4.)

## Step 5: Look around

```bash
cd ~/applications        # one folder per app, named by an internal ID
ls
cd <app-folder>/public_html
```

`public_html` is the web root. Edit a file, refresh the app URL, and you've confirmed the full loop.

## Checkpoint

- [ ] Server shows **Running**
- [ ] You can SSH or SFTP in
- [ ] You know your server ID and app ID (visible in the dashboard URL and in `scripts/list_servers.py` output)

**Next:** [Deploy apps →](../02-deploy-apps/README.md)

## References

- [Flexible trial guide](https://support.cloudways.com/en/articles/10061830-how-to-subscribe-flexible-trial)
