# twenty-custom

Build recipe for the AL ARAIMI / CRMALARAMI self-hosted Twenty CRM image.

It takes the official Twenty **v2.22.0** source, injects our UI customizations, and
publishes the result to `ghcr.io/krispx2811/twenty-custom`. Railway pulls that image
instead of the stock `twentycrm/twenty`.

This repo contains **no secrets and no data** - only the build workflow and the UI
overlay. The CRM database, env vars, and tokens live in Railway.

## What gets customized

`crm-custom/print-invoice.inject.html` is appended to Twenty's `index.html` at build
time. It adds:

- A **Print PDF** button on invoice pages that renders a branded A4 invoice.
- The **Omani Rial** symbol in place of Twenty's generic coins icon.

Auth uses the logged-in user's own session token (read from `localStorage`), so no
API key is baked into the page.

## Rebuilding

- Edit `crm-custom/print-invoice.inject.html` and push to `main`, or
- Actions -> "Build custom CRM image" -> Run workflow (optionally change the Twenty tag).

Then in Railway, redeploy the Twenty + Worker services to pull the new image.

## Upgrading Twenty later

Run the workflow with a newer `twenty_ref` tag. Deploy to a copy of the data first and
verify migrations before pointing production at it.
