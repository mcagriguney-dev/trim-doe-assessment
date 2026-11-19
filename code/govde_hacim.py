# -*- coding: utf-8 -*-
"""Rhino govde modellerinden su altindaki hacmin boyuna dagilimini cikarir.

Yontem
------
Brep yuzlerinde saklanan render mesh'ler kirpilmis gercek geometriyi verir.
Kapali bir govde icin, F = (0, 0, z - T) alaniyla diverjans teoremi:

    V = oint_S (z - T) n_z dS,      div F = 1

Su yuzeyindeki kapak uzerinde z = T oldugundan katkisi sifirdir; yani yalnizca
ISLAK yuzeyi toplamak yeterli, kapak eklemeye gerek yok.

Ayni sey boyuna dilimler icin de gecerli: x = sabit kesitlerinde n_z = 0,
dolayisiyla dilim kapaklari da katki vermez. Bu yuzden ucgenleri once z <= T
ile, sonra x kutulariyla kirpip toplamak her dilimin hacmini TAM verir.

Ucgen duzlemsel ve z uzerinde dogrusal oldugu icin
    int (z - T) n_z dS = n_z A (zbar - T)
bagintisi yaklasiklik degil, kesindir.
"""
import io, math, os, sys
import rhino3dm as r3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DIZIN = r'C:\Users\mcagr\Desktop\ARTICLE'
RHO = 1.025  # t/m3

# ad -> (dosya, tasarim su cekimi T [m], Tablo 1 deplasmani [t])
GEMI = {
    'Neptun':   ('Neptun_Hull.3dm', 4.27, 4934),
    'Alfa Sun': ('AlfaSun_Hull.3dm', 6.70, 8143),
    'Ilgaz':    ('ILGAZ_HULL.3dm', 5.50, 6397),
    'ELA-S':    ('ALB460-ELA_S  FORM- P02.3dm', 5.80, 8189),
}


def ucgenler(yol):
    """Modeldeki her Brep icin ucgen listesi dondur: [(ad, [(p0,p1,p2), ...])]"""
    m = r3.File3dm.Read(yol)
    cikti = []
    for i, ob in enumerate(m.Objects):
        g = ob.Geometry
        if not isinstance(g, r3.Brep):
            continue
        ucg = []
        for f in g.Faces:
            msh = f.GetMesh(r3.MeshType.Render)
            if msh is None:
                continue
            V = [(v.X, v.Y, v.Z) for v in msh.Vertices]
            for k in range(len(msh.Faces)):
                yz = msh.Faces[k]
                a, b, c, d = yz[0], yz[1], yz[2], yz[3]
                ucg.append((V[a], V[b], V[c]))
                if d != c:                      # dortgen -> ikinci ucgen
                    ucg.append((V[a], V[c], V[d]))
        cikti.append(('Brep%d' % i, ucg))
    return cikti


def nz_alan(p0, p1, p2):
    """Alan vektorunun z bileseni: (1/2)((p1-p0) x (p2-p0))_z"""
    return 0.5 * ((p1[0] - p0[0]) * (p2[1] - p0[1])
                  - (p1[1] - p0[1]) * (p2[0] - p0[0]))


def kirp_z(poli, T):
    """Poligonu z <= T yarim uzayina kirp (Sutherland-Hodgman)."""
    if not poli:
        return []
    cik = []
    n = len(poli)
    for i in range(n):
        a = poli[i]
        b = poli[(i + 1) % n]
        a_ic = a[2] <= T
        b_ic = b[2] <= T
        if a_ic:
            cik.append(a)
        if a_ic != b_ic:
            t = (T - a[2]) / (b[2] - a[2])
            cik.append((a[0] + t * (b[0] - a[0]),
                        a[1] + t * (b[1] - a[1]), T))
    return cik


def kirp_x(poli, x0, x1):
    """Poligonu x0 <= x <= x1 dilimine kirp."""
    for sinir, isaret in ((x0, 1), (x1, -1)):
        if not poli:
            return []
        cik = []
        n = len(poli)
        for i in range(n):
            a = poli[i]
            b = poli[(i + 1) % n]
            da = isaret * (a[0] - sinir)
            db = isaret * (b[0] - sinir)
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
    """int (z-T) n_z dS, poligon ucgenlere bolunerek."""
    if len(poli) < 3:
        return 0.0
    s = 0.0
    for i in range(1, len(poli) - 1):
        p0, p1, p2 = poli[0], poli[i], poli[i + 1]
        nz = nz_alan(p0, p1, p2)
        if nz == 0.0:
            continue
        zbar = (p0[2] + p1[2] + p2[2]) / 3.0
        s += nz * (zbar - T)
    return s


def dagilim(ucg, T, x0, x1, nbin):
    """Her x kutusundaki su alti hacmi. Isaret duzeltmesi disarida yapilir."""
    dx = (x1 - x0) / nbin
    kova = [0.0] * nbin
    for tri in ucg:
        if min(p[2] for p in tri) >= T:          # tamamen su ustunde
            continue
        poli = kirp_z(list(tri), T)
        if len(poli) < 3:
            continue
        xmin = min(p[0] for p in poli)
        xmax = max(p[0] for p in poli)
        i0 = max(0, min(nbin - 1, int((xmin - x0) / dx)))
        i1 = max(0, min(nbin - 1, int((xmax - x0) / dx)))
        if i0 == i1:                              # tek kutuda, kirpmaya gerek yok
            kova[i0] += katki(poli, T)
            continue
        for i in range(i0, i1 + 1):
            parca = kirp_x(poli, x0 + i * dx, x0 + (i + 1) * dx)
            if len(parca) >= 3:
                kova[i] += katki(parca, T)
    return kova, dx


print('Rhino modellerinden su alti hacmi (tasarim su cekiminde)')
print()
SONUC = {}
for ad, (dosya, T, depl) in GEMI.items():
    yol = os.path.join(DIZIN, dosya)
    print('=' * 70)
    print('%s   T = %.2f m   Tablo 1 deplasmani %d t' % (ad, T, depl))
    parcalar = ucgenler(yol)
    xmin = min(min(p[0] for tri in u for p in tri) for _, u in parcalar)
    xmax = max(max(p[0] for tri in u for p in tri) for _, u in parcalar)
    NB = 240
    toplam = [0.0] * NB
    for etiket, ucg in parcalar:
        kova, dx = dagilim(ucg, T, xmin, xmax, NB)
        hac = sum(kova)
        print('  %-7s ucgen %7d   hacim %10.1f m3   x %7.2f..%7.2f'
              % (etiket, len(ucg), hac,
                 min(p[0] for tri in ucg for p in tri),
                 max(p[0] for tri in ucg for p in tri)))
        for i in range(NB):
            toplam[i] += kova[i]
    V = sum(toplam)
    print('  TOPLAM hacim %10.1f m3   -> deplasman %8.0f t  (Tablo 1: %d t, fark %+.1f%%)'
          % (V, V * RHO, depl, 100 * (V * RHO - depl) / depl))
    SONUC[ad] = (toplam, xmin, xmax, dx, T, depl)
    print()

# --- dagilimi dosyaya yaz, sonraki adimda kullanilacak
CIK = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hacim_dagilimi.csv')
with io.open(CIK, 'w', encoding='utf-8') as f:
    f.write('ship,x_m,dx_m,volume_m3\n')
    for ad, (kova, x0, x1, dx, T, depl) in SONUC.items():
        for i, v in enumerate(kova):
            f.write('%s,%.4f,%.4f,%.6f\n' % (ad, x0 + (i + 0.5) * dx, dx, v))
print('dagilim -> %s' % CIK)
