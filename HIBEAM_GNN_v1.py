#!/usr/bin/env python3
from pathlib import Path
from glob import glob
import os, re, json, sys, traceback
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import torch
from torch.optim import Adam

from graphnet.data import GraphNeTDataModule
from graphnet.data.dataset import ParquetDataset
from graphnet.models.graphs import KNNGraph
from graphnet.models.gnn import DynEdge
from graphnet.models import StandardModel
from graphnet.models.task.reconstruction import PositionReconstruction
from graphnet.training.loss_functions import LogCoshLoss
from graphnet.training.callbacks import PiecewiseLinearLR

# Hyperparameters / runtime
BATCH_SIZE = 64
MAX_EPOCHS = 30
GPUS       = [0]  # []=CPU, [0]=first GPU; use your environment as needed

# Detector and graph definition
from graphnet.models.detector.detector import Detector
from hibeam_det import HIBEAM_Detector

detector = HIBEAM_Detector()
graph_definition = KNNGraph(detector=detector)

# Utilities
from IPython.display import clear_output

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
    return p

def save_hist(series, title, xlabel, outpath):
    import matplotlib.pyplot as plt
    if series is None or len(series) == 0:
        print(f"[WARN] Empty series for {title}, skipping histogram: {outpath}")
        return
    plt.figure(figsize=(6,4))
    plt.hist(series, bins=50)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()

def safe_read_parquet_list(files):
    dfs = []
    for f in files:
        try:
            dfs.append(pd.read_parquet(str(f)))
        except Exception as e:
            print(f"[WARN] Failed to read {f}: {e}")
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)

def train_and_eval_for_dir(DATA_DIR:str, PRED_DIR, res_tag:str, mul_tag:str, max_epochs=None, folder=None):
    """
    Train on DATA_DIR and run inference on PRED_DIR.
    Returns (out_root: Path, metrics: dict). On failure metrics will include 'failed': True.
    """
    global BATCH_SIZE, MAX_EPOCHS, GPUS
    if max_epochs is None:
        max_epochs = MAX_EPOCHS

    # Normalize inputs
    DATA_DIR = str(DATA_DIR)
    PRED_DIR = str(PRED_DIR)

    # Setup output root
    folder_name = folder or "default"
    # Try to find particle directory segment, else fallback to 'flat'
    try:
        seg = next((seg for seg in Path(DATA_DIR).parts if seg.startswith("particles_")), "flat")
    except Exception:
        seg = "flat"
    out_root = ensure_dir(Path("results") / folder_name / seg / res_tag)

    # Default metrics in case of early failure
    metrics = {
        "mean_abs_dx": np.nan,
        "mean_abs_dy": np.nan,
        "mean_abs_dz": np.nan,
        "mean_dist_residual": np.nan,
        "n_events": 0,
        "data_dir": DATA_DIR,
        "pred_dir": PRED_DIR,
        "res_tag": res_tag,
        "mul_tag": mul_tag,
        "failed": False,
        "error": ""
    }

    try:
        # 1) Data
        features = ["dom_x", "dom_y", "dom_z", "dom_t"]
        truth    = ["position_x", "position_y", "position_z"]

        if not Path(DATA_DIR).exists():
            raise FileNotFoundError(f"Training data dir not found: {DATA_DIR}")

        dm = GraphNeTDataModule(
            dataset_reference=ParquetDataset,
            dataset_args={
                "path": DATA_DIR,
                "pulsemaps": ["pulses"],
                "truth_table": "truth",
                "features": features,
                "truth": truth,
                "graph_definition": graph_definition,
                "index_column": "event_id",
            },
            train_dataloader_kwargs={"batch_size": BATCH_SIZE, "num_workers": 2,"persistent_workers": True,"pin_memory": False},
        )
        train_loader = dm.train_dataloader
        val_loader   = dm.val_dataloader

        # 2) Model
        backbone = DynEdge(
            nb_inputs=graph_definition.nb_outputs,
            global_pooling_schemes=["min", "max", "mean", "sum"],
        )
        task = PositionReconstruction(
            hidden_size=backbone.nb_outputs,
            target_labels=["position_x", "position_y", "position_z"],
            loss_function=LogCoshLoss(),
        )
        model = StandardModel(
            graph_definition=graph_definition,
            backbone=backbone,
            tasks=[task],
            optimizer_class=Adam,
            optimizer_kwargs={"lr": 1e-3},
            scheduler_class=PiecewiseLinearLR,
            scheduler_kwargs={
                "milestones": [0, max(1, len(train_loader)//2), max(2, len(train_loader)*20)],
                "factors": [1e-2, 1, 1e-2],
            },
            scheduler_config={"interval": "step"},
        )

        # 3) Train
        clear_output(wait=True)
        model.fit(
            train_loader,
            val_loader,
            gpus=None if not GPUS else GPUS,
            distribution_strategy="auto",
            max_epochs=max_epochs,
            early_stopping_patience=5,
        )

        # 4) Predict
        from torch_geometric.loader import DataLoader as PyGDataLoader
        clear_output(wait=True)

        if not Path(PRED_DIR).exists():
            raise FileNotFoundError(f"Inference data dir not found: {PRED_DIR}")

        dataset = ParquetDataset(
            path = str(PRED_DIR),
            pulsemaps=["pulses"],
            truth_table="truth",
            features=features,
            truth=truth,
            graph_definition=graph_definition,
            index_column="event_id",
        )
        inference_loader = PyGDataLoader(dataset, batch_size=BATCH_SIZE, num_workers=2, shuffle=False, persistent_workers=True, pin_memory=False)

        predictions = model.predict_as_dataframe(
            inference_loader,
            additional_attributes=["event_id"],
            gpus=GPUS,
        )

        # Ensure output dir exists
        ensure_dir(out_root)
        # Write parquet safely
        try:
            predictions.to_parquet(out_root / "predictions.parquet", index=False)
        except Exception as e:
            # fallback: write csv
            print(f"[WARN] Failed to write parquet: {e}. Writing CSV fallback.")
            predictions.to_csv(out_root / "predictions.csv", index=False)

        # 5) Merge and metrics
        clear_output(wait=True)
        truth_files = sorted(Path(PRED_DIR, "truth").glob("truth_*.parquet"))
        if not truth_files:
            raise FileNotFoundError(f"No truth parquet files found in {Path(PRED_DIR,'truth')}")

        truth_df = safe_read_parquet_list(truth_files)
        if truth_df.empty:
            raise ValueError("Truth dataframe is empty after reading parquet files.")

        # Merge predictions and truth
        merged = predictions.merge(truth_df, on="event_id", how="inner")
        if merged.empty:
            print("[WARN] Merged predictions with truth yielded 0 rows.")
            # still record metrics with n_events = 0
            metrics.update({
                "n_events": 0,
            })
            # write empty merged for debugging
            try:
                merged.to_csv(out_root / "merged_empty.csv", index=False)
            except Exception:
                pass
            return out_root, metrics

        # compute residuals only if predicted and truth columns exist
        required_pred = {"position_x_pred", "position_y_pred", "position_z_pred"}
        required_truth = {"position_x", "position_y", "position_z"}
        if not required_pred.issubset(merged.columns) or not required_truth.issubset(merged.columns):
            missing = {
                "pred_missing": sorted(list(required_pred - set(merged.columns))),
                "truth_missing": sorted(list(required_truth - set(merged.columns))),
            }
            raise KeyError(f"Missing expected columns for residuals: {missing}")

        merged["dx"] = merged["position_x_pred"] - merged["position_x"]
        merged["dy"] = merged["position_y_pred"] - merged["position_y"]
        merged["dz"] = merged["position_z_pred"] - merged["position_z"]
        merged["dist_residual"] = (merged["dx"]**2 + merged["dy"]**2 + merged["dz"]**2) ** 0.5

        # persist merged and metrics
        try:
            merged.to_csv(out_root / "predictions_and_truth_merged.csv", index=False)
        except Exception as e:
            print(f"[WARN] Failed to write merged csv: {e}")

        metrics = {
            "mean_abs_dx": float(merged["dx"].abs().mean()),
            "mean_abs_dy": float(merged["dy"].abs().mean()),
            "mean_abs_dz": float(merged["dz"].abs().mean()),
            "mean_dist_residual": float(merged["dist_residual"].mean()),
            "n_events": int(len(merged)),
            "data_dir": DATA_DIR,
            "pred_dir": PRED_DIR,
            "res_tag": res_tag,
            "mul_tag": mul_tag,
            "failed": False,
            "error": ""
        }
        (out_root / "metrics.txt").write_text("\n".join(f"{k}: {v}" for k,v in metrics.items()))

        # 6) Plots
        save_hist(merged["dist_residual"], f"Distance residual — {res_tag}", "Residual [m]", out_root/f"hist_dist_residual__{res_tag}.png")
        save_hist(merged["dx"], f"dx — {res_tag}", "dx [m]", out_root/f"hist_dx__{res_tag}.png")
        save_hist(merged["dy"], f"dy — {res_tag}", "dy [m]", out_root/f"hist_dy__{res_tag}.png")
        save_hist(merged["dz"], f"dz — {res_tag}", "dz [m]", out_root/f"hist_dz__{res_tag}.png")

        return out_root, metrics

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[ERROR] train_and_eval_for_dir failed for res={res_tag}, mul={mul_tag}: {e}\n{tb}")
        metrics["failed"] = True
        metrics["error"] = f"{e}"
        # persist failure info
        try:
            (out_root / "metrics_failed.txt").write_text(f"error: {e}\n\ntraceback:\n{tb}")
        except Exception:
            pass
        return out_root, metrics


# Discover smeared datasets and run
def main():
    #### Please fix all these input output directories before run!
    training_set = "training"
    validation_set = "validation"
    sample_size = "250k"
    folder_name = f"{training_set}_{validation_set}_{sample_size}" # folder name after traing & validation set of data!

    if validation_set == "validation":
        validation_folder_name = "vertex_random"
    elif validation_set == "training":
        validation_folder_name = ""

    BASE = Path(f"Large_data/{training_set}_data_smeared")
    if not BASE.exists():
        print(f"[ERROR] Base directory does not exist: {BASE}")
        return

    res_dirs = sorted([p for p in BASE.glob("*/res_*cm") if p.is_dir()])
    if not res_dirs:
        print(f"[ERROR] No resolution dirs found under {BASE}. Found: {list(BASE.iterdir())}")
        return

    all_metrics = []
    for p in res_dirs:
        res_tag = p.name  # e.g., res_0.1cm
        mul_tag = p.parent.name
        data_dir = str(p) # where the training data come from?
        pred_dir = Path(str(p).replace(f"{training_set}_data_smeared", f"{validation_set}_data_smeared/{validation_folder_name}"))

        print(f"\n=== Training for {res_tag} ===\nData: {data_dir}\nPredict on: {pred_dir}")
        out_dir, metrics = train_and_eval_for_dir(data_dir, pred_dir, res_tag, mul_tag, max_epochs=MAX_EPOCHS, folder=folder_name)
        all_metrics.append(metrics)
        print(f"Saved outputs to {out_dir}; metrics: failed={metrics.get('failed',False)} n_events={metrics.get('n_events',0)}")

    # Build DataFrame safely
    metrics_df = pd.DataFrame(all_metrics)
    # Ensure columns for sorting exist; if not, add placeholders so sort won't KeyError
    if "res_tag" not in metrics_df.columns:
        metrics_df["res_tag"] = ""
    if "mul_tag" not in metrics_df.columns:
        metrics_df["mul_tag"] = ""
    try:
        metrics_df = metrics_df.sort_values(["res_tag", "mul_tag"])
    except Exception as e:
        print(f"[WARN] Sorting metrics failed: {e}")

    results_root = ensure_dir(Path("results")/folder_name)
    summary_path = results_root / "summary_metrics.csv"
    try:
        metrics_df.to_csv(summary_path, index=False)
        print(f"[INFO] Wrote summary metrics to {summary_path}")
    except Exception as e:
        print(f"[WARN] Failed to write summary metrics: {e}")

    # Return metrics_df for interactive use
    return metrics_df


if __name__ == "__main__":
    # Ensure safe multiprocessing when using DataLoader workers / Lightning spawning.
    import torch.multiprocessing as mp
    try:
        mp.set_start_method("spawn", force=True)
    except RuntimeError:
        # It's fine if the start method was already set.
        pass
    df = main()
    # If you run interactively, this will print summary
    if isinstance(df, pd.DataFrame):
        print(df.head())

