# cfast landing page

A responsive, static product page for the cfast CLI. It has no build step,
framework, package installation, analytics, or backend. The CLI is independent
of this directory.

## Preview

From the repository root:

```bash
python3 -m http.server 4173 --bind 127.0.0.1 --directory website/dist
```

Open `http://127.0.0.1:4173/`. Serve over HTTPS when publishing so the copy
buttons can use the Clipboard API. On an unsupported browser, they select the
commands and explain how to copy manually.

## Files

- `dist/index.html`: product page and real installation instructions.
- `dist/styles.css`: responsive layout, typography, and reduced motion styles.
- `dist/app.js`: example verdicts, command tabs, copy controls, mobile navigation,
  and IntersectionObserver reveals.
- `dist/privacy.html`, `dist/terms.html`: factual privacy and usage notes.
- `dist/404.html`: custom missing page.
- `dist/assets/`: self-hosted Geist fonts, their OFL licenses, favicon, and social
  preview image.
- `CONTENT.md`: extracted product facts and page strategy.
- `.openai/hosting.json`: private Sites hosting configuration.

## Hosting

### Vercel

The repository root contains `vercel.json`. It serves `website/dist/` as a
static site, with no install or build command. No Python server or Node.js
application is deployed. `.vercelignore` limits CLI uploads to the static page
and deployment configuration.

For a new Vercel import, choose the `dhruvkshah75/cfast` GitHub repository,
keep **Root Directory** at the repository root, and use the **Other** framework
preset. The output directory is `website/dist`; leave install and build commands
empty. Connecting GitHub lets Vercel deploy future pushes to `main`.

To deploy with the official CLI from the repository root after signing in:

```bash
npx vercel link
npx vercel project inspect --non-interactive
npx vercel --prod
```

Confirm the linked owner and project before deploying. Local `.vercel/` state
and environment files are ignored by Git. Vercel serves `404.html` for missing
pages automatically.

### Other static hosts

Publish `website/dist/` with any static host. Configure its custom 404 document
as `404.html` where supported. No client-side router or catch-all fallback is
needed. Before moving domains, update the canonical URL, social metadata,
`robots.txt`, and `sitemap.xml` to the production origin. The current Sites
preview is private; public access is a separate hosting setting.

## Content assumptions

- Audience: C++ competitive programmers using Linux and a local editor.
- Primary action: install the existing CLI. There is no signup or mailing list.
- The repository README and implementation define product behavior.
- Terminal timings are explicitly illustrative, not benchmark claims. Demo
  controls do not compile, execute, or upload code in the browser.
- No license, testimonials, user counts, pricing, or exact online judge parity
  is asserted. The source repository does not currently contain a license.
- Installation commands use the documented `~/dev/cfast` path. An existing
  checkout at that path should be updated instead of cloning over it.
- The site itself uses no cookies, analytics, third party fonts, or tracking.
  Hosting providers and outbound links have their own policies.

## Verification

The local development suite is intentionally ignored by Git, following this
repository's policy:

```bash
python3 -m unittest discover -s tests -v
node --check website/dist/app.js
```

Also check the page at desktop, tablet, 390px, and 320px widths; use the verdict
and command tabs, copy buttons, FAQ disclosures, and mobile menu with a keyboard.
Enable reduced motion and confirm the content remains visible.
