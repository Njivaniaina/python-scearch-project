# Visual Search Engine — Reconaise

A CLI-based image analysis tool powered by **Groq LLM (Llama 4 Scout)** and **DuckDuckGo Search**. Give it any image, and it will identify the subject, find related web articles, discover similar images, and save everything to a local history.

## Features

- **AI Vision Analysis** — Identifies objects, categories, and attributes from any image using Llama 4 Scout (17B)
- **Structured Output** — Extracts exact names, descriptions, keywords, and optimized search queries via JSON
- **Web Search** — Automatically searches DuckDuckGo for related articles (8 results)
- **Image Search** — Finds visually similar images via DuckDuckGo (5 results)
- **Persistent History** — Saves all analyses to local JSON files with duplicate detection
- **History Browsing** — Browse past analyses or view detailed results by name

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd <repository-directory-name>
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

Create a `.env` file in the project root:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

> Get a free API key at [https://console.groq.com](https://console.groq.com)

## Usage

### Analyze an image

```bash
python3 main.py --image photo.jpg
```

**Supported formats:** JPEG, PNG, WebP

### View analysis history

```bash
python3 main.py --historique
```

### View details of a specific entry

```bash
python3 main.py --detail "Monstera deliciosa"
```

## Project Structure

```
reconaise/
├── main.py           # CLI entry point & orchestration
├── config.py         # Model configuration & analysis prompt
├── image_utils.py    # Image encoding (base64) & Groq LLM call
├── search.py         # DuckDuckGo web & image search
├── display.py        # Formatted terminal output
├── history.py        # JSON-based history persistence & indexing
├── requirements.txt  # Python dependencies
├── .env              # API key (not versioned)
└── history/          # Saved analysis results (JSON)
    ├── index.json
    └── <object_name>.json
```

## Architecture

```
┌────────────┐     ┌───────────────┐     ┌────────────┐
│   Image    │────▶│  image_utils  │────▶│  Groq API  │
│  (input)   │     │ (base64+LLM)  │     │(Llama 4)   │
└────────────┘     └───────────────┘     └─────┬──────┘
                                               │
                                         JSON response
                                               │
                   ┌───────────────┐     ┌─────▼──────┐
                   │  DuckDuckGo   │◀────│   main.py  │
                   │ (web+images)  │     │  (search)  │
                   └───────┬───────┘     └─────┬──────┘
                           │                   │
                   ┌───────▼───────┐     ┌─────▼──────┐
                   │   display.py  │     │ history.py  │
                   │  (terminal)   │     │  (JSON)     │
                   └───────────────┘     └────────────┘
```

## Technology Stack

| Technology | Purpose |
|---|---|
| [Groq API](https://groq.com) | LLM inference (Llama 4 Scout 17B — vision + text) |
| [ddgs](https://pypi.org/project/ddgs/) | DuckDuckGo search (no API key needed) |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Secure API key management via `.env` |
| Python 3 + argparse | CLI framework |

## Example Output

```
$ python3 main.py --image plante.jpg

Analyzing image: plante.jpg ...

=== Analysis Characteristics ===
Object      : houseplant
Category    : plant
Description : A large tropical houseplant with distinctive split leaves,
              commonly known as the Swiss Cheese Plant.
Exact name  : Monstera deliciosa
Attributes  : green, tropical, perforated leaves
Keywords    : monstera, deliciosa, swiss cheese plant, tropical, houseplant
===================================

=== Web Search Results ===
[1] Monstera Deliciosa — Complete Care Guide
    URL: https://www.example.com/monstera-care
[2] How to Grow Monstera Indoors
    URL: https://www.example.com/grow-monstera
===================================

=== Similar Images ===
[1] Monstera Deliciosa Plant
    Image URL: https://www.example.com/img/monstera.jpg
===================================

[History] New item : 'Monstera deliciosa' → history/Monstera_deliciosa.json

Query used: Monstera deliciosa swiss cheese plant care
```
