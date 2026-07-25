# twenty-custom

Builds and deploys the **AL ARAIMI / CRMALARAMI** self-hosted Twenty CRM image.

It takes the official Twenty **v2.22.0** source, injects our UI customizations (a **Print PDF**
button on invoices + the **Omani Rial** icon), and publishes the result to
`ghcr.io/krispx2811/twenty-custom`. Railway pulls that image instead of the stock
`twentycrm/twenty`.

This repo contains **no secrets and no data** - only the build recipe and the UI overlay. The CRM
database, env vars, and tokens live in Railway.

---

## Architecture (how the pieces fit)

```
 twentyhq/twenty @ twenty/v2.22.0  (official source, pulled fresh in CI)
              +
 crm-custom/print-invoice.inject.html   (our Print PDF button + Rial icon)
              |
       GitHub Actions build  (this repo, free public Actions)
              |
   ghcr.io/krispx2811/twenty-custom:2.22.0   (public image in GHCR)
              |
        Railway pulls the image
              |
   Twenty service + Twenty Worker service   (the live CRM)
```

Everything else the CRM has - the 23 objects, 543 fields, dashboard, roles, Audit Log, VAT, OMR
currency, kanban boards, sidebar folders - is **data in the Postgres database**, not part of this
image. It was built via Twenty's metadata API (see the `build-scripts/` in the CRMALARAMI repo) and
restored from a DB dump. This image only adds the two things that must live in the frontend source.

---

## Key facts (things that bite you if forgotten)

- **Twenty release tags are prefixed**: the tag is `twenty/v2.22.0`, NOT `v2.22.0`.
- **The image must match the DB version.** The live data is v2.22.0, so we build v2.22.0. Building a
  newer version forces a database migration on first boot - only do that deliberately, on a backup.
- **The GHCR package must be public** for Railway to pull it without credentials
  (`https://github.com/users/krispx2811/packages/container/twenty-custom/settings` -> make Public).
- **Print auth uses the logged-in user's session token** (read from `localStorage['tokenPairState']`),
  so no API key is baked into the page.
- **Railway does not auto-update.** It only pulls the image when you redeploy.

---

## Railway service reference

| Thing | Value |
|---|---|
| Project | `5d849c6a-0d98-4d77-8c37-fc56be37d2bf` (Production) |
| Environment | `7662b4a3-cc57-4510-8f46-0924af9d4a12` |
| Twenty service | `30cc3ce4-a586-4364-9f11-04069c10b635` |
| Twenty Worker service | `7931605c-5189-451c-889c-644b07070c8c` |
| Custom image | `ghcr.io/krispx2811/twenty-custom:2.22.0` |
| Rollback image | `twentycrm/twenty:v2.22.0` |
| CRM URL | https://twenty-production-4200.up.railway.app |

---

## Making a new update (the common case: change a UI customization)

1. **Edit the customization** - `crm-custom/print-invoice.inject.html` (company details, invoice
   layout, the button, the Rial icon). To add a *new* overlay, drop another file in `crm-custom/`
   and add an inject step for it in `.github/workflows/build-custom-crm.yaml`.

2. **Push to `main`** - this triggers the build automatically:
   ```bash
   git add crm-custom/
   git commit -m "invoice: <what changed>"
   git push origin main
   ```
   Watch it in the repo's **Actions** tab (or `gh run watch`). Takes ~15-25 min. It republishes
   `ghcr.io/krispx2811/twenty-custom:2.22.0` (and a unique `:2.22.0-<run number>`).

3. **Redeploy Railway** so it pulls the new image. Two ways:
   - **Script (fastest):** see "Deploy / redeploy" below.
   - **Railway UI:** open the **Twenty** service -> Deployments -> **Redeploy**. Repeat for
     **Twenty Worker**.

4. **Verify** - open the CRM, hard-refresh (Cmd+Shift+R), confirm the change.

---

## Deploy / redeploy (script)

`deploy/railway-set-image.py` points both services at an image tag and redeploys them.

```bash
export RAILWAY_TOKEN=<a Railway Project-Access-Token>   # Railway -> project Settings -> Tokens

# Redeploy the current custom image (after a new build):
python3 deploy/railway-set-image.py ghcr.io/krispx2811/twenty-custom:2.22.0

# Roll back to stock:
python3 deploy/railway-set-image.py twentycrm/twenty:v2.22.0
```

The token is read from the environment and never committed.

---

## Upgrading Twenty to a newer version (deliberate, do on a backup)

1. **Back up the database first** (Railway -> Postgres -> Backups).
2. In `.github/workflows/build-custom-crm.yaml`, bump the `TWENTY_REF` default and the image `tags:`
   to the new version (e.g. `twenty/v2.23.0` and `:2.23.0`).
3. Push -> a new image builds.
4. Point Railway at the new tag with the deploy script. On first boot Twenty **auto-migrates the
   database** to the new version - watch the deploy logs. If it fails, roll back to
   `twentycrm/twenty:v2.22.0` (or your last good custom tag) immediately.

---

## Rollback

```bash
export RAILWAY_TOKEN=<token>
python3 deploy/railway-set-image.py twentycrm/twenty:v2.22.0
```

Or in the Railway UI: Twenty + Twenty Worker services -> Settings -> Source -> Image ->
`twentycrm/twenty:v2.22.0` -> Deploy.

---

## What was done to set this up (one-time, for reference)

1. Created this **public** repo (public so GitHub Actions run free; the private CRMALARAMI fork's
   Actions were billing-blocked).
2. Added `crm-custom/print-invoice.inject.html` - the Print PDF + Rial script, reworked to read the
   user's session token instead of a hardcoded API key.
3. Added `.github/workflows/build-custom-crm.yaml` - checks out `twentyhq/twenty@twenty/v2.22.0`,
   injects the overlay into `packages/twenty-front/index.html`, builds with Twenty's stock Dockerfile
   (target `twenty`), pushes to GHCR.
4. Made the GHCR package **public**.
5. Pointed Railway's **Twenty** and **Twenty Worker** services at
   `ghcr.io/krispx2811/twenty-custom:2.22.0` and redeployed. They booted on the existing v2.22.0 data
   with no migration.
