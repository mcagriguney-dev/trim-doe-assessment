# Trim optimisation: reduced designs and where their optima lie

Data and analysis code for:

> Guney MC, Ince ST. *Assessment of reduced experimental designs for
> CFD-based trim optimisation.* Ships and Offshore Structures, ICSOS 2026 Special Issue.

Extended version of ICSOS2026-18, presented at the 11th International Conference
on Ships and Offshore Structures, Yildiz Technical University, Istanbul,
4-7 October 2026.

## What is here

### `data/`

| File | Rows | Contents |
|---|---|---|
| `S1_reference_datasets.csv` | 167 | Every trim-response value extracted from the seven published reference datasets, with the sign convention of the source and the conversion applied |
| `S2_design_enumeration.csv` | 1639 | Every design-operating-point pair: the subset of trim levels used, whether its range contained the true optimum, the trim it selected and the resulting penalty |
| `S3_screening_runs.csv` | 16 | The sixteen URANS runs of the screening design: ship, trim, draught, speed, total resistance and total resistance coefficient |
| `S4_hull_coefficients.csv` | 4 | Block coefficients of the whole hull and of its thirds and halves, computed from the hull surface models at the design draught |

Trim sign convention throughout: **positive = trim by the bow**. The seven source
studies do not use a common convention; `S1` records each source's own convention
and the conversion applied, so the raw published values remain recoverable.

Resistance in `S3` is in kN and the coefficient is given as C_T x 10^3.

### `code/`

| File | Purpose |
|---|---|
| `altkume_analizi.py` | Loads the seven reference datasets, locates the true optimum of each operating point, evaluates a reduced design against it |
| `tam_altkume.py` | Exhaustive enumeration of every subset of every dataset's trim levels (296 designs, 1639 design-operating-point pairs) |
| `sekiller.py` | Regenerates every figure in the paper |
| `ittc78.py` | ITTC-57/78 decomposition and consistency check of the sixteen CFD runs |
| `ek_malzeme.py` | Rebuilds the supplementary CSVs from the analysis |
| `crossref_dogrula.py` | Cross-checks every reference in the paper against the publisher's own Crossref record |
| `uc_parca_cb.py` | Block coefficients of the whole hull and of its longitudinal parts, from the hull surface models |
| `govde_hacim.py` | Longitudinal distribution of immersed volume, and the displacement check against the published particulars |
| `referans_kontrol.py` | Builds a per-reference folder pairing each citation with its source |

### `figures/`

The figures of the paper as published, at submission resolution.

## Reproducing the analysis

Requires Python 3.9+ and matplotlib.

```
python code/tam_altkume.py      # enumeration, prints the summary tables
python code/ittc78.py           # ITTC-57/78 check of the CFD runs
python code/sekiller.py         # regenerates every figure
```

`altkume_analizi.py` is imported by the other two and can also be run on its own.

## What is not here

The hull geometries and hydrostatic datasets of the four vessels are commercial
property of their owners and are not redistributed. The CFD results computed from
them are in `S3_screening_runs.csv`.

## Repository

https://github.com/mcagriguney-dev/trim-doe-assessment

## Citing

Please cite the journal article above. The reference datasets in `S1` belong to
their original authors and are cited individually in the paper; if you use them,
cite the original source as well.
