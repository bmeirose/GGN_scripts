import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(1)
BASE_DIR = Path("large_training_data")

R_INNER, R_OUTER = 0.22, 0.32
N_LAYERS = 10
LAYER_RADII = np.linspace(R_INNER, R_OUTER, N_LAYERS)
TPC_HALF_LENGTH = 0.516 / 2.0

MUON_MASS = 105.658  # MeV
C = 299_792_458.0    # m/s

N_FILES = 50
EVENTS_PER_FILE = 5000
PARTICLES_CHOICES = [3]  # [2,3, 4, 5 , 10, 20, 30]
EPS = 1e-9
MIN_HITS_PER_EVENT = 3            # <── require at least this many hits

for n_particles in PARTICLES_CHOICES:
    print(f"\n=== Generating dataset for {n_particles} particles per event ===")

    # separate output directory for this case
    DATA_DIR = BASE_DIR / f"particles_{n_particles}"
    (DATA_DIR / "pulses").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "truth").mkdir(parents=True, exist_ok=True)

    global_event_id = 0

    for index in range(N_FILES):
        pulses_rows, truth_rows = [], []

        accepted = 0
        attempts = 0
        max_attempts = EVENTS_PER_FILE * 50  # safety guard

        while accepted < EVENTS_PER_FILE and attempts < max_attempts:
            attempts += 1

            # --- vertex -------------------------------------------------
            r   = rng.uniform(0, 0.2)
            phi = rng.uniform(0, 2*np.pi)
            x0, y0 = r*np.cos(phi), r*np.sin(phi)
            z0  = rng.uniform(-0.004, 0.004)

            # collect hits for THIS event locally first
            event_pulses = []

            # --- particles ----------------------------------------------
            for _ in range(n_particles):
                phi   = rng.uniform(0, 2*np.pi)
                theta = rng.uniform(0, np.pi/4)
                direction = np.array([
                    np.cos(phi) * np.cos(theta),
                    np.sin(phi) * np.cos(theta),
                    rng.choice([-1, 1]) * np.sin(theta),
                ])

                KE     = rng.uniform(200, 800)
                gamma  = (KE + MUON_MASS) / MUON_MASS
                beta   = np.sqrt(1 - 1 / gamma**2)
                speed  = beta * C

                dz = direction[2]
                if   dz > EPS: s_endcap = (TPC_HALF_LENGTH - z0) / dz
                elif dz < -EPS: s_endcap = (-TPC_HALF_LENGTH - z0) / dz
                else:           s_endcap = np.inf
                if s_endcap <= EPS:
                    continue

                dx, dy = direction[0], direction[1]
                a = dx*dx + dy*dy
                for r_layer in LAYER_RADII:
                    b = 2*(x0*dx + y0*dy)
                    c0 = x0*x0 + y0*y0 - r_layer*r_layer
                    if a <= EPS:
                        continue
                    disc = b*b - 4*a*c0
                    if disc <= 0:
                        continue

                    sqrt_disc = np.sqrt(disc)
                    s1 = (-b - sqrt_disc) / (2*a)
                    s2 = (-b + sqrt_disc) / (2*a)
                    candidates = [s for s in (s1, s2) if s > EPS]
                    if not candidates:
                        continue

                    s_layer = min(candidates)
                    if s_layer - s_endcap > EPS:
                        continue

                    x_hit = x0 + dx*s_layer
                    y_hit = y0 + dy*s_layer
                    z_hit = z0 + dz*s_layer
                    if abs(z_hit) - TPC_HALF_LENGTH > 1e-6:
                        continue

                    t_hit = (s_layer / speed) * 1e9  # ns
                    event_pulses.append({
                        "event_id": global_event_id,   # tentative; finalized on accept
                        "dom_x": x_hit,
                        "dom_y": y_hit,
                        "dom_z": z_hit,
                        "dom_t": t_hit,
                    })

            # ---------- accept / reject the event ------------------------
            if len(event_pulses) >= MIN_HITS_PER_EVENT:
                # finalize event_id into rows and append
                for row in event_pulses:
                    row["event_id"] = global_event_id
                pulses_rows.extend(event_pulses)

                truth_rows.append({
                    "event_id": global_event_id,
                    "position_x": x0,
                    "position_y": y0,
                    "position_z": z0,
                })

                global_event_id += 1
                accepted += 1
            # else: reject and try another event (no writes, no id increment)

        if accepted < EVENTS_PER_FILE:
            print(f"  [WARN] Only accepted {accepted}/{EVENTS_PER_FILE} events in file {index} after {attempts} attempts.")

        pd.DataFrame(pulses_rows).to_parquet(DATA_DIR/"pulses"/f"pulses_{index}.parquet")
        pd.DataFrame(truth_rows ).to_parquet(DATA_DIR/"truth"/f"truth_{index}.parquet")
        print(f"  File {index} written to", DATA_DIR.resolve(), f"(accepted {accepted} events)")

import numpy as np
import pandas as pd
from pathlib import Path

# ------------------------------------------------------------------
# configuration
# ------------------------------------------------------------------
BASE_DIR = Path("large_validation_data/vertex_random/")            # base output folder
PARTICLES_CHOICES = [3] #2, 3, 4, 5              # one dataset per value

N_FILES = 50
EVENTS_PER_FILE = 500
MIN_HITS_PER_EVENT = 3                        # <── require at least this many hits
target_radius = 0.2

# detector geometry
R_INNER, R_OUTER = 0.22, 0.32      # m
N_LAYERS = 5
LAYER_RADII = np.linspace(R_INNER, R_OUTER, N_LAYERS)
TPC_HALF_LENGTH = 0.516 / 2.0      # m

MUON_MASS = 105.658                # MeV
C = 299_792_458.0                  # m/s
EPS = 1e-9

# ------------------------------------------------------------------
# generate one dataset per particle multiplicity
# ------------------------------------------------------------------
for n_particles in PARTICLES_CHOICES:
    print(f"\n=== Generating validation dataset for {n_particles} particles/event ===")

    # separate output directory for this case
    DATA_DIR = BASE_DIR / f"particles_{n_particles}"
    (DATA_DIR / "pulses").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "truth").mkdir(parents=True, exist_ok=True)

    # independent, reproducible RNG per dataset
    rng = np.random.default_rng(1 + n_particles)

    global_event_id = 0  # counter spanning all files (reset per dataset)

    for index in range(N_FILES):
        pulses_rows, truth_rows = [], []

        accepted = 0
        attempts = 0
        max_attempts = EVENTS_PER_FILE * 50  # safety guard to avoid infinite loops

        while accepted < EVENTS_PER_FILE and attempts < max_attempts:
            attempts += 1

            # ---------- vertex -----------------------------------------
            r   = rng.uniform(0, target_radius)
            phi = rng.uniform(0, 2*np.pi)
            x0, y0 = r*np.cos(phi), r*np.sin(phi)
            z0  = rng.uniform(-0.004, 0.004)                # ±0.4 cm

            # collect hits for THIS event locally first
            event_pulses = []

            # ---------- particles --------------------------------------
            for _ in range(n_particles):
                # direction
                phi   = rng.uniform(0, 2*np.pi)
                theta = rng.uniform(0, np.pi/4)
                direction = np.array([
                    np.cos(phi) * np.cos(theta),
                    np.sin(phi) * np.cos(theta),
                    rng.choice([-1, 1]) * np.sin(theta),
                ])

                # speed from kinetic energy
                KE = rng.uniform(200, 800)      # MeV
                gamma = (KE + MUON_MASS) / MUON_MASS
                beta = np.sqrt(1 - 1/gamma**2)
                speed = beta * C

                # distance to nearest endcap
                dz = direction[2]
                if   dz > EPS: s_endcap = (TPC_HALF_LENGTH - z0) / dz
                elif dz < -EPS: s_endcap = (-TPC_HALF_LENGTH - z0) / dz
                else:           s_endcap = np.inf
                if s_endcap <= EPS:
                    continue

                # hit positions for each cylindrical layer
                dx, dy = direction[0], direction[1]
                a = dx*dx + dy*dy
                for r_layer in LAYER_RADII:
                    b = 2*(x0*dx + y0*dy)
                    c = x0*x0 + y0*y0 - r_layer*r_layer
                    if a <= EPS:
                        continue
                    disc = b*b - 4*a*c
                    if disc <= 0:
                        continue
                    sqrt_disc = np.sqrt(disc)
                    s_candidates = [
                        (-b - sqrt_disc) / (2*a),
                        (-b + sqrt_disc) / (2*a),
                    ]
                    s_layer = min([s for s in s_candidates if s > EPS], default=None)
                    if s_layer is None or s_layer - s_endcap > EPS:
                        continue

                    x_hit = x0 + dx*s_layer
                    y_hit = y0 + dy*s_layer
                    z_hit = z0 + dz*s_layer
                    if abs(z_hit) - TPC_HALF_LENGTH > 1e-6:
                        continue

                    t_hit = (s_layer / speed) * 1e9  # ns
                    event_pulses.append({
                        "event_id": global_event_id,  # tentative; finalized on accept
                        "dom_x": x_hit,
                        "dom_y": y_hit,
                        "dom_z": z_hit,
                        "dom_t": t_hit,
                    })

            # ---------- accept / reject the event ----------------------
            if len(event_pulses) >= MIN_HITS_PER_EVENT:
                # stamp the final event_id and append
                for row in event_pulses:
                    row["event_id"] = global_event_id
                pulses_rows.extend(event_pulses)

                truth_rows.append({
                    "event_id": global_event_id,
                    "position_x": x0,
                    "position_y": y0,
                    "position_z": z0,
                })

                global_event_id += 1
                accepted += 1
            # else: reject & retry

        if accepted < EVENTS_PER_FILE:
            print(f"  [WARN] Only accepted {accepted}/{EVENTS_PER_FILE} events in file {index} after {attempts} attempts.")

        pd.DataFrame(pulses_rows).to_parquet(DATA_DIR/"pulses"/f"pulses_{index}.parquet")
        pd.DataFrame(truth_rows ).to_parquet(DATA_DIR/"truth"/f"truth_{index}.parquet")
        print(f"  File {index} written to", DATA_DIR.resolve(), f"(accepted {accepted} events)")

print("\nAll validation datasets generated.")

import numpy as np, pandas as pd, shutil
from pathlib import Path
from typing import Iterable, Optional

# ------------------------------------------------------------
# TPC geometry (meters) — must match generation step
# ------------------------------------------------------------
R_INNER, R_OUTER = 0.22, 0.32
TPC_HALF_LENGTH = 0.516 / 2.0

def smear_hits_df(df: pd.DataFrame, sigma_cm: float, clip_to_tpc: bool = True,
                  rng: Optional[np.random.Generator] = None) -> pd.DataFrame:
    """
    Apply 3D Gaussian smearing (per-axis) to dom_x, dom_y, dom_z (in meters).
    sigma_cm is converted to meters internally.
    """
    if rng is None:
        rng = np.random.default_rng(12345)
    sigma_m = sigma_cm / 100.0

    out = df.copy()
    for comp in ("dom_x", "dom_y", "dom_z"):
        if comp not in out.columns:
            raise ValueError(f"Column {comp} not found in pulses dataframe.")
        out[comp] = out[comp] + rng.normal(loc=0.0, scale=sigma_m, size=len(out))

    if clip_to_tpc:
        # Clip cylindrical radius while preserving the azimuth
        r = np.sqrt(out["dom_x"]**2 + out["dom_y"]**2)
        theta = np.arctan2(out["dom_y"], out["dom_x"])
        r = np.clip(r, R_INNER, R_OUTER)
        out["dom_x"] = r * np.cos(theta)
        out["dom_y"] = r * np.sin(theta)
        # Clip z
        out["dom_z"] = np.clip(out["dom_z"], -TPC_HALF_LENGTH, TPC_HALF_LENGTH)

    return out

def _list_datasets(in_base: Path):
    """
    Detect input layout.
    Returns a list of tuples: (dataset_tag, pulses_dir, truth_dir)

    - Flat layout:
        dataset_tag == "" (empty)
        pulses: in_base/pulses
        truth : in_base/truth

    - Per-multiplicity layout:
        dataset_tag == "particles_<N>"
        pulses: in_base/particles_<N>/pulses
        truth : in_base/particles_<N>/truth
    """
    in_base = Path(in_base)
    flat_pulses = in_base / "pulses"
    flat_truth  = in_base / "truth"

    datasets = []

    # Prefer per-multiplicity if present
    particle_dirs = sorted([p for p in in_base.glob("particles_*") if p.is_dir()])
    if particle_dirs:
        for pdir in particle_dirs:
            p_pulses = pdir / "pulses"
            p_truth  = pdir / "truth"
            if p_pulses.exists() and list(p_pulses.glob("pulses_*.parquet")) \
               and p_truth.exists()  and list(p_truth.glob("truth_*.parquet")):
                datasets.append((pdir.name, p_pulses, p_truth))

    # Otherwise fall back to flat
    elif flat_pulses.exists() and list(flat_pulses.glob("pulses_*.parquet")) \
         and flat_truth.exists()  and list(flat_truth.glob("truth_*.parquet")):
        datasets.append(("", flat_pulses, flat_truth))

    if not datasets:
        raise FileNotFoundError(
            "No input datasets found.\n"
            "Expected either:\n"
            "  - flat: <in_base>/pulses/pulses_*.parquet and <in_base>/truth/truth_*.parquet\n"
            "  - per multiplicity: <in_base>/particles_*/{pulses,truth}/... ."
        )
    return datasets

def write_smeared_datasets(
    resolutions_cm: Iterable[float],
    in_base: str,
    out_base: str,
    overwrite: bool = False,
    copy_truth: bool = True,
    clip_to_tpc: bool = True,
    seed: int = 12345,
):
    """
    For each input dataset and each resolution (in cm), write smeared copies of pulses parquet files.

    Input (auto-detected):
      - Flat:           <in_base>/{pulses,truth}/
      - Per multiplicity: <in_base>/particles_*/{pulses,truth}/

    Output (mirrors input; inserts res_<v>cm level):
      - Flat:           <out_base>/res_<v>cm/{pulses,truth}/
      - Per multiplicity: <out_base>/<particles_X>/res_<v>cm/{pulses,truth}/
    """
    in_base = Path(in_base)
    out_base = Path(out_base)
    rng = np.random.default_rng(seed)

    datasets = _list_datasets(in_base)

    for tag, pulses_dir, truth_dir in datasets:
        tag_msg = tag or "(flat dataset)"
        print(f"\n=== Smearing dataset: {tag_msg} ===")
        parquet_files = sorted(pulses_dir.glob("pulses_*.parquet"))
        if not parquet_files:
            print(f"  No pulses found in {pulses_dir}, skipping.")
            continue

        for res in resolutions_cm:
            res_tag = f"res_{res}cm"
            # Build output path, mirroring input structure
            out_root = (out_base / tag) if tag else out_base
            out_dir = out_root / res_tag
            out_pulses = out_dir / "pulses"
            out_truth  = out_dir / "truth"
            out_pulses.mkdir(parents=True, exist_ok=True)
            out_truth.mkdir(parents=True, exist_ok=True)

            print(f"  -> Writing {res_tag} to {out_dir.resolve()}")

            # Copy truth tables (unchanged)
            if copy_truth:
                for truth_path in sorted(truth_dir.glob("truth_*.parquet")):
                    dst = out_truth / truth_path.name
                    if overwrite or not dst.exists():
                        shutil.copy2(truth_path, dst)

            # Create smeared pulses
            for p in parquet_files:
                df = pd.read_parquet(p)
                df_sm = smear_hits_df(df, sigma_cm=float(res),
                                      clip_to_tpc=clip_to_tpc, rng=rng)
                dst = out_pulses / p.name
                if overwrite or not dst.exists():
                    df_sm.to_parquet(dst)

            # Write simple metadata
            meta = {
                "resolution_cm": float(res),
                "sigma_m": float(res) / 100.0,
                "clip_to_tpc": bool(clip_to_tpc),
                "seed": int(seed),
                "source_dir": str(pulses_dir.resolve()),
                "dataset_tag": tag,
            }
            pd.Series(meta).to_json(out_dir / "metadata.json", indent=2)

    print("\nAll smearing tasks complete.")


write_smeared_datasets([0], in_base="large_training_data/", out_base="large_training_data_smeared") #,0.5,1.0
#0, 0.01, 0.1, 0.5, 1.0 
write_smeared_datasets([0], in_base="large_validation_data/vertex_random/", out_base="large_validation_data_smeared/vertex_random/")



