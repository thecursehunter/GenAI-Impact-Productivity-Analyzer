"""
ABExperimentService
====================
Runs the complete FDS pipeline independently on two pre-clustered CSV files
(Control group and GenAI group) and persists all per-developer scores and
group-level aggregate statistics needed for the A/B comparison dashboard.

Hypothesis targeted:
  H1 – GenAI reduces mean time-between-commits (speed_sec ↓ is better)
  H2 – GenAI increases total lines of functional code produced (churn ↑ is better)
"""

import sys
import threading
import time
import pandas as pd
from pathlib import Path
from django.utils import timezone as django_timezone


class ABExperimentService:
    """Run A/B experiment analysis in a background thread."""

    def start_experiment(self, experiment_id: int):
        """Kick off analysis in a daemon thread so the HTTP request returns immediately."""
        thread = threading.Thread(target=self._run_experiment, args=(experiment_id,))
        thread.daemon = True
        thread.start()

    # ------------------------------------------------------------------
    # Internal runner
    # ------------------------------------------------------------------

    def _run_experiment(self, experiment_id: int):
        # Late import to avoid circular imports at module load time
        from .models import ABExperiment

        try:
            experiment = ABExperiment.objects.get(id=experiment_id)
            experiment.status = 'running'
            experiment.save(update_fields=['status'])

            control_results = self._run_fds_on_csv(experiment.control_csv_path)
            genai_results = self._run_fds_on_csv(experiment.genai_csv_path)

            self._save_results(experiment, control_results, genai_results)

            experiment.status = 'completed'
            experiment.completed_at = django_timezone.now()
            experiment.save(update_fields=['status', 'completed_at',
                                           'control_total_commits', 'control_developer_count',
                                           'control_mean_fds', 'control_mean_speed_sec', 'control_mean_churn',
                                           'genai_total_commits', 'genai_developer_count',
                                           'genai_mean_fds', 'genai_mean_speed_sec', 'genai_mean_churn'])

        except Exception as exc:  # noqa: BLE001
            try:
                from .models import ABExperiment as _ABE
                exp = _ABE.objects.get(id=experiment_id)
                exp.status = 'failed'
                exp.error_message = str(exc)
                exp.save(update_fields=['status', 'error_message'])
            except Exception:
                pass

    # ------------------------------------------------------------------
    # FDS pipeline runner (single group)
    # ------------------------------------------------------------------

    def _run_fds_on_csv(self, csv_path: str) -> dict:
        """
        Run the full FDS pipeline on a pre-clustered CSV file.

        The CSV is expected to have the agreed schema:
            hash, author_name, author_email, commit_ts_utc, dt_prev_commit_sec,
            files_changed, insertions, deletions, is_merge, dirs_touched,
            file_types, msg_subject, batch_id

        Returns a dict of DataFrames and computed stats.
        """
        from .fds_algorithm.preprocessing.data_processor import DataProcessor
        from .fds_algorithm.effort_calculator.developer_effort import DeveloperEffortCalculator
        from .fds_algorithm.importance_calculator.batch_importance import BatchImportanceCalculator
        from .fds_algorithm.fds_calculator import FDSCalculator

        config = {
            'noise_factor_threshold': 0.1,
            'whitespace_noise_factor': 0.99,
            'vendor_noise_factor': 0.1,
            'key_file_extensions': ['.py', '.js', '.java', '.cpp', '.c', '.h'],
            'pagerank_iterations': 100,
            'pagerank_damping': 0.85,
            'min_churn_for_edge': 2,
            'min_batch_size': 1,
            'min_batch_churn': 1,
            'time_window_days': 365,
            'min_contributions': 1,
            'contribution_threshold': 0.01,
            'novelty_cap': 2.0,
            'speed_half_life_hours': 72,
            'release_proximity_days': 7,
            'complexity_scale_factor': 1.0,
        }

        # ── Load raw CSV (batch_id already present — no TORQUE step needed) ──
        raw_df = pd.read_csv(csv_path)

        # ── Step 1: Preprocessing ──
        processor = DataProcessor(config)
        processed_df = processor.process_data(csv_path)   # takes file path
        
        # Ensure dates are properly parsed for FDS math (prevents string subtraction errors)
        if 'commit_ts_utc' in processed_df.columns:
            processed_df['commit_ts_utc'] = pd.to_datetime(processed_df['commit_ts_utc'])

        # ── Step 2: Developer Effort ──
        effort_calc = DeveloperEffortCalculator(config)
        effort_df = effort_calc.process_all_batches(processed_df)

        # ── Step 3: Batch Importance ──
        importance_calc = BatchImportanceCalculator(config)
        importance_df, _ = importance_calc.process_all_batches(processed_df)

        # ── Step 4: FDS Scores ──
        # Merge on commit hash + batch_id (same pattern as services.py)
        merge_cols = [c for c in ['hash', 'batch_id'] if c in effort_df.columns and c in importance_df.columns]
        merged_df = effort_df.merge(importance_df, on=merge_cols, suffixes=('', '_imp'))

        fds_calc = FDSCalculator(config)
        contributions = fds_calc.calculate_contributions(merged_df)
        fds_scores = fds_calc.aggregate_contributions_by_author(contributions)
        detailed = fds_calc.calculate_detailed_metrics(contributions)

        # ── Compute raw Speed metric: mean dt_prev_commit_sec per developer ──
        # H1 — lower seconds between commits = faster developer
        speed_by_dev = {}
        if 'dt_prev_commit_sec' in raw_df.columns and 'author_email' in raw_df.columns:
            spd = raw_df[['author_email', 'dt_prev_commit_sec']].copy()
            spd['dt_prev_commit_sec'] = pd.to_numeric(spd['dt_prev_commit_sec'], errors='coerce')
            spd = spd.dropna(subset=['dt_prev_commit_sec'])
            if not spd.empty:
                speed_by_dev = spd.groupby('author_email')['dt_prev_commit_sec'].mean().to_dict()

        return {
            'fds_scores': fds_scores,      # DataFrame: author_email, fds, avg_effort, avg_importance, commit_count, total_churn, …
            'detailed': detailed,           # DataFrame: author_email, speed_z_mean, scale_z_mean, …
            'speed_by_dev': speed_by_dev,  # {email: mean_seconds}
            'total_commits': len(processed_df),
            'developer_count': int(processed_df['author_email'].nunique()),
        }

    # ------------------------------------------------------------------
    # Persist results to DB
    # ------------------------------------------------------------------

    def _save_results(self, experiment, control: dict, genai: dict):
        from .models import ABDeveloperScore

        # Save per-developer rows for both groups
        self._save_group_scores(experiment, 'control', control)
        self._save_group_scores(experiment, 'genai', genai)

        # Compute group-level aggregate stats
        def _mean(qs, field):
            vals = [getattr(s, field) for s in qs if getattr(s, field) is not None]
            return sum(vals) / len(vals) if vals else 0.0

        ctrl_devs = experiment.developer_scores.filter(group='control')
        gnai_devs = experiment.developer_scores.filter(group='genai')

        experiment.control_total_commits = control['total_commits']
        experiment.control_developer_count = control['developer_count']
        experiment.control_mean_fds = _mean(ctrl_devs, 'fds_score')
        experiment.control_mean_speed_sec = _mean(ctrl_devs, 'mean_speed_sec')
        experiment.control_mean_churn = _mean(ctrl_devs, 'total_churn')

        experiment.genai_total_commits = genai['total_commits']
        experiment.genai_developer_count = genai['developer_count']
        experiment.genai_mean_fds = _mean(gnai_devs, 'fds_score')
        experiment.genai_mean_speed_sec = _mean(gnai_devs, 'mean_speed_sec')
        experiment.genai_mean_churn = _mean(gnai_devs, 'total_churn')

    def _save_group_scores(self, experiment, group: str, results: dict):
        from .models import ABDeveloperScore

        fds_df = results['fds_scores']
        detailed_df = results['detailed']
        speed_by_dev = results['speed_by_dev']

        if fds_df is None or fds_df.empty:
            return

        # Index detailed by author_email for O(1) lookup
        if detailed_df is not None and not detailed_df.empty and 'author_email' in detailed_df.columns:
            detail_idx = detailed_df.set_index('author_email')
        else:
            detail_idx = pd.DataFrame()

        for _, row in fds_df.iterrows():
            email = str(row.get('author_email', '') or '').strip()
            if not email:
                continue

            d = detail_idx.loc[email] if (not detail_idx.empty and email in detail_idx.index) else None

            def _z(key):
                if d is not None:
                    val = d.get(key) if isinstance(d, dict) else (d[key] if key in d.index else 0)
                    return float(val or 0)
                return 0.0

            ABDeveloperScore.objects.update_or_create(
                experiment=experiment,
                group=group,
                author_email=email,
                defaults=dict(
                    fds_score=float(row.get('fds', 0) or 0),
                    avg_effort=float(row.get('avg_effort', 0) or 0),
                    avg_importance=float(row.get('avg_importance', 0) or 0),
                    total_commits=int(row.get('commit_count', 0) or 0),
                    total_churn=float(row.get('total_churn', 0) or 0),
                    mean_speed_sec=float(speed_by_dev.get(email, 0) or 0),
                    speed_z_mean=_z('speed_z_mean'),
                    scale_z_mean=_z('scale_z_mean'),
                    reach_z_mean=_z('reach_z_mean'),
                    centrality_z_mean=_z('centrality_z_mean'),
                    dominance_z_mean=_z('dominance_z_mean'),
                    novelty_z_mean=_z('novelty_z_mean'),
                )
            )
