# -*- coding: utf-8 -*-
"""Secim yanliligini kaldiran tam sayim.

Elle secilmis tasarimlar yerine, her veri setinin yayimlanmis trim seviyelerinin
BUTUN altkumelerini (2 <= |S| <= n-1) uygular. Boylece "bu yirmi tasarimi siz
sectiniz" itirazi ortadan kalkar.

Ek olarak:
  - veri seti bazinda ayrisim (havuzun dengesizligi gorunur olsun)
  - veri setleri uzerinden kume (cluster) bootstrap ile guven araligi
  - yanit degiskeni turune gore ayrim (guc benzeri / direnc)
  - seviye sayisinin, aralik kapsamasi sabit tutuldugunda etkisi
"""
import sys, io, json, random
from itertools import combinations
import altkume_analizi as A

# stdout'u altkume_analizi zaten sariyor; ikinci kez sarmak akisi kapatiyor

# yanit turu: guc benzeri mi, direnc mi
TUR = {
    'Vasilev vd. 2024 - RO-RO 158 m, tam olcek CFD': 'guc',
    'Kim vd. 2015 - 6500 TEU konteyner, model deneyi': 'guc',
    'Kim vd. 2015 - Capesize dokme yuk, model deneyi': 'guc',
    'Korkmaz vd. 2023 - RoPax, model deneyi, 17 kn': 'guc',
    'Shivachev vd. 2017 - KCS 1:75, Fn 0.26': 'direnc',
    'Ziylan & Nas 2022 - 2478 TEU konteyner, model deneyi (ITTC-78)': 'direnc',
    'Martic vd. 2024 - KCS, sig su (h/T 1.78)': 'direnc',
}


def bedel(ds, row, j, g):
    if ds['yanit'].endswith('[%]'):
        return row[j] - row[g]
    return 100.0 * (row[j] - row[g]) / abs(row[g])


def ciftler(ds):
    """Butun altkumeler x butun isletme noktalari."""
    tr = ds['trimler']
    n = len(tr)
    opt = {k: min(range(len(v)), key=lambda m: v[m]) for k, v in ds['veri'].items()}
    out = []
    for boy in range(2, n):
        for sec in combinations(range(n), boy):
            idx = list(sec)
            lo, hi = tr[idx[0]], tr[idx[-1]]
            for k, row in ds['veri'].items():
                g = opt[k]
                j = min(idx, key=lambda m: row[m])
                b = bedel(ds, row, j, g)
                if g in idx:
                    grup = 'bulundu'
                elif lo <= tr[g] <= hi:
                    grup = 'cozunurluk'
                else:
                    grup = 'aralik'
                out.append({'grup': grup, 'bedel': b, 'seviye': boy,
                            'genislik': (hi - lo) / (tr[-1] - tr[0]),
                            'sifir': 0.0 in [tr[i] for i in idx]})
    return out


def ozet(v):
    if not v:
        return (0, 0.0, 0.0)
    return (len(v), sum(x['bedel'] for x in v) / len(v),
            max(x['bedel'] for x in v))


HEPSI = {}
for ds in A.VERI_SETLERI:
    HEPSI[ds['ad']] = ciftler(ds)

if __name__ == '__main__':
    # ---------------------------------------------------------------- 1. genel
    print('=' * 86)
    print('TAM SAYIM: her veri setinin butun trim altkumeleri (2 <= |S| <= n-1)')
    tasarim = sum(len({(p['seviye'], p['genislik']) for p in v}) for v in HEPSI.values())
    toplam = sum(len(v) for v in HEPSI.values())
    print('   tasarim x isletme noktasi cifti: %d   (elle secilmis surumde 112)' % toplam)

    kat = {'bulundu': [], 'cozunurluk': [], 'aralik': []}
    for v in HEPSI.values():
        for p in v:
            kat[p['grup']].append(p)

    print('\n%-44s%8s%12s%11s' % ('grup', 'cift', 'ort.bedel', 'en kotu'))
    isim = {'bulundu': 'optimum seviyesi tasarimda var',
            'cozunurluk': 'COZUNURLUK kacirmasi (aralik icinde)',
            'aralik': 'ARALIK kacirmasi (aralik disinda)'}
    for g in ('bulundu', 'cozunurluk', 'aralik'):
        n, o, w = ozet(kat[g])
        print('%-44s%8d%11.2f%%%10.2f%%' % (isim[g], n, o, w))
    oran = (sum(p['bedel'] for p in kat['aralik']) / len(kat['aralik'])) / \
           (sum(p['bedel'] for p in kat['cozunurluk']) / len(kat['cozunurluk']))
    print('   --> aralik kacirmasi %.1f kat pahali' % oran)

    # ---------------------------------------------------- 2. veri seti bazinda
    print('\n' + '=' * 86)
    print('VERI SETI BAZINDA AYRISIM  (havuzun dengesizligi burada gorunur)')
    print('%-40s%7s%9s%9s%9s%9s' % ('veri seti', 'cift', 'pay', 'coz.ort', 'ara.ort', 'oran'))
    setorani = []
    for ad, v in HEPSI.items():
        c = [p for p in v if p['grup'] == 'cozunurluk']
        a = [p for p in v if p['grup'] == 'aralik']
        oc = sum(p['bedel'] for p in c) / len(c) if c else float('nan')
        oa = sum(p['bedel'] for p in a) / len(a) if a else float('nan')
        r = oa / oc if c and oc > 0 else float('nan')
        if c and oc > 0:
            setorani.append(r)
        print('%-40s%7d%8.0f%%%8.2f%%%8.2f%%%9.1f' %
              (ad[:38], len(v), 100.0 * len(v) / toplam, oc, oa, r))
    print('   veri setleri esit agirlikli ortalama oran: %.1f  (havuzlanmis: %.1f)'
          % (sum(setorani) / len(setorani), oran))

    # ------------------------------------------------- 3. kume bootstrap (CI)
    random.seed(20261103)
    adlar = list(HEPSI)
    oranlar = []
    for _ in range(4000):
        sec = [random.choice(adlar) for _ in adlar]
        c = []; a = []
        for ad in sec:
            for p in HEPSI[ad]:
                if p['grup'] == 'cozunurluk':
                    c.append(p['bedel'])
                elif p['grup'] == 'aralik':
                    a.append(p['bedel'])
        if c and sum(c) > 0:
            oranlar.append((sum(a) / len(a)) / (sum(c) / len(c)))
    oranlar.sort()
    alt = oranlar[int(0.025 * len(oranlar))]
    ust = oranlar[int(0.975 * len(oranlar))]
    print('\n   veri setleri uzerinden kume bootstrap, %%95 aralik: %.1f - %.1f kat'
          % (alt, ust))
    print('   (n = 7 veri seti oldugu icin aralik genis; durust olan budur)')

    # -------------------------------------------------- 4. yanit turune gore
    print('\n' + '=' * 86)
    print('YANIT DEGISKENI TURUNE GORE  (guc benzeri vs direnc ayri raporlanir)')
    print('%-26s%8s%12s%12s%9s' % ('tur', 'cift', 'coz.ort', 'ara.ort', 'oran'))
    for t in ('guc', 'direnc'):
        c = [p['bedel'] for ad, v in HEPSI.items() if TUR[ad] == t
             for p in v if p['grup'] == 'cozunurluk']
        a = [p['bedel'] for ad, v in HEPSI.items() if TUR[ad] == t
             for p in v if p['grup'] == 'aralik']
        n = sum(len(v) for ad, v in HEPSI.items() if TUR[ad] == t)
        etk = {'guc': 'guc benzeri (Pb, PD, BHP)', 'direnc': 'direnc (RT)'}[t]
        print('%-26s%8d%11.2f%%%11.2f%%%9.1f' %
              (etk, n, sum(c) / len(c), sum(a) / len(a),
               (sum(a) / len(a)) / (sum(c) / len(c))))

    # ------------------------------- 5. seviye sayisi, kapsama sabit tutulunca
    print('\n' + '=' * 86)
    print('SEVIYE SAYISI, ARALIK KAPSAMASI SABIT TUTULDUGUNDA')
    print('%-10s%14s%10s%14s%10s' % ('seviye', 'kapsiyorsa', 'cift', 'kapsamiyorsa', 'cift'))
    for s in range(2, 7):
        ic = [p['bedel'] for v in HEPSI.values() for p in v
              if p['seviye'] == s and p['grup'] != 'aralik']
        dis = [p['bedel'] for v in HEPSI.values() for p in v
               if p['seviye'] == s and p['grup'] == 'aralik']
        if not ic and not dis:
            continue
        print('%-10d%13.2f%%%10d%13.2f%%%10d' %
              (s, sum(ic) / len(ic) if ic else 0, len(ic),
               sum(dis) / len(dis) if dis else 0, len(dis)))
    print('   --> aralik optimumu kapsiyorsa seviye sayisi neredeyse bir sey degistirmiyor;')
    print('       kapsamiyorsa seviye eklemek bedeli dusurmuyor.')

    # ------------------------------------------------- 6. %1 gurultu esigi
    print('\n' + '=' * 86)
    print('%1 GURULTU ESIGI TESTI')
    for g in ('cozunurluk', 'aralik'):
        v = [p['bedel'] for p in kat[g]]
        ust1 = sum(1 for b in v if b >= 1.0)
        print('   %-14s %5d cift, %5d tanesi (%%%.0f) %%1 ve uzeri'
              % (g, len(v), ust1, 100.0 * ust1 / len(v)))

    # ------------------------------------------------------------- 7. kayit
    with open('tam_altkume_sonuc.json', 'w', encoding='utf-8') as f:
        json.dump({'toplam_cift': toplam, 'oran_havuzlanmis': oran,
                   'oran_ci': [alt, ust],
                   'kategori': {g: {'cift': ozet(kat[g])[0], 'ort': ozet(kat[g])[1],
                                    'en_kotu': ozet(kat[g])[2]} for g in kat}},
                  f, ensure_ascii=False, indent=1)
    print('\n--> tam_altkume_sonuc.json yazildi')
