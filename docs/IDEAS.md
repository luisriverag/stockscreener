# Stock Screener Improvement Ideas

This document collects product and engineering ideas that could improve Stock Screener beyond the current roadmap.

## Product & UX

- **Saved screen presets**: Let users name, save, and quickly reapply filter combinations.
- **Watchlists**: Allow users to pin tickers and revisit them from a dedicated watchlist page.
- **Comparison workspace**: Select multiple companies and compare valuation, growth, margins, and price performance side by side.
- **Better onboarding states**: Show setup progress when the database is empty and make the data downloader status visible in the UI.
- **Light/dark theme toggle**: Keep the current dark theme but add a persisted light theme for daytime use.
- **Mobile-first table cards**: Convert dense tables into stacked metric cards on small screens.

## Data Quality & Coverage

- **Downloader health metadata**: Track last successful refresh, failed tickers, runtime, and data freshness per company.
- **Incremental refreshes**: Fetch only new stock-price rows and recently reported quarters instead of reprocessing the full ticker universe.
- **Ticker universe management**: Move ticker lists into editable config files and support custom user-provided ticker sets.
- **Data-source fallback**: Add alternate providers for missing Yahoo Finance values and mark source provenance per field.
- **Financial statement normalization**: Normalize line-item names across providers so charts remain stable when source labels differ.

## Charts & Analytics

- **Margin charts**: Add gross, operating, and net-margin trends beside revenue and expense charts.
- **Free-cash-flow view**: Chart operating cash flow, CAPEX, and free cash flow together.
- **Technical overlays**: Add moving averages, RSI, MACD, and Bollinger Bands to price charts.
- **Normalized comparison charts**: Compare multiple tickers on percentage change from a selected start date.
- **Chart export**: Export charts as PNG/SVG for reports and presentations.

## Alerts & Automation

- **Price and valuation alerts**: Notify users when price, P/E, growth, or spread thresholds are crossed.
- **Scheduled exports**: Generate and email CSV snapshots for saved screens.
- **Background job dashboard**: Show whether the downloader is idle, running, failed, or disabled.
- **Retry/backoff controls**: Add bounded retries for transient provider/API errors.

## Backend & Operations

- **Job queue abstraction**: Replace ad-hoc background threading with APScheduler/RQ/Celery if deployments need multiple workers.
- **Structured logging**: Emit JSON logs for downloads, request latency, and provider failures.
- **Pagination and server-side search**: Keep large result pages fast as the ticker universe grows.
- **Database migrations**: Introduce Alembic for schema changes rather than relying only on `create_all()`.
- **Automated tests**: Add unit tests for calculations, downloader parsing, route responses, and chart payload shapes.

## Security & Deployment

- **Config hardening**: Move runtime settings into environment variables with documented defaults.
- **Read-only demo mode**: Add a mode suitable for public demos where data updates and exports can be limited.
- **Container deployment**: Provide a Dockerfile and compose file for app + persistent SQLite volume.
- **Basic authentication**: Optional password protection for private deployments.

## Additional High-Impact Ideas

- **Data freshness badges**: Show per-company timestamps for latest price and latest financial quarter so users know when data is stale.
- **Provider error report**: Keep a downloadable report of tickers that failed during refresh, including provider error messages and retry counts.
- **Screen result snapshots**: Save historical snapshots of filtered results to track how screens change over time.
- **Valuation guardrails**: Flag negative earnings, missing shares outstanding, or stale market caps before showing calculated P/E values.
- **Accessibility pass**: Audit color contrast, keyboard navigation, focus states, and chart/table screen-reader labels.
- **Deployment profile docs**: Document recommended settings for local development, private server deployment, and read-only demo mode.

