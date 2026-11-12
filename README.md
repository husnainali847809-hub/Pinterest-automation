# Pinterest Article Publisher

Publishes 4 original articles and 4 Pinterest Pins daily, split evenly between SmartTools Hub and TemplivoX.

## Pakistan-time schedule
- 08:00 — SmartTools Hub
- 12:00 — TemplivoX
- 16:00 — SmartTools Hub
- 20:00 — TemplivoX

GitHub scheduled workflows may start a little later than cron time.

## Each run
1. Gemini writes one original evergreen article.
2. The article is added under that website's blog folder.
3. A custom vertical 2:3 Pinterest graphic is uploaded.
4. The blog index and sitemap are updated.
5. Pinterest creates a Pin linked to the exact article URL.
6. Successful titles and slots are saved to reduce duplicates.

Existing homepages and current tools/templates are not overwritten.

## Required Actions secrets
In Settings > Secrets and variables > Actions, add:
- GEMINI_API_KEY — Google AI Studio API key.
- GITHUB_CONTENT_TOKEN — fine-grained GitHub token with Contents Read and write access to Smart-Tools-Hub and TemplivoX.
- PINTEREST_ACCESS_TOKEN — Pinterest OAuth access token with boards:read, boards:write and pins:write scopes.
- Optional for automatic token refresh: PINTEREST_APP_ID, PINTEREST_APP_SECRET and PINTEREST_REFRESH_TOKEN. If all three are set, the workflow refreshes the access token before each run.

Never place tokens in source code or commits.

## Pinterest setup
Register/connect a Pinterest developer app and authorize your account with boards:read, boards:write and pins:write. Add the token as PINTEREST_ACCESS_TOKEN. The automation finds or creates two public boards:
- Smart Tools Hub | Tips & Tutorials
- TemplivoX | Printable Planners & Templates

Pinterest Trial access can create Pins visible only to the app owner. Public distribution requires appropriate Standard access approval. Pinterest access tokens expire. Configure the three optional refresh secrets for automatic refresh. If Pinterest rotates your refresh token, update PINTEREST_REFRESH_TOKEN as the workflow log instructs. Otherwise, renew the access token manually when needed.

## Test
Open Actions > Pinterest Article Publisher > Run workflow. Choose a website and keep dry_run enabled for a preview. After reviewing the log, run again with dry_run disabled to publish one test article and Pin.
