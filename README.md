# Mailchimp Reporter

Mailchimp Reporter is a read-only command-line tool for pulling Mailchimp Marketing API data and exporting it as CSV, JSON, or a console table.

## Supported reports

### audiences

Lists Mailchimp audiences from the authenticated account.

Examples:

```bash
mcr audiences --config config/auth.json --output table --limit 100
```

```bash
mcr audiences --config config/auth.json --audience-id YOUR_AUDIENCE_ID --output table
```

```bash
mcr audiences --config config/auth.json --audience "Customers" --output json
```

### campaigns

Lists Mailchimp campaigns from the authenticated account. Campaigns can be scoped to an audience by ID or name.

Examples:

```bash
mcr campaigns --config config/auth.json --output table --limit 100
```

```bash
mcr campaigns --config config/auth.json --audience-id YOUR_AUDIENCE_ID --output json
```

```bash
mcr campaigns --config config/auth.json --audience "Customers" --subject "spring" --output table
```

### contacts

Lists contacts for a specific Mailchimp audience. Contacts require either `--audience-id` or `--audience`.

Examples:

```bash
mcr contacts --config config/auth.json --audience-id YOUR_AUDIENCE_ID --output table --limit 100
```

```bash
mcr contacts --config config/auth.json --audience "Customers" --email "example.com" --output json
```

```bash
mcr contacts --config config/auth.json --audience "Customers" --name "ada" --output table
```

### whoami

Shows authenticated Mailchimp account context from the API root endpoint. This report does not require audience or date arguments.

Example:

```bash
mcr whoami --config config/auth.json --output table
```

## Output modes

- `csv` - saved to file
- `json` - saved to file
- `table` - printed to terminal

When file output is used, files are saved under `~/mcr_outputs` unless you provide `--savefile`.

## Requirements

- Python 3.11+
- A valid Mailchimp Marketing API key

## Installation

Create a virtual environment, activate it, and install the package in editable mode from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

After installation, use the console entrypoint:

```bash
mcr --help
```

For development dependencies, install the `dev` extra:

```bash
pip install -e ".[dev]"
```

## Configure Mailchimp API key

The CLI loads credentials from a JSON file. The current logic accepts either `api_key` or `mailchimp_api_key` as the JSON key name.

Example config file:

```json
{
  "api_key": "YOUR_API_KEY"
}
```

You must replace the placeholder with a real API key before running commands. If the placeholder is still present, the CLI intentionally raises an error.

To generate or manage your Mailchimp API key, use Mailchimp's official quick start guide:

- [Mailchimp Marketing API quick start](https://mailchimp.com/developer/marketing/guides/quick-start/)

Recommended local setup:

1. Copy the sample file to your own local config path, such as `config/auth.json`.
2. Update the value to your real key in `token-datacenter` format.
3. Keep credential files local and out of source control.

## CLI usage

Run commands with all required options supplied:

```bash
mcr audiences --config config/auth.json --output table --limit 50
```

```bash
mcr campaigns --config config/auth.json --output json --limit 100 --savefile weekly_campaigns.json
```

```bash
mcr contacts --config config/auth.json --audience-id YOUR_AUDIENCE_ID --output table --limit 25
```

Notes:

- Use `--output table` for terminal display only.
- Use `--output csv` or `--output json` to write files.
- If `--savefile` is omitted for file outputs, the CLI generates a timestamped filename.

## Audience selection

Reports that support audience scoping accept these options:

- `--audience-id` - uses the supplied Mailchimp audience ID directly.
- `--audience` - resolves a Mailchimp audience name to an ID before fetching scoped data.

Resolution behavior:

- Direct `--audience-id` values bypass name resolution.
- `--audience` performs an exact case-insensitive audience name match.
- No match, duplicate matches, or a matched audience without an ID raises an error.
- `audiences` without either option uses the paginated `/lists` collection endpoint.
- `audiences` with an audience ID or resolved audience name uses `lists/{audience_id}` without collection query parameters.

## Date filtering

The report commands support date range options where the underlying Mailchimp endpoint has a mapped API parameter:

```bash
--start-date YYYY-MM-DD
--end-date YYYY-MM-DD
--last DAYS
--previous week|month|quarter|year
```

Precedence and validation rules:

- `--start-date` and `--end-date` can be used together or individually.
- `--last` creates an inclusive date range ending today.
- `--previous` creates the prior completed named period.
- `--last` and `--previous` are mutually exclusive.
- Explicit `--start-date` or `--end-date` cannot be combined with `--last` or `--previous`.

## Local post-fetch filters

Local filters are applied after the Mailchimp API fetch. They do not add or change Mailchimp API query parameters.

### Campaign filters

```bash
--subject TEXT
```

`--subject` performs a case-insensitive partial match against normalized campaign subject or title fields.

### Contact filters

```bash
--email TEXT
--name TEXT
```

`--email` performs a case-insensitive partial match against email addresses.

`--name` performs a case-insensitive partial match against available normalized contact name fields, including full name, first name, and last name when present.

If no rows match a local filter, the command returns an empty result cleanly.

## Prompted options

If you run the CLI without a command, it prompts for missing values:

```bash
mcr
```

Typical prompt flow:

1. Choose command: `audiences`, `campaigns`, `contacts`, or `whoami`.
2. Provide audience ID if `contacts` is selected and no audience name was supplied.
3. Provide config path. The default prompt shows `config/auth.json`.
4. Choose output format: `csv`, `json`, or `table`.
5. Choose max results for collection reports. The default is 100.
6. Optionally provide savefile path for `csv` or `json`.

You can also partially prefill options and let prompts fill the rest:

```bash
mcr --config config/auth.json --output csv
```

## Testing

Run these checks before submitting changes:

```bash
python -m compileall mcr
python -m pytest -q
python -m ruff check .
git diff --check
```

## License

MIT License - see [LICENSE](LICENSE).

## Contributors

- **Joe Thompson** (@jopeymonster)

## Legal

The developers of this application are not responsible for any actions performed using this tool. Your privacy is respected - see our [Privacy Policy](https://jopeymonster.github.io/privacy/).
