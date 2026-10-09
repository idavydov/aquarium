# Cloudflare Pages

The Pages build preserves the existing extensionless URLs, Cyrillic filenames,
canonical domain and sitemap. Chord pages are stored as `.html` files; Pages
serves them through their extensionless routes.

## Local build

```bash
python3 -m pip install -r requirements.txt
python3 bin/build.py
python3 bin/check_pages.py
```

The build replaces the generated `public/` directory. The existing SSH publish
script still generates extensionless files for the previous server.

## Random review route

`/r?r=r` serves a newly selected song on every request without redirecting.
`/r` without the switch returns 404. The route is unlinked and omitted from
robots.txt and the sitemap. Responses use `no-store` and `X-Robots-Tag: noindex,
nofollow`; song HTML, canonical URLs and ordinary static routes stay intact.

The build bundles `bin/random_worker.mjs` with the generated song paths into
Pages advanced mode's `public/_worker.js`. `_routes.json` invokes it only on
`/r`. The Python preview server supports the same route, including `--no-js`.

Validate the handler after building with `node --test bin/test_random_worker.mjs`.

## Pages settings

Create a Pages project connected to this GitHub repository:

| Setting | Value |
| --- | --- |
| Framework preset | None |
| Production branch | `main` |
| Build command | `python3 -m pip install -r requirements.txt && python3 bin/build.py` |
| Build output directory | `public` |
| Root directory | Repository root (leave blank) |

Use the current Pages build image with Python 3. The explicit pip step installs
the dependency even when automatic dependency installation is disabled.

## Validate before moving DNS

Build the same revision locally, then check the temporary Pages address:

```bash
python3 bin/check_pages.py https://YOUR-PROJECT.pages.dev
```

This checks every sitemap URL against its expected title and canonical link,
including percent-encoded Cyrillic and punctuation. It also checks robots.txt,
sitemap.xml, representative static assets and a missing URL's 404 status.

After these checks pass, add `aquarium.rifma.ch` in the Pages project's Custom
domains section and follow Cloudflare's DNS instructions. Keep canonical and
sitemap URLs on `https://aquarium.rifma.ch/`. Run the checker again against that
domain after the switch. Keep the old host available during the transition.

The production `pages.dev` address should redirect to the custom domain once
the migration is complete, to avoid publishing two indexable copies of the site.

References:

- https://developers.cloudflare.com/pages/get-started/git-integration/
- https://developers.cloudflare.com/pages/configuration/serving-pages/
- https://developers.cloudflare.com/pages/configuration/custom-domains/
- https://developers.cloudflare.com/pages/how-to/redirect-to-custom-domain/
