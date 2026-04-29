# 📖 GIPA User Guide — GenAI Impact & Productivity Analyzer

> **Who this guide is for:** Researchers, professors, and students evaluating the tool as part of an IEEE study on Generative AI's impact on developer productivity. No programming knowledge is required to use the web interface.

---

## 🗺️ Quick Navigation

| I want to… | Go to |
|------------|-------|
| Run an A/B comparison between Control and GenAI groups | [A/B Experiment](#-ab-experiment-the-core-research-feature) |
| Understand what each metric means | [Metric Reference](#-metric-reference) |
| Browse previously run experiments | [Public Analyses](#-public-analyses) |
| Analyze a single GitHub repo | [FDS Analysis (Optional)](#-fds-analysis-single-repository-optional) |
| Customize algorithm weights | [Parameter Sets (Advanced)](#-parameter-sets-advanced-optional) |
| Know which features to mention in my essay | [Essay Reference](#-essay-reference-which-features-to-mention) |

---

## ⚗️ A/B Experiment — The Core Research Feature

This is the primary tool for your research. It takes two CSV files and produces a side-by-side productivity comparison.

### Step 1 — Navigate to the Upload Page

Go to: **`http://127.0.0.1:8000/ab-experiment/new/`**

You will see a two-panel upload form. **No account or login is required.**

<!-- 📌 PLACEHOLDER: Add screenshot of the upload form here -->
<!-- ![Upload Form Screenshot](docs/screenshot_upload_form.png) -->

### Step 2 — Fill in the Experiment Details

| Field | What to enter |
|-------|---------------|
| **Experiment Name** | A short descriptive label, e.g. `Sprint 23 — Copilot Study` |
| **Notes** (optional) | Team size, sprint duration, project context |

### Step 3 — Upload Your CSV Files

Drag and drop (or click) to upload:

| Zone | File | Represents |
|------|------|------------|
| 🔵 **Control Group CSV** | `Control_Group.csv` | Developers working **without** GitHub Copilot |
| 🟣 **GenAI Group CSV** | `GenAI_Group.csv` | Developers working **with** GitHub Copilot |

> ⚠️ **Both files must have exactly these 13 columns** (the form will validate this):
> ```
> hash, author_name, author_email, commit_ts_utc, dt_prev_commit_sec,
> files_changed, insertions, deletions, is_merge, dirs_touched,
> file_types, msg_subject, batch_id
> ```

### Step 4 — Submit and Wait

Click **⚗️ Run A/B Analysis**. The page will redirect to the dashboard, which shows a loading spinner while the FDS pipeline processes both datasets. This typically takes **20–60 seconds** depending on CSV size.

> The analysis runs in the background. You can safely stay on the page or reload it — your experiment is saved in the database.

### Step 5 — Reading the Dashboard

Once complete, the dashboard renders automatically. Here is what each section shows:

<!-- 📌 PLACEHOLDER: Add screenshot of completed dashboard here -->
<!-- ![Dashboard Screenshot](docs/screenshot_dashboard.png) -->

---

#### 🔬 Key Finding Banner

The top of the dashboard shows an auto-generated sentence directly aligned to your research hypothesis:

> *"The GenAI group committed **X% faster** (lower mean time-between-commits: Xmin vs Xmin) and produced **Y% more code** per developer (X vs X lines). Mean FDS score changed by **+Z%**."*

This is the sentence to quote or paraphrase in your paper.

---

#### ⚡ Speed KPI Card (Hypothesis H1)

| What it shows | How to interpret |
|---------------|-----------------|
| **Δ Speed %** | Positive = GenAI commits faster (less time between commits) |
| Control (sec) | Mean `dt_prev_commit_sec` for the Control group |
| GenAI (sec) | Mean `dt_prev_commit_sec` for the GenAI group |

A **positive Speed Δ** (e.g., `+34%`) means GenAI developers committed 34% faster than the Control group. This supports H1.

---

#### 📊 Scale KPI Card (Hypothesis H2)

| What it shows | How to interpret |
|---------------|-----------------|
| **Δ Scale %** | Positive = GenAI produces more code per developer |
| Control (lines) | Mean effective churn per developer in the Control group |
| GenAI (lines) | Mean effective churn per developer in the GenAI group |

A **positive Scale Δ** (e.g., `+21%`) means GenAI developers produced 21% more lines of functional code. This supports H2.

> **Note on "effective churn":** Raw insertions + deletions are noise-filtered (vendor files, whitespace-only changes are down-weighted). This represents *meaningful* code output, not just any line change.

---

#### 🏆 FDS Score KPI Card

The overall Fair Developer Score delta. A positive Δ means GenAI developers scored higher in the composite quality-weighted productivity metric.

---

#### 📈 Chart 1 — Speed Bar Chart

Side-by-side bars showing mean time-between-commits for each group. **Shorter bar = faster.** Use this chart in your paper to visually demonstrate H1.

---

#### 📈 Chart 2 — Scale Bar Chart

Side-by-side bars showing mean total churn per developer. **Taller bar = more code produced.** Use this chart to demonstrate H2.

---

#### 🕸️ Chart 3 — FDS Radar (6 Dimensions)

A radar/spider chart comparing the two groups across all six FDS effort dimensions:

| Dimension | Meaning |
|-----------|---------|
| Speed | How quickly commits arrive |
| Scale | How much code is written |
| Reach | How broadly work spans directories |
| Centrality | Whether work touches architecturally important code |
| Dominance | Whether the developer leads a build |
| Novelty | Whether new files or key paths are introduced |

Use this chart to show that AI assistance affects productivity multidimensionally, not just in one metric.

---

#### 📊 Chart 4 — FDS Distribution

Top 10 developers per group ranked by FDS score, shown as grouped bars. Use this to show the score spread within each group.

---

#### 🔵🟣 Chart 5 — Speed × Scale Scatter

Each dot represents one developer. X-axis = mean seconds between commits (lower = faster). Y-axis = total churn (higher = more code). Groups are color-coded blue (Control) and violet (GenAI).

Use this chart to show the *distribution* of the productivity relationship — ideal for identifying outliers or cluster separation between groups.

---

#### 👥 Developer Tables

Scrollable tables listing every developer in each group with:
- FDS score
- Mean commit interval (Speed)
- Total churn (Scale)
- Number of commits

---

## 🌐 Public Analyses

**URL:** `/analyses/`  
**No login required.**

Lists all completed single-repository FDS analyses that have been marked as public. You can browse results from any analysis shared by any user.

> **Relevance to your essay:** If you run a single-repo FDS analysis on a real project (e.g., the GitHub repo of a developer team), the public analyses list lets professors access and verify your results without an account.

---

## 📊 FDS Analysis — Single Repository (Optional)

**URL:** `/create-analysis/`  
**Login required.**

This is the original feature of the application, allowing analysis of a **single GitHub repository** by providing a GitHub URL and API token.

### When would you use this?

- If you want to show what FDS scores look like on a real open-source project
- If you want to compare the FDS methodology against your A/B experiment results
- For demonstration purposes in a paper appendix

### Workflow

1. Sign in (or register — no email verification required)
2. Go to **Create Analysis**
3. Enter a GitHub repository URL (e.g., `https://github.com/numpy/numpy`)
4. Enter your GitHub Personal Access Token (needed to fetch commit history via the API)
5. Optionally choose a **Parameter Set** (see below)
6. Submit — the pipeline fetches commits, runs TORQUE clustering, then FDS

The resulting dashboard shows per-developer FDS scores, build timelines, and 6-dimension breakdowns.

> **Note:** This feature requires a valid GitHub token and an internet connection. The A/B experiment feature does **not** require either.

---

## ⚙️ Parameter Sets (Advanced, Optional)

**URL:** `/parameters/`  
**Login required.**

The FDS algorithm uses a set of weights to combine the six effort dimensions and six importance dimensions into a final score. The Parameter Sets feature lets you:

- Create named weight configurations (e.g., "Speed-Focused", "Quality-Focused")
- Save and reuse them across multiple analyses
- Compare results under different weight assumptions

### Default Weights

```
Effort:     Share×base | Scale=0.25 | Reach=0.15 | Centrality=0.20 | Dominance=0.20 | Novelty=0.15 | Speed=0.05
Importance: Scale=0.30 | Scope=0.20 | Centrality=0.15 | Complexity=0.15 | Type=0.10 | Release=0.10
```

### When to mention this in your essay

If your paper discusses the **validity and configurability** of the FDS algorithm, mention that the tool supports researcher-defined weight tuning — this is evidence of the algorithm's adaptability for different research contexts.

---

## 📄 Essay Reference — Which Features to Mention

Here is a concise summary for your IEEE paper, organized by what each feature contributes to your research narrative:

---

### ✅ Must mention: A/B Experiment Feature

> *"We developed a web-based experimental platform — the GenAI Impact & Productivity Analyzer (GIPA) — which accepts two Git commit CSV datasets and applies the Fair Developer Score (FDS) pipeline independently to each cohort. The system computes raw Speed (mean inter-commit interval, `dt_prev_commit_sec`) and Scale (mean effective churn per developer) as the primary comparison metrics, directly testing our hypotheses H1 and H2."*

**Key metrics to cite from the dashboard:**
- Speed Δ% (shown on the ⚡ KPI card)
- Scale Δ% (shown on the 📊 KPI card)
- FDS Score Δ% (shown on the 🏆 KPI card)

---

### ✅ Should mention: FDS Algorithm (the scoring engine)

> *"The underlying productivity scoring uses the Fair Developer Score algorithm, which models developer contribution as Effort × Build Importance across six dimensions each, normalized using Median Absolute Deviation (MAD-z) to resist outliers. Commits are first clustered into logical build units using the TORQUE algorithm before scoring."*

---

### 🔵 Optional mention: Public Analyses

> *"All experiment results are accessible via a public analysis listing, enabling peer verification without account creation — supporting transparency and reproducibility."*

---

### 🔵 Optional mention: Parameter Sets

> *"The platform supports configurable FDS weight parameters, allowing future researchers to adapt the scoring formula to domain-specific productivity definitions."*

---

### ❌ Not necessary to mention: Authentication / User Dashboard / Test Runner

These are infrastructure features for multi-user deployment and are not directly relevant to the research findings.

---

## ❓ FAQ

**Q: The experiment is stuck on "Running" for more than 5 minutes. What do I do?**  
A: Check that your CSV files are well-formed and contain the required 13 columns. Re-upload if needed. If the issue persists, check the server console for a Python error traceback.

**Q: The Speed Δ% is showing a negative number. What does that mean?**  
A: A negative Speed Δ means the GenAI group's mean time between commits is *longer* than the Control group's — i.e., the GenAI group committed less frequently. This would challenge H1.

**Q: Can professors access my results without logging in?**  
A: Yes — share the direct URL of your experiment dashboard, e.g. `http://127.0.0.1:8000/ab-experiment/3/`. No login is needed to view it.

**Q: Can I run multiple experiments with different CSV datasets?**  
A: Yes — each submission creates a new experiment with a unique URL. All experiments are stored in the database.

**Q: Do I need a GitHub token for the A/B experiment?**  
A: No. The A/B experiment feature is entirely CSV-based and does not interact with GitHub at all.
