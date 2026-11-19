# -*- coding: utf-8 -*-
"""Gonderim icin ek malzeme paketini uretir (CSV'ler + kod + README + zip)."""
import io, os, csv, shutil, zipfile
from itertools import combinations
import altkume_analizi as A

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CIK = os.path.join(KOK, 'gonderim', 'supplementary')
if os.path.isdir(CIK):
    shutil.rmtree(CIK)
os.makedirs(CIK)

KAYNAK = {
 'Vasilev vd. 2024 - RO-RO 158 m, tam olcek CFD': 'Vasilev et al. (2024), Tables 8-9',
 'Kim vd. 2015 - 6500 TEU konteyner, model deneyi': 'Kim et al. (2015), Table 2',
 'Kim vd. 2015 - Capesize dokme yuk, model deneyi': 'Kim et al. (2015), Table 3',
 'Ziylan & Nas 2022 - 2478 TEU konteyner, model deneyi (ITTC-78)':
     'Ziylan and Nas (2022), Tables 5-6',
 'Shivachev vd. 2017 - KCS 1:75, Fn 0.26': 'Shivachev et al. (2017), Table 7',
 'Korkmaz vd. 2023 - RoPax, model deneyi, 17 kn': 'Korkmaz et al. (2023), Table 10',
 'Martic vd. 2024 - KCS, sig su (h/T 1.78)': 'Martic et al. (2024), Table 9',
}


def yaz(ad, basliklar, satirlar):
    yol = os.path.join(CIK, ad)
    with io.open(yol, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(basliklar)
        w.writerows(satirlar)
    print('%-34s %5d satir' % (ad, len(satirlar)))


# ---------------------------------------------- S1: referans veri setleri
s1 = []
for ds in A.VERI_SETLERI:
    tr = ds['trimler']
    for k, row in ds['veri'].items():
        en_iyi = min(range(len(row)), key=lambda m: row[m])
        for i, v in enumerate(row):
            s1.append([ds['ad'], KAYNAK.get(ds['ad'], ''), str(k), ds['yanit'],
                       tr[i], v, 'yes' if i == en_iyi else 'no', ds['not']])
yaz('S1_reference_datasets.csv',
    ['dataset', 'source_table', 'operating_point', 'response_variable',
     'trim_tau_positive_by_bow', 'response_value', 'is_optimum', 'note'], s1)

# ------------------------------------- S2: butun azaltilmis tasarimlar
s2 = []
for ds in A.VERI_SETLERI:
    tr = ds['trimler']
    n = len(tr)
    opt = {k: min(range(len(v)), key=lambda m: v[m]) for k, v in ds['veri'].items()}
    for boy in range(2, n):
        for sec in combinations(range(n), boy):
            idx = list(sec)
            lo, hi = tr[idx[0]], tr[idx[-1]]
            etiket = ';'.join('%g' % tr[i] for i in idx)
            for k, row in ds['veri'].items():
                g = opt[k]
                j = min(idx, key=lambda m: row[m])
                if ds['yanit'].endswith('[%]'):
                    bedel = row[j] - row[g]
                else:
                    bedel = 100.0 * (row[j] - row[g]) / abs(row[g])
                if g in idx:
                    kat = 'optimum sampled'
                elif lo <= tr[g] <= hi:
                    kat = 'resolution miss'
                else:
                    kat = 'range miss'
                s2.append([ds['ad'], boy, etiket, str(k), tr[g], tr[j],
                           kat, round(bedel, 4)])
yaz('S2_design_enumeration.csv',
    ['dataset', 'n_levels', 'design_levels', 'operating_point',
     'true_optimum_trim', 'selected_trim', 'category', 'penalty_percent'], s2)

# ------------------------------------------- S3: ICSOS 16 koşuluk tasarim
# Tablo 2 ve 3; trim isaretleri makalenin konvansiyonunda (pozitif = basa trim).
ICSOS = [
 (1, 'Neptun', 'container', 1.0, 4.48, 14.38, 19.18, 3.71),
 (2, 'Neptun', 'container', 0.5, 4.91, 13.13, 14.98, 3.31),
 (3, 'Neptun', 'container', 0.0, 3.63, 11.88, 10.77, 3.45),
 (4, 'Neptun', 'container', -0.5, 4.06, 10.63, 6.57, 2.48),
 (5, 'Alfa Sun', 'bulk carrier', 1.0, 6.00, 10.00, 7.16, 2.40),
 (6, 'Alfa Sun', 'bulk carrier', 0.5, 6.40, 11.00, 9.35, 2.49),
 (7, 'Alfa Sun', 'bulk carrier', 0.0, 6.70, 12.00, 12.07, 2.63),
 (8, 'Alfa Sun', 'bulk carrier', -0.5, 7.00, 13.00, 14.67, 2.66),
 (9, 'Ilgaz', 'chemical tanker', 1.0, 5.23, 15.75, 23.75, 3.50),
 (10, 'Ilgaz', 'chemical tanker', 0.5, 4.68, 17.25, 38.85, 5.13),
 (11, 'Ilgaz', 'chemical tanker', 0.0, 6.33, 12.75, 13.72, 2.75),
 (12, 'Ilgaz', 'chemical tanker', -0.5, 5.78, 14.25, 17.97, 3.08),
 (13, 'ELA-S', 'general cargo', 1.0, 5.00, 9.00, 5.79, 2.23),
 (14, 'ELA-S', 'general cargo', 0.5, 5.30, 10.00, 7.44, 2.26),
 (15, 'ELA-S', 'general cargo', 0.0, 5.79, 11.00, 9.54, 2.30),
 (16, 'ELA-S', 'general cargo', -0.5, 6.10, 12.00, 12.93, 2.55),
]
# ICSOS listesindeki R_T, Tablo 3'un eski olceginde (deger x 1e4 N). ITTC-57/78
# ayristirmasi bu olcegin dogrusunun kN oldugunu gosterdi; CSV'ye kN yaziliyor.
ICSOS = [t[:6] + (round(t[6] * 10.0, 1), t[7]) for t in ICSOS]
yaz('S3_screening_runs.csv',
    ['run', 'ship', 'ship_type', 'trim_m_positive_by_bow', 'draught_m',
     'speed_kn', 'RT_kN', 'CT_x1e3'], ICSOS)

# ------------------------------------------------------------- kod
KOD = os.path.join(CIK, 'code')
os.makedirs(KOD)
for f in ('altkume_analizi.py', 'tam_altkume.py', 'sekiller.py', 'ittc78.py',
          'uc_parca_cb.py'):
    shutil.copy(os.path.join(KOK, 'analiz', f), os.path.join(KOD, f))
print('kod: 5 dosya')

# govde katsayilari uc_parca_cb.py tarafindan uretiliyor, oldugu gibi kopyalanir
shutil.copy(os.path.join(KOK, 'analiz', 'uc_parca_cb.csv'),
            os.path.join(CIK, 'S4_hull_coefficients.csv'))
print('S4_hull_coefficients.csv            4 satir')

OKU = """# Supplementary material

Guney MC, Ince ST. Assessment of reduced experimental designs for
CFD-based trim optimisation. *Ships and Offshore Structures*, ICSOS 2026 Special Issue.

Every number in Sections 3.2, 3.3 and 4.1 of the manuscript, and every figure from
Fig. 3 onwards, is reproduced by the code in `code/` from the data files below. No new
simulation or experimental data were generated for the retrospective assessment; all
values are extracted from the published sources named in Table 6 of the manuscript.

## Data files

**S1_reference_datasets.csv** - the seven reference datasets. One row per
(dataset, operating point, trim level). Trim is given in the harmonised convention of
Section 2.5, in which a positive value denotes trim by the bow; where a source uses
the opposite convention the sign has been reversed, and the sentence in that source
establishing its convention is quoted in the header of `code/altkume_analizi.py`.
The `note` column records whether displacement was held constant, as stated by the
source.

**S2_design_enumeration.csv** - all reduced designs applied to those datasets. One row
per (design, operating point) pair: 1 639 rows over 296 designs. `design_levels` lists
the trim levels of the subset, separated by semicolons. `category` is the
classification of Section 2.5: *optimum sampled*, *resolution miss* (the optimum lies
inside the design's range but is not one of its levels) or *range miss* (the optimum
lies outside the design's range). `penalty_percent` is the increase in the response at
the selected trim relative to the response at the true optimum; for datasets whose
response is already a percentage of the even-keel value it is the difference in
percentage points.

**S3_screening_runs.csv** - the sixteen CFD runs of the orthogonal screening design
reported in Table 3, with the trim levels given in the same harmonised convention as
S1 and S2. In the conference version these levels appear with the opposite sign.
Resistance is in kN and the coefficient is given as C_T x 10^3.

**S4_hull_coefficients.csv** - block coefficients of the whole hull and of its
longitudinal parts, for the four vessels, computed from the hull surface models at the
design draught by the method described in Section 2.1 and reported in Table 7.

## Code

Python 3, standard library only except `matplotlib` for the figures.

- `altkume_analizi.py` - the reference datasets as published, the sign conversions with
  their justification, and the hand-picked designs of Table 7.
- `tam_altkume.py` - the exhaustive enumeration: all subsets, the per-dataset
  breakdown, the cluster bootstrap over datasets, the split by response variable, and
  the level-count by range-coverage table (Table 8). Run it to reproduce every pooled
  figure in Section 3.7.
- `sekiller.py` - generates Figures 3 to 8 as vector PDF and 400 dpi PNG.

Run `python tam_altkume.py` for the analysis and `python sekiller.py` for the figures.
"""
io.open(os.path.join(CIK, 'README.md'), 'w', encoding='utf-8').write(OKU)

# ------------------------------------------------------------- zip
zip_yol = os.path.join(KOK, 'gonderim', 'Guney_Ince_supplementary.zip')
with zipfile.ZipFile(zip_yol, 'w', zipfile.ZIP_DEFLATED) as z:
    for kok, _, dosyalar in os.walk(CIK):
        for d in dosyalar:
            tam = os.path.join(kok, d)
            z.write(tam, os.path.relpath(tam, CIK))
print('\n%s  (%.0f KB)' % (os.path.basename(zip_yol), os.path.getsize(zip_yol) / 1024))
