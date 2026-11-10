# Abaqus input files — Casing collapse in Gachsaran salt (Sirri-E vs Marun)

Numerical model inputs accompanying the manuscript

> Kalhori, M. *Casing collapse in creeping Gachsaran salt: why cement-sheath defects control failure time at Sirri-E and Marun* (submitted to *Rock Mechanics and Rock Engineering*).

This repository contains every Abaqus/Standard input deck (`.inp`) used to produce the results, figures and tables in the paper, so that reviewers and readers can inspect or re-run the models.

## Contents

| Folder | Models | Files | Used in the paper |
|---|---|---|---|
| `1_2D_plane_strain/` | Plane-strain casing–cement–salt discs (R = 16 m): intact and defective cement, four creep laws, three in-situ stress states, solver/option checks | 30 | Figs. 4–9 |
| `2_verification/` | Open hole (analytical check), coarse/fine mesh, pressure-boundary, time-step (CETOL) variants | 8 | Fig. 3; Table 5 |
| `3_quarter_3D/` | Quarter-symmetric 3D models (100 m), void length 2–100 m, water/mud/full-ring voids, incl. restart decks | 23 | Figs. 10–11; Table 6 |
| `4_layered_column/` | 600 m layered column at Sirri-E (salt/anhydrite/marl, frictionless interfaces), S0 and S2 | 3 | Fig. 12 |
| `5_delayed_defects_Marun/` | Defect activated 5/10/20 yr after installation (2D) and 10 yr (3D, 10 m void) | 4 | Fig. 13; Table 7 |
| `6_delayed_defects_SirriE/` | Late void (T1) and fluid loss (T2) triggered at 5/10/20 yr (2D) and 10 yr (3D) | 8 | Fig. 13; Table 7 |

`file_list.csv` lists every file with its group, size and SHA-256 checksum. `SHA256SUMS.txt` contains the same checksums in `sha256sum` format.

## Software and units

* Abaqus/Standard 2022 (decks generated with Abaqus/CAE 2022 and then edited by script). No user subroutines are required.
* Consistent units: **N, mm, MPa, s** (time in seconds; 1 yr = 3.15576e7 s).
* Salt creep: `*Creep, law=TIME` (power law, n = 3). Cement: Mohr–Coulomb with tension cut-off (4.83 MPa). Casing: elastic–plastic steel, E = 206 GPa.
* All models start from an initial casing ovality of 0.3 % (applied by nodal perturbation; see deck header).

Each deck begins with comment lines (`**`) recording the scripted modifications applied after CAE export (solution controls, initial ovality, stabilisation, trigger time, etc.) and a one-line description `field | stress state | creep law | defect`.

## File-naming key

| Code | Meaning |
|---|---|
| `SH` | Sirri-E (shallow, 1585 m) |
| `DP` | Marun (deep, 3450 m) |
| `S0`, `S1`, `S2` | In-situ stress state: isotropic (K = 1), and the two anisotropic cases defined in Table 4 |
| `TAH`, `GOR`, `BGR`, `MAX` | Salt creep law: Taheri, Gorjian, BGRa, Maxwell-type (Table 4) |
| `INT` | Intact cement sheath |
| `V90W`, `V90M` | 90° cement void filled with water / drilling mud |
| `RINGM` | 360° mud-filled ring (no cement over the void length) |
| `L02` … `L100` | Void length along the well, m (3D models) |
| `Q3` | Quarter-symmetric 3D model |
| `Q5S` … `_NS` | Layered 3D column, frictionless sliding interfaces, no separation |
| `N8T1`, `N8T2` | Delayed defect: T1 = late void, T2 = fluid loss from a mud-filled void |
| `5S`, `10S`, `20S` | Defect trigger time after casing installation, years |
| `OH` | Open hole (no casing/cement) — verification against the analytical closure solution |
| `MC`, `MF` | Coarse / fine mesh (mesh-convergence study) |
| `PB` | Pressure (instead of pinned) outer boundary |
| `DTH`, `DTD` | Creep tolerance (CETOL) halved / doubled |
| `_R` (2D S2 models) | Borehole pre-filled with soft elements (E = 1 MPa, removed at installation) to equilibrate the anisotropic initial stress |
| `T1_UNSYMM`, `T4DP_NOTC` | Solver checks: default time incrementation; Marun model without the cement tension cut-off |

## Running the models

```bat
abaqus job=SH_S0_TAH_V90W input=SH_S0_TAH_V90W.inp cpus=4 interactive
```

### Restart chains

Some long 3D runs were continued from restart files. The restart decks (`*_R.inp`, `*_R_R.inp`, …) contain only `*Restart, read` and the remaining steps; they must be run **after** their parent job, from the same folder, with `oldjob`:

```bat
abaqus job=Q3_DP_V90W_L10       cpus=4 interactive
abaqus job=Q3_DP_V90W_L10_R     oldjob=Q3_DP_V90W_L10     cpus=4 interactive
abaqus job=Q3_DP_V90W_L10_R_R   oldjob=Q3_DP_V90W_L10_R   cpus=4 interactive
abaqus job=Q3_DP_V90W_L10_R_R_R oldjob=Q3_DP_V90W_L10_R_R cpus=4 interactive
```

| Parent | Restart chain |
|---|---|
| `Q3_DP_V90W_L10` | `_R` → `_R_R` → `_R_R_R` |
| `Q3_DP_V90W_L30` | `_R` → `_R_R` |
| `Q3_DP_V90M_L30` | `_R` |
| `Q3_SH_V90W_L30` | `_R` → `_R_R` |
| `Q5S_SH_S2_V90W_NS` | `_R` |

Each restart deck states in its header the step and increment from which it continues.

### Load history

All models use the same step sequence (Fig. 2 of the paper):

| Step | Procedure | Duration |
|---|---|---|
| `Init` | `*Static` — in-situ stress equilibrium, casing/cement deactivated | — |
| `Drill` | `*Static` — borehole excavation, mud pressure applied | — |
| `OpenHole` | `*Visco` — open-hole salt creep | 3 d |
| `Install` | `*Static` — casing and cement activated (`*Model Change, add`) | — |
| `Prod1` | `*Visco` — production | 10 yr |
| `Shut` | `*Visco` — shut-in | 0.5 yr |
| `Prod2` | `*Visco` — production | 19.5 yr |

In the delayed-defect models (`N8`) a `Trigger` step is inserted at the trigger time (5, 10 or 20 yr after installation); it removes the cement in the void region (`*Model Change, remove`) and applies the void pressure, and the remaining creep steps are stabilised (`stabilize`, line search).

## Post-processing

Ovality is computed as |ΔD_v − ΔD_h| / ID₀ with ID₀ = 216.79 mm, from the displacements of the inner casing nodes. Collapse is defined as 20 % ovality.

## License

The input files are released under the Creative Commons Attribution 4.0 International licence (CC BY 4.0). See `LICENSE`.

## Citation

If you use these files, please cite the paper (citation will be updated on acceptance) and this dataset (see `CITATION.cff`).

## Contact

Mehran Kalhori — Petroleum Geology Research Group, Research Institute of Applied Sciences (ACECR), Tehran, Iran. ORCID: [0000-0002-5319-6161](https://orcid.org/0000-0002-5319-6161)
