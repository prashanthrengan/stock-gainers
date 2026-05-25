# GitHub Actions Setup

Upload this workspace to a GitHub repository.

## Required secrets

Create these in GitHub:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM`

For Gmail, use an app password, not your normal Gmail password.

## Output

Each run saves files in:

- `outputs/europe_open/`
- `outputs/europe_pre_close/`
- `outputs/us_open/`
- `outputs/us_pre_close/`

The workflow also emails the latest CSV and summary to:

- `prashanthrengan@gmail.com`

## Data source

If no CSV exists under `data/`, the workflow fetches Yahoo Finance day gainers using an unofficial public endpoint. For Nordnet/European coverage, add provider-specific CSVs under:

- `data/europe_open/`
- `data/europe_pre_close/`

or add a dedicated fetcher later.

## Manual run

Use GitHub Actions > Stock Discovery Reports > Run workflow.

