# SUIBE Summer School Course Site Deployment Design

## Objective

Publish the two existing HTML lectures as a stable public course website. The site must be easy to share with students and automatically update through GitHub and Netlify, without manually copying rendered HTML files.

## Repository and site identity

- GitHub repository: `xqwang-sh/suibe-summer-school`
- Visibility: public
- Netlify site name: `suibe-summer-school` when available; otherwise use the closest available Netlify-generated name and report it explicitly.
- Default branch: `main`

## Public site structure

- `/`: a minimal course landing page linking to both lectures
- `/lecture1_payment_banks.html`: Lecture 1
- `/lecture2_capital_markets_ai.html`: Lecture 2

The landing page will show only course-facing information and direct lecture links. Internal QA notes, build diagnostics, and development instructions will not appear on the public site.

## Source and build model

The repository will contain the Quarto source and only the assets, styles, data, and scripts required to reproduce the course site. Netlify will build the site from the repository on every push to `main`.

The Netlify configuration will:

1. install or invoke an available Quarto runtime in the build environment;
2. render the `html_lectures` project;
3. publish `html_lectures/_site`;
4. treat a failed render as a failed deployment rather than publishing stale output.

Locally rendered `_site` output may be retained for immediate verification, but Netlify's deployed output must be reproducible from committed source files.

## Public-repository boundaries

Before the first push, the repository will be audited for secrets and unnecessary material. The public repository will exclude:

- caches, temporary files, rendered QA screenshots, and local virtual environments;
- credentials, tokens, browser profiles, and machine-specific configuration;
- unrelated raw downloads and working materials not required by the two lectures;
- operating-system metadata.

Existing course source files will not be rewritten merely to simplify deployment. Only deployment-related files and the minimal landing page will be added unless a build issue requires a targeted change.

## Deployment flow

1. Initialize the local repository on `main` and commit the scoped course-site files.
2. Create the public GitHub repository and push `main`.
3. Install and authenticate Netlify CLI.
4. Create or select the Netlify site and link it to the GitHub repository.
5. Configure continuous deployment from `main` using `netlify.toml`.
6. Trigger the first production deployment.
7. verify the landing page and both lecture URLs over HTTPS.

## Validation and failure handling

Before publishing, run the existing lecture tests, deck verifier, and rendered-site audit. After deployment, request all three public URLs and confirm successful HTTP responses and expected page titles.

If the preferred Netlify site name is unavailable, deployment may continue under an available name, but the final URL must be reported. If Netlify authentication requires an interactive browser confirmation, pause only for that authorization and resume automatically afterward. If a repository audit finds potentially private material, exclude it rather than publishing it by assumption.

## Success criteria

- The GitHub repository is public and contains reproducible source for both lectures.
- Netlify is connected to the GitHub repository and deploys automatically from `main`.
- The landing page and both lectures are publicly reachable over stable HTTPS URLs.
- A later push to `main` will trigger a new Netlify deployment without manual file copying.
