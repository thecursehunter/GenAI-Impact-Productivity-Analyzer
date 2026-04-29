# GenAI Impact & Productivity Analyzer (GIPA)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-green)](https://www.djangoproject.com/)

> A research-grade A/B testing tool for measuring the impact of Generative AI (GitHub Copilot) on software developer productivity.
> Built on the **Fair Developer Score (FDS)** algorithm — quantifying developer output as **Effort × Build Importance** using only Git commit data.

---

## 🎯 Research Purpose

This tool was developed to support an **IEEE academic paper** investigating whether Generative AI assistance (GitHub Copilot) meaningfully changes developer productivity. The system accepts two Git commit CSV datasets and performs a full FDS scoring pipeline on each group independently, then compares:

- **H1 — Speed**: Did GenAI reduce mean time-between-commits (`dt_prev_commit_sec`)?
- **H2 — Scale**: Did GenAI increase total lines of functional code produced (effective churn)?

---

## 🎥 Demo

### Upload Form — Start a New A/B Experiment

<!-- 📌 PLACEHOLDER: Replace with a screenshot or GIF of /ab-experiment/new/ -->
![A/B Experiment Upload Form](docs/demo_upload.gif)

*Dual CSV upload interface — Control Group (blue) vs GenAI Group (violet)*

### A/B Comparison Dashboard

<!-- 📌 PLACEHOLDER: Replace with a screenshot or GIF of /ab-experiment/<id>/ after completion -->
![A/B Comparison Dashboard](docs/demo_dashboard.gif)

*Side-by-side Speed & Scale comparison charts, hypothesis finding banner, radar chart, and developer tables*

### Single-Repository FDS Dashboard (Original Feature)

<!-- 📌 PLACEHOLDER: Replace with a screenshot or GIF of a completed single analysis dashboard -->
![FDS Analysis Dashboard](docs/demo_fds.gif)

*Per-developer FDS scores, build timeline, and 6-dimension contribution breakdown*

---

## 🧪 A/B Experiment Feature (New)

The core new feature for this research. Navigate to `/ab-experiment/new/` — **no login required**.

### Required CSV Schema (both files must match exactly)

```
hash, author_name, author_email, commit_ts_utc, dt_prev_commit_sec,
files_changed, insertions, deletions, is_merge, dirs_touched,
file_types, msg_subject, batch_id
```

### Workflow

1. Upload `Control_Group.csv` (developers without AI) and `GenAI_Group.csv` (GitHub Copilot users)
2. The FDS pipeline runs independently on each group in the background (~20–60 seconds)
3. The comparison dashboard auto-loads with:
   - **Headline KPI deltas**: Speed Δ%, Churn Δ%, FDS Score Δ%
   - **Key Finding banner**: auto-generated hypothesis statement
   - **5 charts**: Speed bar, Scale bar, 6-dimension Radar, FDS distribution, Speed×Scale scatter
   - **Per-developer tables** for both groups

---

## 💡 Algorithm Overview

### Step 1 — TORQUE Clustering

Commits are clustered into **builds** (logical units of work) using temporal gaps and directory similarity:

```
New build when:
  Δt > TIME_GAP_HOURS (default 2h)
  OR Jaccard(dir_set_curr, dir_set_prev) < 0.30
```

> **Note:** For the A/B experiment feature, CSVs already include a `batch_id` column, so this step is skipped.

### Step 2 — Developer Effort (per developer `u`, build `k`)

$$\text{Effort}(u, k) = \text{Share}(u, k) \cdot \left( 0.25 Z_{\text{scale}} + 0.15 Z_{\text{reach}} + 0.20 Z_{\text{central}} + 0.20 Z_{\text{dom}} + 0.15 Z_{\text{novel}} + 0.05 Z_{\text{speed}} \right)$$

| Dimension | Meaning |
|-----------|---------|
| **Share** | Author's churn / total build churn |
| **Scale** | log(1 + author churn), MAD-z normalized |
| **Reach** | Directory entropy (how broadly the author spread work) |
| **Centrality** | Mean PageRank of directories touched |
| **Dominance** | First/last committer + commit-count share |
| **Novelty** | New file lines + key-path lines / total churn |
| **Speed** | exp(−hours_since_prev / τ), decay-based |

### Step 3 — Build Importance (per build `k`)

$$\text{Importance}(k) = 0.30 Z_{\text{scale}} + 0.20 Z_{\text{scope}} + 0.15 Z_{\text{central}} + 0.15 Z_{\text{complex}} + 0.10 Z_{\text{type}} + 0.10 Z_{\text{release}}$$

### Step 4 — Final FDS Score

$$\text{FDS}(u) = \sum_k \text{Effort}(u, k) \times \text{Importance}(k)$$

### Robust Standardization (MAD-z)

All raw features are standardized using Median Absolute Deviation to resist outliers:

$$z = \text{clip}\left(\frac{x - \text{median}}{1.4826 \cdot \text{MAD}},\ -3,\ +3\right)$$

---

## 🖥️ Web Application Features

| Feature | URL | Auth Required | Purpose |
|---------|-----|---------------|---------|
| **⚗️ A/B Experiment** | `/ab-experiment/new/` | ❌ No | Core research tool — upload two CSVs, compare groups |
| **📊 FDS Analysis** | `/create-analysis/` | ✅ Yes | Analyze a single GitHub repository via URL |
| **🌐 Public Analyses** | `/analyses/` | ❌ No | Browse all shared analyses |
| **⚙️ Parameter Sets** | `/parameters/` | ✅ Yes | Create/tune custom FDS weight configurations |
| **👤 User Dashboard** | `/dashboard/` | ✅ Yes | View your analyses and activity |

---

## 🚀 Local Setup

### Prerequisites

- Python 3.10+
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/thecursehunter/GenAI-Impact-Productivity-Analyzer.git
cd "GenAI Impact & Productivity Analyzer"

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply database migrations
cd fds_webapp
python manage.py migrate

# 5. Run the development server
python manage.py runserver
```

The app will be available at **http://127.0.0.1:8000**

To access the A/B experiment tool directly: **http://127.0.0.1:8000/ab-experiment/new/**

---

## 📁 Project Structure

```
GenAI Impact & Productivity Analyzer/
├── fds_webapp/                     # Django web application
│   ├── dev_productivity/
│   │   ├── fds_algorithm/          # Core FDS algorithm modules
│   │   │   ├── preprocessing/      # DataProcessor — noise filtering, PageRank
│   │   │   ├── effort_calculator/  # DeveloperEffortCalculator
│   │   │   ├── importance_calculator/ # BatchImportanceCalculator
│   │   │   └── fds_calculator.py   # FDS aggregation and scoring
│   │   ├── ab_service.py           # ⭐ A/B experiment background service (NEW)
│   │   ├── models.py               # Django ORM — incl. ABExperiment, ABDeveloperScore
│   │   ├── views.py                # URL handlers
│   │   ├── forms.py                # Upload forms — incl. ABExperimentForm
│   │   ├── services.py             # Single-repo FDS pipeline
│   │   └── templates/
│   │       └── dev_productivity/
│   │           ├── ab_dashboard.html        # ⭐ A/B comparison dashboard (NEW)
│   │           ├── create_ab_experiment.html # ⭐ A/B upload form (NEW)
│   │           ├── base.html                # Shared layout (GIPA rebrand)
│   │           └── dashboard.html           # Single-repo FDS dashboard
│   └── fds_webapp/
│       └── settings.py
├── modules/                        # Standalone algorithm scripts
│   ├── fds_algorithm/
│   └── torque_clustering/
├── README.md
├── DEPLOYMENT_GUIDE.md
├── USER_GUIDE.md                   # ⭐ New user guide for research use
└── requirements.txt
```

---

## 📊 Output Artifacts

| File | Description |
|------|-------------|
| `build_table.csv` | Per-build Importance components |
| `effort_table.csv` | Per developer–build Effort components |
| `contribution_table.csv` | `contribution = effort × importance` |
| `fds_table.csv` | Final FDS scores per developer |

---

## 🔧 Configuration

Default algorithm weights are tunable via the **Parameter Sets** UI (`/parameters/`):

```text
# Effort weights
W_SCALE=0.25  W_REACH=0.15  W_CENTRAL=0.20  W_DOM=0.20  W_NOVEL=0.15  W_SPEED=0.05

# Importance weights
A_SCALE=0.30  A_SCOPE=0.20  A_CENTRAL=0.15  A_COMPLEX=0.15  A_TYPE=0.10  A_RELEASE=0.10

# Clustering
TIME_GAP_HOURS=2   JACCARD_MIN=0.30   ALPHA_PAGERANK=0.85
```

---

## 📄 License & Citation

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

If you use this tool in academic work, please cite the associated IEEE paper.

---

<div align="center">

**⭐ If this research tool helps your work, please star the repository! ⭐**

</div>
