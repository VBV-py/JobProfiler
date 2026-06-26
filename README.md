
# Redrob Hackathon — Intelligent Candidate Discovery & Ranking

AI-powered candidate ranking system for the Redrob Hackathon challenge. Ranks 100K candidates for a Senior AI Engineer role using multi-component scoring with behavioral signal modifiers.

## Prerequisites

- Python 3.10+ (tested on 3.11)
- 16 GB RAM
- No GPU required

### Setup

```bash
# Clone the repository
git clone https://github.com/VBV-py/JobProfiler.git
cd redrob-ranker

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Place the data

Copy `candidates.jsonl` (or `candidates.jsonl.gz`) into the `data/` directory:

## How to run:

### Option 1 - CLI based

#### Reproduce Submission

```bash
python rank.py --candidates ./data/candidates.jsonl --out ./output/team_id.csv
```

#### Validate

```bash
python validate_submission.py output/team_id.csv
```

<pre class="vditor-reset" placeholder="" contenteditable="true" spellcheck="false"><hr data-block="0"/></pre>

### Option 2- UI Based

#### Run Sandbox Locally

```bash
streamlit run app.py
```

---

## Approach

### Architecture

```
candidates.jsonl (100K)
      │
      ▼
 ┌───────────────┐
 │ Honeypot Check │ ← Detects ~80 impossible profiles (8 heuristic checks)
 └───────┬───────┘
         ▼
 ┌───────────────┐
 │ Coarse Filter  │ ← Quick-reject non-tech titles (Marketing, HR, Sales...)
 └───────┬───────┘
         ▼
 ┌───────────────┐
 │ Feature Engine │ ← 6 scoring dimensions (0.0 – 1.0 each)
 └───────┬───────┘
         ▼
 ┌───────────────┐
 │ Composite Score│ ← Weighted sum × behavioral modifier
 └───────┬───────┘
         ▼
 ┌───────────────┐
 │ Rank Top 100   │ ← Sort, assign ranks, generate reasoning
 └───────────────┘
```

### Scoring Components

| Component                     | Weight | What It Measures                                                         |
| ----------------------------- | ------ | ------------------------------------------------------------------------ |
| **Title Relevance**     | 25%    | Current title alignment with AI/ML engineering roles                     |
| **Skill Match**         | 20%    | Must-have + nice-to-have skill overlap, with endorsement trust weighting |
| **Career Trajectory**   | 25%    | Product company experience, production ML work, career stability         |
| **Experience Fit**      | 10%    | Years of experience vs the JD's 5-9 year sweet spot                      |
| **Location**            | 5%     | Proximity to Pune/Noida (preferred)                                      |
| **Education**           | 5%     | Institution tier + field relevance                                       |
| **Behavioral Modifier** | 10%    | Engagement signals: response rate, recency, notice period                |

### Key Design Decisions

1. **Title is the strongest filter** — the JD explicitly warns that keyword-matching is a trap. A "Marketing Manager" with perfect AI skills is not a fit.
2. **Endorsement + duration trust multiplier** — skills with 0 endorsements and 0 duration are down-weighted as potential keyword stuffing.
3. **Career trajectory > skill count** — building a recommendation system at a product company matters more than listing "Pinecone" as a skill.
4. **Behavioral signals as multiplicative modifier** — a perfect candidate who hasn't logged in for 6 months and won't respond to recruiters is not actually available.
5. **8-check honeypot detector** — catches impossible profiles (experience > career span, expert skills with 0 duration, overlapping career dates, etc.)

### Runtime

- ~2 minutes for 100K candidates on CPU (well within 5-minute budget)
- ~16 GB RAM peak usage (streaming mode for memory efficiency)
- No GPU, no network calls during ranking

---

## Project Structure

```
redrob-ranker/
├── rank.py                      # Main CLI entry point
├── app.py                       # Streamlit sandbox (required for submission)
├── explore_data.py              # Data exploration script
├── validate_submission.py       # Format validator (from challenge bundle)
├── requirements.txt             # Dependencies
├── submission_metadata.yaml     # Submission metadata
├── Dockerfile                   # Docker sandbox option
├── setup.md                     # Detailed setup guide
├── src/
│   ├── __init__.py
│   ├── config.py                # All tunable weights, skill lists, thresholds
│   ├── data_loader.py           # JSONL/JSON/GZ data loading + streaming
│   ├── honeypot_detector.py     # 8-check honeypot detection
│   ├── feature_engineering.py   # 6 scoring dimensions
│   ├── behavioral_signals.py    # Behavioral engagement modifier
│   ├── scoring.py               # Composite scoring engine
│   ├── ranker.py                # Ranking pipeline orchestrator
│   └── reasoning.py             # Per-candidate reasoning generation
├── data/
│   ├── candidates.jsonl         # 100K candidate pool (not in git)
│   └── sample_candidates.json   # 50 sample candidates
└── output/
    └── team_id.csv           # Final ranked output
```

---

## Submission Contents

1. **CSV file** — `output/team_id.csv` (100 ranked candidates)
2. **This repository** — full source code with setup instructions
3. **Sandbox** — Streamlit app at [sandbox URL]
4. **Metadata** — `submission_metadata.yaml`
