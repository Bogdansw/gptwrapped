# GPT Wrapped

An offline, privacy-first tool that builds an interactive, Spotify Wrapped-style summary of your ChatGPT usage from your exported data.

**Runs entirely on your machine in the browser, with no data ever leaving your computer.**

---

## Quick Start

### Windows (GUI)

- Double-click the **GPT Wrapped** shortcut on your Desktop.
- Alternatively, run `Launch GPT Wrapped.vbs` directly from the project folder.

### From Source / CLI

Requires **Python 3.8+**.

Install the dependencies:

```bash
pip install -r requirements.txt
```

**Run the Desktop Interface:**

```bash
python gui.py
```

**Run the CLI:**

```bash
python gpt_wrapped.py path/to/export.zip
```

#### CLI Options

| Option | Description |
|---|---|
| `--year YEAR` | Filter activity by a specific year. |
| `--output DIR` | Specify a custom export directory. |
| `--no-browser` | Prevent the browser from opening automatically when processing completes. |

**Examples:**

```bash
python gpt_wrapped.py export.zip --year 2026
python gpt_wrapped.py export.zip --output ./reports
python gpt_wrapped.py export.zip --no-browser
```

---

## How It Works

1. **Attach Export:** Select your ChatGPT export `.zip` file, or test the application using `sample_export.zip`.
2. **Select Period:** Choose a specific year or analyze your all-time activity.
3. **Generate Report:** The tool parses your data in memory and generates a standalone HTML report.

---

## Privacy & Design

- **Zero Network Activity:** No telemetry, cloud APIs, or analytics.
- **Standalone Output:** Generated HTML reports contain all CSS, SVG graphics, and JavaScript inline. They work completely offline without loading remote scripts or CDN assets.
- **In-Memory ZIP Parsing:** Reads data directly from the archive without extracting thousands of individual files to your disk.

---

## Features & Metrics

### Core Statistics

- Total conversations and message counts.
- User-to-assistant message ratio.
- Active days and consecutive activity streaks.

### Time Distribution

- Monthly activity heatmaps.
- Activity breakdown by day of the week.
- Time-of-day analysis, including **Night Owl** and **Early Bird** detection.

### Topic Engine

- Classifies conversations into **11 categories**.
- Supports both English and Romanian.
- Uses stopword filtering to improve topic classification.

### Conversation Highlights

- Detects notable conversations, including your longest thread (**The Rabbit Hole**).
- Identifies quick lookups consisting of two messages or fewer.

### Interactive Experience

- Switch between a full-scroll report and an interactive story-slide mode.

---

## Repository Structure

```text
├── parser.py            # Resilient JSON DAG tree and legacy format parser
├── analyzer.py          # Metrics, time-series aggregations, and award triggers
├── topics.py            # Keyword classification and bilingual stopword filtering
├── report.py            # Self-contained HTML/SVG report generator
├── gpt_wrapped.py       # CLI entry point and workflow orchestrator
├── gui.py               # Desktop wrapper interface
├── test_gpt_wrapped.py  # Automated test suite and mock data generator
└── sample_export.zip    # Mock data for rapid testing
```

---

## Testing

Run the automated test suite against mock data:

```bash
python test_gpt_wrapped.py
```

---

## Requirements

- Python 3.8 or newer.
- Dependencies listed in `requirements.txt`.
- A ChatGPT data export in `.zip` format, or the included `sample_export.zip` for testing.

---

## Privacy First

GPT Wrapped is designed to keep your ChatGPT usage data private. Your conversations are processed locally, and the generated report is designed to work offline.

**Your data. Your machine. Your insights.**