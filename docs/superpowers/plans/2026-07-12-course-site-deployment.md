# SUIBE Summer School Course Site Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish both Quarto lecture HTML pages through a public GitHub repository and a continuously deployed Netlify site.

**Architecture:** Keep a narrowly scoped public repository whose root contains only deployment documentation and the reproducible `html_lectures` Quarto project. Netlify builds that project on every push to `main` and publishes `html_lectures/_site`; a minimal Quarto landing page provides stable links to both lectures.

**Tech Stack:** Git, GitHub CLI, Quarto Reveal.js, Python 3 post-render checks, Netlify CLI, Netlify continuous deployment.

## Global Constraints

- GitHub repository is public at `xqwang-sh/suibe-summer-school`.
- Netlify site name is `suibe-summer-school` when available.
- Default branch is `main`.
- Do not publish credentials, machine-specific files, unrelated working materials, caches, QA screenshots, or temporary files.
- A failed Quarto render must fail the Netlify deployment.
- Both lecture pages and the landing page must be publicly reachable over HTTPS.

---

### Task 1: Define and test the publishable repository boundary

**Files:**
- Create: `.gitignore`
- Create: `scripts/check_public_repo.sh`
- Test: direct shell execution of `scripts/check_public_repo.sh`

**Interfaces:**
- Consumes: the current course workspace and the approved public-repository boundaries.
- Produces: a tracked-file policy and an executable audit that returns zero only when forbidden paths and likely secrets are absent from tracked content.

- [ ] **Step 1: Write the failing repository audit**

Create `scripts/check_public_repo.sh` so it fails if tracked files include `.DS_Store`, `_site.zip`, `qa_screenshots`, `tmp`, `work`, `*.pptx`, or common token/private-key patterns. It must also confirm that both QMD files, `_quarto.yml`, `styles.scss`, and the deployment design are tracked.

- [ ] **Step 2: Run the audit and verify it fails before the source is scoped**

Run: `bash scripts/check_public_repo.sh`

Expected: non-zero exit with missing required tracked files.

- [ ] **Step 3: Add explicit ignore rules and stage only public course-site inputs**

The `.gitignore` must exclude OS metadata, caches, `_site.zip`, QA screenshots, temporary images, unrelated root documents, PPTX artifacts, and scratch directories. Stage required files explicitly rather than using `git add -A`.

- [ ] **Step 4: Run the audit and existing lecture checks**

Run:

```bash
bash scripts/check_public_repo.sh
cd html_lectures
python3 -m unittest scripts.test_lecture2_ai_tail scripts.test_verify_decks scripts.test_presentation_shell -q
python3 scripts/verify_decks.py
quarto render
python3 scripts/audit_rendered_site.py _site
```

Expected: repository audit exits zero; tests report `OK`; deck verifier and rendered-site audit report `OK`.

- [ ] **Step 5: Commit the scoped repository**

```bash
git add .gitignore scripts/check_public_repo.sh html_lectures docs/superpowers/specs/2026-07-12-course-site-deployment-design.md docs/superpowers/plans/2026-07-12-course-site-deployment.md
git commit -m "Prepare public summer school course site"
```

### Task 2: Add and test the course landing page

**Files:**
- Create: `html_lectures/index.qmd`
- Modify: `html_lectures/_quarto.yml`
- Test: `html_lectures/scripts/test_course_index.py`

**Interfaces:**
- Consumes: rendered filenames `lecture1_payment_banks.html` and `lecture2_capital_markets_ai.html`.
- Produces: `_site/index.html` containing direct relative links to both lecture pages.

- [ ] **Step 1: Write the failing landing-page test**

The test must render or inspect the generated index and assert that it contains both exact relative lecture URLs and the audience-facing title `SUIBE Summer School`.

- [ ] **Step 2: Run the test and verify it fails**

Run: `cd html_lectures && python3 -m unittest scripts.test_course_index -v`

Expected: failure because `index.qmd` or `_site/index.html` is absent.

- [ ] **Step 3: Add the minimal landing page**

Create an audience-facing page with the course title and two clearly labeled links. Add `index.qmd` to the Quarto project without changing either lecture's Reveal.js presentation format.

- [ ] **Step 4: Render and verify all three pages**

Run:

```bash
cd html_lectures
quarto render
python3 -m unittest scripts.test_course_index -v
python3 scripts/audit_rendered_site.py _site
```

Expected: test and audit pass; `_site/index.html` plus both lecture HTML files exist.

- [ ] **Step 5: Commit**

```bash
git add html_lectures/index.qmd html_lectures/_quarto.yml html_lectures/scripts/test_course_index.py html_lectures/_site
git commit -m "Add course landing page"
```

### Task 3: Configure a reproducible Netlify build

**Files:**
- Create: `netlify.toml`
- Create: `scripts/netlify_build.sh`
- Create: `scripts/test_netlify_config.py`

**Interfaces:**
- Consumes: the `html_lectures` Quarto project and Python post-render script.
- Produces: Netlify build output at `html_lectures/_site` and a configuration declaring that directory as the publish root.

- [ ] **Step 1: Write the failing configuration test**

The test must assert that `netlify.toml` invokes `scripts/netlify_build.sh`, publishes `html_lectures/_site`, and pins a supported Quarto version through a Netlify environment variable or explicit installer.

- [ ] **Step 2: Run the test and verify it fails**

Run: `python3 -m unittest scripts.test_netlify_config -v`

Expected: failure because Netlify configuration is absent.

- [ ] **Step 3: Implement the build wrapper and configuration**

The wrapper must use `set -euo pipefail`, verify `quarto` and `python3` are present, run `quarto render html_lectures`, and run the rendered-site audit. `netlify.toml` must publish only `html_lectures/_site`.

- [ ] **Step 4: Verify the local equivalent of the Netlify build**

Run:

```bash
python3 -m unittest scripts.test_netlify_config -v
bash scripts/netlify_build.sh
```

Expected: tests pass and the build exits zero with all three pages present.

- [ ] **Step 5: Commit**

```bash
git add netlify.toml scripts/netlify_build.sh scripts/test_netlify_config.py html_lectures/_site
git commit -m "Configure Netlify course deployment"
```

### Task 4: Publish the public GitHub repository

**Files:**
- No source changes expected.

**Interfaces:**
- Consumes: audited `main` branch.
- Produces: public GitHub repository `xqwang-sh/suibe-summer-school` with `origin` configured locally.

- [ ] **Step 1: Reconfirm authentication and repository scope**

Run:

```bash
gh auth status
git status -sb
bash scripts/check_public_repo.sh
```

Expected: authenticated account is `xqwang-sh`; branch is `main`; audit passes; no unrelated staged files.

- [ ] **Step 2: Create the public repository and push**

Run:

```bash
gh repo create xqwang-sh/suibe-summer-school --public --source=. --remote=origin --push
```

Expected: repository URL is returned and `main` tracks `origin/main`.

- [ ] **Step 3: Verify public repository metadata**

Run: `gh repo view xqwang-sh/suibe-summer-school --json nameWithOwner,visibility,url,defaultBranchRef`

Expected: visibility is `PUBLIC` and default branch is `main`.

### Task 5: Install Netlify CLI and connect continuous deployment

**Files:**
- Netlify may create or update `.netlify/state.json`; keep it ignored as machine-local state.

**Interfaces:**
- Consumes: public GitHub repository and `netlify.toml`.
- Produces: a Netlify site linked to the repository, with production deploys from `main`.

- [ ] **Step 1: Install and verify Netlify CLI**

Run: `npm install --global netlify-cli && netlify --version`

Expected: installation succeeds and a Netlify CLI version is printed.

- [ ] **Step 2: Authenticate Netlify**

Run: `netlify status`; if logged out, run `netlify login` and complete the browser authorization.

Expected: CLI reports the authenticated Netlify account.

- [ ] **Step 3: Create and link the site**

Run: `netlify sites:create --name suibe-summer-school`

If the name is unavailable, create without `--name`, retain the assigned name, and report it. Link the local checkout with `netlify link --id <site-id>` when creation does not link automatically.

- [ ] **Step 4: Connect the GitHub repository and deploy production**

Use Netlify CLI/API capabilities available in the authenticated session to connect `xqwang-sh/suibe-summer-school` to `main`. Then run `netlify deploy --build --prod` to establish the first verified production deployment.

- [ ] **Step 5: Verify continuous-deployment settings**

Run: `netlify api getSite --data '{"site_id":"<site-id>"}'`

Expected: response includes the production URL and repository build configuration. If the CLI cannot establish the repository hook non-interactively, open the Netlify repository-connection flow and pause only for the user's authorization click.

### Task 6: Verify the production website end to end

**Files:**
- No source changes expected unless verification exposes a deployment defect.

**Interfaces:**
- Consumes: Netlify production URL.
- Produces: evidence that the landing page and both lectures are publicly accessible and correctly linked.

- [ ] **Step 1: Retrieve the authoritative production URL**

Run: `netlify status`

Expected: a stable HTTPS site URL is printed.

- [ ] **Step 2: Check all public routes**

Run:

```bash
curl -fsSL "<site-url>/" | rg "SUIBE Summer School|lecture1_payment_banks.html|lecture2_capital_markets_ai.html"
curl -fsSL "<site-url>/lecture1_payment_banks.html" | rg "<title>"
curl -fsSL "<site-url>/lecture2_capital_markets_ai.html" | rg "<title>"
```

Expected: all commands exit zero and return the expected page content.

- [ ] **Step 3: Confirm GitHub-triggered deployment configuration**

Verify through the Netlify site metadata or deploy log that the site is linked to `xqwang-sh/suibe-summer-school`, branch `main`, with publish directory `html_lectures/_site`.

- [ ] **Step 4: Report final URLs and maintenance workflow**

Report the GitHub URL, Netlify URL, both direct lecture URLs, validation results, and the future update workflow: commit and push source changes to `main`; Netlify rebuilds automatically.
