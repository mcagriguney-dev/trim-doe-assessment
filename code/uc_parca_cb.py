# -*- coding: utf-8 -*-
"""Govdeyi boyuna uc esit parcaya bolup her parcanin blok katsayisini cikarir.

Hocanin onerisi: "gemiyi 3 parcaya bolup 3 tarafin Cb degerini alip
karsilastirsak burdan bir yorum yapabilir miyiz".

Yontem govde_hacim.py'dekiyle ayni (diverjans teoremi, render mesh). Burada
ayrica su hatti genisligi, su hatti boyu, LCB ve iki parcali bolum de
hesaplanir; iki parcali sonuc makaledeki Tablo 7 ile karsilastirilabilir.

Dogrulama: ayni boru hatti Alfa Sun, Ilgaz ve ELA-S icin Tablo 1 deplasmanini
%0.0, %0.1 ve %0.6 hata ile veriyor.
"""
import io, os, sys
import rhino3dm as r3

if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                 errors='replace')

DIZIN = r'C:\Users\mcagr\Desktop\ARTICLE'
RHO = 1.025

GEMI = {
    'Neptun':   ('Neptun_Hull.3dm', 4.27, 4934, 0.839),
    'Alfa Sun': ('AlfaSun_Hull.3dm', 6.70, 8143, 0.755),
    'Ilgaz':    ('ILGAZ_HULL.3dm', 5.50, 6397, 0.713),
    'ELA-S':    ('ALB460-ELA_S  FORM- P02.3dm', 5.80, 8189, 0.875),
}
# makalede kayitli en iyi trim (pozitif = basa trim)
EN_IYI = {'Neptun': -0.5, 'Alfa Sun': +1.0, 'Ilgaz': 0.0, 'ELA-S': +1.0}


def ucgenler(yol):
    m = r3.File3dm.Read(yol)
    ucg = []
    for ob in m.Objects:
        g = ob.Geometry
        if not isinstance(g, r3.Brep):
            continue
        for f in g.Faces:
            msh = f.GetMesh(r3.MeshType.Render)
            if msh is None:
                continue
            V = [(v.X, v.Y, v.Z) for v in msh.Vertices]
            for k in range(len(msh.Faces)):
                a, b, c, d = msh.Faces[k]
                ucg.append((V[a], V[b], V[c]))
                if d != c:
                    ucg.append((V[a], V[c], V[d]))
    return ucg


def nz_alan(p0, p1, p2):
    return 0.5 * ((p1[0] - p0[0]) * (p2[1] - p0[1])
                  - (p1[1] - p0[1]) * (p2[0] - p0[0]))


def kirp_z(poli, T):
    cik = []
    n = len(poli)
    for i in range(n):
        a, b = poli[i], poli[(i + 1) % n]
        ai, bi = a[2] <= T, b[2] <= T
        if ai:
            cik.append(a)
        if ai != bi:
            t = (T - a[2]) / (b[2] - a[2])
            cik.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), T))
    return cik


def kirp_x(poli, x0, x1):
    for sinir, isaret in ((x0, 1), (x1, -1)):
        if not poli:
            return []
        cik = []
        n = len(poli)
        for i in range(n):
            a, b = poli[i], poli[(i + 1) % n]
            da, db = isaret * (a[0] - sinir), isaret * (b[0] - sinir)
            if da >= 0:
                cik.append(a)
            if (da >= 0) != (db >= 0):
                t = da / (da - db)
                cik.append((a[0] + t * (b[0] - a[0]),
                            a[1] + t * (b[1] - a[1]),
                            a[2] + t * (b[2] - a[2])))
        poli = cik
    return poli


def katki(poli, T):
    if len(poli) < 3:
        return 0.0
    s = 0.0
    for i in range(1, len(poli) - 1):
        p0, p1, p2 = poli[0], poli[i], poli[i + 1]
        nz = nz_alan(p0, p1, p2)
        if nz:
            s += nz * ((p0[2] + p1[2] + p2[2]) / 3.0 - T)
    return s


def dagilim(ucg, T, x0, x1, nbin):
    dx = (x1 - x0) / nbin
    kova = [0.0] * nbin
    for tri in ucg:
        if min(p[2] for p in tri) >= T:
            continue
        poli = kirp_z(list(tri), T)
        if len(poli) < 3:
            continue
        xs = [p[0] for p in poli]
        i0 = max(0, min(nbin - 1, int((min(xs) - x0) / dx)))
        i1 = max(0, min(nbin - 1, int((max(xs) - x0) / dx)))
        if i0 == i1:
            kova[i0] += katki(poli, T)
        else:
            for i in range(i0, i1 + 1):
                p = kirp_x(poli, x0 + i * dx, x0 + (i + 1) * dx)
                if len(p) >= 3:
                    kova[i] += katki(p, T)
    return kova, dx


def hidrostatik(ucg, T, nbin=600):
    xs = [p[0] for tri in ucg for p in tri]
    x0, x1 = min(xs), max(xs)
    kova, dx = dagilim(ucg, T, x0, x1, nbin)
    if sum(kova) < 0:                       # normaller ice bakiyorsa cevir
        kova = [-v for v in kova]
    # su alti maksimum yari genislik
    yarim = max(abs(p[1]) for tri in ucg for p in tri if p[2] <= T)
    # su hatti boyu: hacmi olan ilk ve son kutu
    dolu = [i for i, v in enumerate(kova) if v > 1e-6]
    xa = x0 + dolu[0] * dx
    xb = x0 + (dolu[-1] + 1) * dx
    return kova, x0, dx, 2.0 * yarim, xa, xb


def parca_cb(kova, x0, dx, xa, xb, B, T, n):
    """Su hatti boyunu n esit parcaya bol, her parcanin C_B'si."""
    L = xb - xa
    sonuc = []
    for k in range(n):
        a, b = xa + k * L / n, xa + (k + 1) * L / n
        v = 0.0
        for i, val in enumerate(kova):
            c0, c1 = x0 + i * dx, x0 + (i + 1) * dx
            ust, alt = min(c1, b), max(c0, a)
            if ust > alt:                   # kutu ile parca kesisimi oraninca
                v += val * (ust - alt) / (c1 - c0)
        sonuc.append((v, v / ((L / n) * B * T)))
    return sonuc, L


if __name__ == '__main__':
    print('UC PARCALI BLOK KATSAYISI  (Rhino modellerinden)')
    print('x ekseni kictan basa; parca 1 = kic, parca 3 = bas')
    print()
    SATIR = []
    for ad, (dosya, T, depl, cb_tablo) in GEMI.items():
        ucg = ucgenler(os.path.join(DIZIN, dosya))
        kova, x0, dx, B, xa, xb = hidrostatik(ucg, T)
        V = sum(kova)
        uc, L = parca_cb(kova, x0, dx, xa, xb, B, T, 3)
        iki, _ = parca_cb(kova, x0, dx, xa, xb, B, T, 2)
        lcb = sum((x0 + (i + 0.5) * dx) * v for i, v in enumerate(kova)) / V
        cb = V / (L * B * T)
        print('=' * 74)
        print('%s   T %.2f m   B_su hatti %.2f m   L_su hatti %.2f m' % (ad, T, B, L))
        print('  hacim %8.1f m3  -> %7.0f t   (Tablo 1: %d t, fark %+.1f%%)'
              % (V, V * RHO, depl, 100 * (V * RHO - depl) / depl))
        print('  C_B butun gemi  %.3f   (Tablo 1: %.3f, fark %+.3f)'
              % (cb, cb_tablo, cb - cb_tablo))
        print('  LCB  %.2f m  (orta %.2f m, %+.2f m = %+.2f%% L)'
              % (lcb, (xa + xb) / 2, lcb - (xa + xb) / 2,
                 100 * (lcb - (xa + xb) / 2) / L))
        print('  iki parca   kic %.3f   bas %.3f   (dolgun yari: %s)'
              % (iki[0][1], iki[1][1], 'kic' if iki[0][1] > iki[1][1] else 'bas'))
        print('  UC PARCA    kic %.3f   orta %.3f   bas %.3f'
              % (uc[0][1], uc[1][1], uc[2][1]))
        print('              hacim %6.0f  %6.0f  %6.0f m3'
              % (uc[0][0], uc[1][0], uc[2][0]))
        print('  en iyi trim %+.1f m' % EN_IYI[ad])
        SATIR.append((ad, B, L, V, cb, uc[0][1], uc[1][1], uc[2][1],
                      iki[0][1], iki[1][1], EN_IYI[ad]))
        print()

    print('=' * 74)
    print('OZET')
    print('%-9s %6s %6s %6s | %6s %6s %6s | %6s %6s | %6s'
          % ('gemi', 'B', 'L_WL', 'C_B', 'kic', 'orta', 'bas', 'kic2', 'bas2', 'trim'))
    for s in SATIR:
        print('%-9s %6.2f %6.2f %6.3f | %6.3f %6.3f %6.3f | %6.3f %6.3f | %+6.1f'
              % (s[0], s[1], s[2], s[4], s[5], s[6], s[7], s[8], s[9], s[10]))

    CIK = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uc_parca_cb.csv')
    with io.open(CIK, 'w', encoding='utf-8') as f:
        f.write('ship,B_wl_m,L_wl_m,volume_m3,CB_whole,'
                'CB_aft_third,CB_mid_third,CB_fwd_third,'
                'CB_aft_half,CB_fwd_half,best_trim_m\n')
        for s in SATIR:
            f.write('%s,%.3f,%.3f,%.1f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%+.1f\n'
                    % (s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], s[10]))
    print()
    print('-> %s' % CIK)
