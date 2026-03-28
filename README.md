# Mailchimp Reporter

Mailchimp Reporter is a read-only command-line tool for pulling Mailchimp Marketing API data and exporting it as CSV, JSON, or a console table.

## Supports

- `audiences` - list audiences from the connected Mailchimp account
- `campaigns` - list campaigns from the connected Mailchimp account
- `contacts` - list contacts for a specific audience

Output modes:
- `csv` (saved to file)
- `json` (saved to file)
- `table` (printed to terminal)

When file output is used, files are saved under `~/mcr_outputs` unless you provide `--savefile`.

## Requirements

- Python 3.11+
- A valid Mailchimp Marketing API key

## Configure Mailchimp API key

The CLI loads credentials from a JSON file. The current logic accepts either `api_key` or `mailchimp_api_key` as the JSON key name.

The repository includes a starter `auth.json` with a placeholder value:

```json
{
  "api_key": "YOUR_API_KEY"
}
```

You must replace the placeholder with a real API key before running commands. If the placeholder is still present, the CLI intentionally raises an error.

To generate or manage your Mailchimp API key, use Mailchimp's official quick start guide:
- [Mailchimp Marketing API quick start](https://mailchimp.com/developer/marketing/guides/quick-start/)

Recommended local setup:
1. Copy the sample file to your own local config path (for example `config/auth.json`).
2. Update the value to your real key in `token-datacenter` format.
3. Keep credential files local and out of source control.

## CLI usage

### Automated execution (non-interactive)

Run commands with all required options supplied:

```bash
python main.py audiences --config auth.json --output csv --limit 50
```

```bash
python main.py campaigns --config auth.json --output json --limit 100 --savefile weekly_campaigns.json
```

```bash
python main.py contacts --config auth.json --audience-id YOUR_AUDIENCE_ID --output table --limit 25
```

Notes:
- Use `--output table` for terminal display only.
- Use `--output csv` or `--output json` to write files.
- If `--savefile` is omitted for file outputs, the CLI auto-generates a timestamped filename.

### Prompted options (interactive mode)

If you run the CLI without a command, it will prompt for missing values:

```bash
python main.py
```

Typical prompt flow:
1. Choose command (`audiences`, `campaigns`, or `contacts`)
2. Provide audience ID if `contacts` is selected
3. Provide config path (default prompt shows `config/auth.json`)
4. Choose output format (`csv`, `json`, or `table`)
5. Choose max results (default 100)
6. Optionally provide savefile path for `csv` or `json`

You can also partially prefill options and let prompts fill the rest:

```bash
python main.py --config auth.json --output csv
```

## License

MIT License - see [LICENSE](LICENSE).

## Contributors

- **Joe Thompson** (@jopeymonster)

## Legal

The developers of this application are not responsible for any actions performed using this tool. Your privacy is respected - see our [Privacy Policy](https://jopeymonster.github.io/privacy/).
