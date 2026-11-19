# -*- coding: utf-8 -*-
"""
Geriye donuk deney tasarimi analizi
===================================
Yayimlanmis yogun trim veri setlerini "tam uzay" referansi kabul eder, uzerine
azaltilmis tasarimlar uygular ve bu tasarimlarin optimumu bulup bulamadigini olcer.

ORTAK ISARET KONVANSIYONU
-------------------------
Bu scriptte tau > 0  =  BASA TRIM (bas su cekimi daha buyuk, bas asagi).
Kaynaklarin konvansiyonlari farkli oldugu icin her veri setinde cevrim yapilir:

  Vasilev vd. 2024 : negatif = basa trim  -> isaret TERSLENIR
      ("A negative sign means the trim by the bow and a positive sign,
        the trim by the stern")
  Shivachev vd. 2017 : pozitif = basa trim -> isaret AYNEN
      (Tablo 7 basligi: "Positive by bow")
  Kim vd. 2015 (KRISO) : pozitif = basa trim -> isaret AYNEN
      (trim kosullari +1.0 m, +0.5 m, E, -1.0 m; + bas tarafa)

  >>> Makalede belirtilmeli: literaturde trim isareti standart degil.
      Bu, veri setlerini karsilastirmayi zorlastiran ayri bir bulgudur.

DOGRULAMA DURUMU (3 Kasim 2026)
-------------------------------
  Vasilev Tablo 8  : 63 degerin tamami PDF metin katmanindan koordinatlariyla
                     yeniden kurularak TEYIT EDILDI.
                     Yayin hatasi: Tablo 8 ve 9'un "Trim by stern" sutun
                     basliklari bas trim etiketlerini tekrarliyor. Tablo 7
                     (devir) ayni duzende dogru etiketli. Makalede dipnot gerekli.
  Kim vd. Tablo 2-3: TEYIT EDILDI (makale metninden, model deneyi sonuclari).
  Shivachev Tablo 7: TEYIT EDILDI (tablo basligi ve degerler metinden).
  Ziylan, Korkmaz, Martic, Park : tablolar PDF'te grafik olarak gomulu,
                     metin katmanindan cikarilamadi. ELLE OKUNUP EKLENECEK.
  Campbell 105 vaka: veri dosyasi Cloudflare arkasinda, tarayicidan indirilmeli.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ======================================================================= VERI
# Her veri seti: trimler ORTAK konvansiyonda (pozitif = basa trim), artan sirada.

VERI_SETLERI = []

# --- Vasilev vd. (2024) JMSE 12(8):1265, Tablo 8 - fren gucu Pb [kW]
# Kaynak sutun sirasi: -1.5 -1 -0.5 0 +0.5 +1 +1.5 (negatif = basa trim)
# Ortak konvansiyona cevrim: isaret terslenir ve sira ters cevrilir.
_vas = {
    (7.5, 12.5): [2248, 2335, 2370, 2447, 2601, 2739, 2837],
    (7.5, 15.0): [3509, 3665, 3772, 3965, 4130, 4414, 4642],
    (7.5, 18.0): [5957, 6187, 6345, 6441, 6667, 7124, 7480],
    (8.0, 12.5): [2155, 2221, 2285, 2357, 2450, 2664, 2882],
    (8.0, 15.0): [3587, 3719, 3818, 3869, 4073, 4352, 4639],
    (8.0, 18.0): [6595, 6567, 6750, 6942, 7120, 7879, 7991],
    (8.7, 12.5): [2293, 2353, 2403, 2478, 2564, 2771, 3048],
    (8.7, 15.0): [4018, 4072, 4181, 4303, 4504, 4890, 5113],
    (8.7, 18.0): [7531, 7663, 7707, 8003, 8405, 9143, 9361],
}
VERI_SETLERI.append({
    'ad': 'Vasilev vd. 2024 - RO-RO 158 m, tam olcek CFD',
    'yanit': 'Pb [kW]',
    'trimler': [-1.5, -1.0, -0.5, 0.0, 1.5, 1.0, 0.5][:0] or [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5],
    'veri': {k: list(reversed(v)) for k, v in _vas.items()},   # sira ters -> tau_bow artan
    'not': 'sabit ortalama su cekimi; deplasman trimle degisiyor',
})
# ters cevirince trimler: +1.5 +1 +0.5 0 -0.5 -1 -1.5 (tau_bow) -> artan sirada:
VERI_SETLERI[-1]['trimler'] = [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5]

# --- Kim, Yoon, Jeong (2015) SNAK, Tablo 2 - 6500 TEU konteyner, model deneyi
# BHP'nin duz omurgaya gore yuzde degisimi. Trim kosullari: +1.0 +0.5 E -1.0 (+ = basa)
VERI_SETLERI.append({
    'ad': 'Kim vd. 2015 - 6500 TEU konteyner, model deneyi',
    'yanit': 'BHP degisimi [%]',
    'trimler': [-1.0, 0.0, 0.5, 1.0],
    'veri': {
        ('T1', 20.0): [2.7, 0.0, -2.2, -3.8],
        ('T1', 21.5): [2.6, 0.0, -2.4, -4.0],
        ('T1', 23.0): [1.9, 0.0, -2.6, -4.3],
        ('T2', 20.0): [6.7, 0.0, -3.0, -3.5],
        ('T2', 21.5): [4.8, 0.0, -4.2, -4.9],
        ('T2', 23.0): [4.2, 0.0, -5.0, -5.6],
    },
    'not': 'SABIT DEPLASMAN; model deneyi (kendinden sevkli)',
})

# --- Kim, Yoon, Jeong (2015) Tablo 3 - Capesize dokme yuk, model deneyi
VERI_SETLERI.append({
    'ad': 'Kim vd. 2015 - Capesize dokme yuk, model deneyi',
    'yanit': 'BHP degisimi [%]',
    'trimler': [-2.0, -1.0, 0.0, 1.0],
    'veri': {
        ('T1', 13.0): [0.5, -0.2, 0.0, -0.9],
        ('T1', 14.0): [0.5, -0.3, 0.0, -0.4],
        ('T1', 15.0): [0.5, 0.1, 0.0, -0.1],
        ('T2', 13.0): [3.6, 2.5, 0.0, -2.6],
        ('T2', 14.0): [4.0, 2.8, 0.0, -1.8],
        ('T2', 15.0): [4.5, 3.1, 0.0, -0.8],
    },
    'not': 'SABIT DEPLASMAN; model deneyi',
})

# --- Shivachev vd. (2017) OMAE2017-61860, Tablo 7 - KCS 1:75, Fn 0.26
# Trim acisi [derece], pozitif = basa. Yanit: toplam direnc RT [N].
VERI_SETLERI.append({
    'ad': 'Shivachev vd. 2017 - KCS 1:75, Fn 0.26',
    'yanit': 'RT [N]',
    'trimler': [-1.0, -0.6, -0.25, 0.0, 0.25, 0.6, 1.0],
    'veri': {
        ('EFD', 0.26): [8.09, 7.74, 7.64, 7.50, 7.41, 7.62, 7.89],
        ('CFD-serbest', 0.26): [7.68, 7.33, 7.23, 7.21, 7.16, 7.26, 7.45],
        ('CFD-sabit', 0.26): [7.44, 7.08, 7.02, 6.94, 6.92, 7.03, 7.16],
    },
    'not': 'trim DERECE cinsinden; sabit ortalama su cekimi',
})

# --- Ziylan & Nas (2022) ToMS 11(2), Tablo 5-6 - 2478 TEU, model deneyi + ITTC-78
# Kaynak sutunlari: -2, -1, 0, +1 m. Konvansiyon metinden: "resistance increases
# with increasing stern trim", "highest resistance in the negative trimmed
# conditions" -> negatif = KICA trim, pozitif = BASA trim. Ortak konvansiyonla ayni.
VERI_SETLERI.append({
    'ad': 'Ziylan & Nas 2022 - 2478 TEU konteyner, model deneyi (ITTC-78)',
    'yanit': 'RT [kN]',
    'trimler': [-2.0, -1.0, 0.0, 1.0],
    'veri': {
        ('T 11.40 m', 22.0): [1760.5, 1629.9, 1485.1, 1615.5],
        ('T 10.10 m', 22.0): [1491.3, 1414.0, 1220.0, 1406.3],
        ('T 8.80 m', 22.0): [1256.8, 1155.4, 1176.5, 1229.9],
        ('T 11.40 m', 15.0): [812.3, 665.1, 646.7, 722.7],
        ('T 10.10 m', 15.0): [722.1, 737.2, 657.2, 666.2],
        ('T 8.80 m', 15.0): [720.0, 666.5, 694.4, 668.5],
    },
    'not': 'tam olcege ITTC-78 ile ekstrapole; deplasman sabitligi belirtilmemis',
})

# --- Korkmaz, Werner, Bensow (2023) Ocean Eng. 288:116098, Tablo 10 - RoPax
# Yanit: teslim gucunun duz omurgaya gore degisimi [%]. 17 kn.
# Konvansiyon metinden: "H-1.5m loading condition having the greatest transom
# submergence" -> negatif = KICA trim. Ortak konvansiyonla ayni.
VERI_SETLERI.append({
    'ad': 'Korkmaz vd. 2023 - RoPax, model deneyi, 17 kn',
    'yanit': 'PD degisimi [%]',
    'trimler': [-1.5, 0.0, 1.5],
    'veri': {
        ('hafif yuk', 17.0): [19.9, 0.0, -0.7],
        ('agir yuk', 17.0): [21.2, 0.0, -5.9],
    },
    'not': 'SABIT DEPLASMAN; kendinden sevkli model deneyi',
})

# --- Martic vd. (2024) Appl. Sci. 14(15):6570, Tablo 9 - KCS, SIG SU
# Trim [derece]. Konvansiyon metinden: "For a trim by bow, there is a reduction
# in pressure resistance ... Conversely, for a trim by stern" -> pozitif = BASA.
VERI_SETLERI.append({
    'ad': 'Martic vd. 2024 - KCS, sig su (h/T 1.78)',
    'yanit': 'RT [N]',
    'trimler': [-0.4, -0.2, 0.0, 0.2, 0.4],
    'veri': {
        ('KCS sig su', 0.469): [2.89, 2.81, 2.77, 2.71, 2.68],
    },
    'not': 'SIG SU - derin su setleriyle dogrudan karsilastirilmamali',
})

# --- Vasilev Tablo 9 - gunluk yakit [t/gun], bedeli tona cevirmek icin
DFOC_VAS = {
    (7.5, 12.5): [10.70, 11.08, 11.24, 11.57, 12.25, 12.84, 13.26],
    (7.5, 15.0): [16.11, 16.75, 17.20, 18.00, 18.68, 19.85, 20.79],
    (7.5, 18.0): [26.22, 27.18, 27.83, 28.23, 29.18, 31.09, 32.58],
    (8.0, 12.5): [10.29, 10.58, 10.86, 11.18, 11.59, 12.52, 13.46],
    (8.0, 15.0): [16.43, 16.98, 17.39, 17.60, 18.45, 19.60, 20.78],
    (8.0, 18.0): [28.88, 28.76, 29.53, 30.33, 31.08, 34.26, 34.73],
    (8.7, 12.5): [10.90, 11.16, 11.38, 11.71, 12.08, 12.98, 14.16],
}
DFOC_VAS = {k: list(reversed(v)) for k, v in DFOC_VAS.items()}   # tau_bow artan

# ==================================================================== ANALIZ

def optimum_konumu(ds):
    """Her isletme noktasinda optimum trim: kenarda mi, ic noktada mi?"""
    tr = ds['trimler']
    print('\n' + '=' * 78)
    print(ds['ad'] + '   [' + ds['yanit'] + ']')
    print('   ' + ds['not'])
    print(f"{'nokta':>18}{'opt tau_bow':>13}{'yanit':>10}{'duz omurga':>12}{'kazanc':>9}{'konum':>11}")
    opt = {}; kenar = 0
    for k, row in ds['veri'].items():
        i = min(range(len(row)), key=lambda m: row[m])
        opt[k] = i
        j0 = tr.index(0.0)
        if ds['yanit'].endswith('[%]'):
            kaz = row[j0] - row[i]          # zaten yuzde
        else:
            kaz = 100 * (row[j0] - row[i]) / row[j0]
        yer = 'KENAR' if i in (0, len(tr) - 1) else 'ic nokta'
        if yer == 'KENAR': kenar += 1
        print(f"{str(k):>18}{tr[i]:>13}{row[i]:>10.2f}{row[j0]:>12.2f}{kaz:>8.1f}%{yer:>11}")
    print(f"   --> {kenar}/{len(ds['veri'])} isletme noktasinda optimum ARALIGIN UCUNDA")
    return opt

def azaltilmis(ds, opt, secilen, etiket):
    tr = ds['trimler']
    try:
        idx = [tr.index(t) for t in secilen]
    except ValueError:
        return
    yanlis = 0; toplam = 0.0; enkotu = 0.0
    for k, row in ds['veri'].items():
        j = min(idx, key=lambda m: row[m])
        g = opt[k]
        if ds['yanit'].endswith('[%]'):
            bedel = row[j] - row[g]                      # yuzde puan farki
        else:
            bedel = 100 * (row[j] - row[g]) / abs(row[g])
        toplam += bedel; enkotu = max(enkotu, bedel)
        if j != g: yanlis += 1
    n = len(ds['veri'])
    print(f"{etiket:<34}{len(secilen):>5}{yanlis:>8}/{n}{toplam/n:>12.2f}{enkotu:>11.2f}")
    return {"yanlis": yanlis, "nokta": n, "ort_bedel": toplam/n, "en_kotu": enkotu}

def yakit(secilen, etiket, gun=280):
    tr = VERI_SETLERI[0]['trimler']; guc = VERI_SETLERI[0]['veri']
    idx = [tr.index(t) for t in secilen]
    top = 0.0; n = 0
    for k, row in DFOC_VAS.items():
        j = min(idx, key=lambda m: guc[k][m])
        g = min(range(len(guc[k])), key=lambda m: guc[k][m])
        top += row[j] - row[g]; n += 1
    o = top / n
    print(f"{etiket:<34}{o:>10.3f} t/gun{o*gun:>12.0f} t/yil")
    return {"etiket": etiket, "seviye": len(secilen), "gunluk": o, "yillik": o*gun,
            "nokta": n}

# ==================================================== AZALTILMIS TASARIM TANIMLARI
# kapsam etiketi:  'tam'   = yayimlanmis matrisin tamami
#                  'uclar' = aralik taranan uzayin uclarini iceriyor
#                  'ic'    = aralik daraltilmis, uclar dislanmis
#                  'dar'   = en dar aralik

TASARIMLAR = {
 'Vasilev vd. 2024 - RO-RO 158 m, tam olcek CFD': [
    ('tam tarama',                    [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5], 'tam'),
    ('4 seviye, uclar dahil',         [-1.5, -0.5, 0.5, 1.5],                 'uclar'),
    ('3 seviye, uclar dahil',         [-1.5, 0.0, 1.5],                       'uclar'),
    ('4 seviye, ic aralik',           [-1.0, -0.5, 0.5, 1.0],                 'ic'),
    ('3 seviye, ic aralik',           [-1.0, 0.0, 1.0],                       'ic'),
    ('4 seviye, bildirimizin araligi',[-1.0, -0.5, 0.0, 0.5],                 'ic'),
    ('3 seviye, dar aralik',          [-0.5, 0.0, 0.5],                       'dar'),
 ],
 'Shivachev vd. 2017 - KCS 1:75, Fn 0.26': [
    ('tam tarama',                    [-1.0, -0.6, -0.25, 0.0, 0.25, 0.6, 1.0], 'tam'),
    ('3 seviye, uclar dahil',         [-1.0, 0.0, 1.0],                         'uclar'),
    ('4 seviye, uclar dahil',         [-1.0, -0.25, 0.25, 1.0],                 'uclar'),
    ('3 seviye, ic aralik',           [-0.6, 0.0, 0.6],                         'ic'),
    ('3 seviye, dar aralik',          [-0.25, 0.0, 0.25],                       'dar'),
 ],
 'Kim vd. 2015 - 6500 TEU konteyner, model deneyi': [
    ('tam tarama',                    [-1.0, 0.0, 0.5, 1.0], 'tam'),
    ('3 seviye, uclar dahil',         [-1.0, 0.0, 1.0],      'uclar'),
    ('3 seviye, bas ucu kirpilmis',   [-1.0, 0.0, 0.5],      'ic'),
 ],
 'Kim vd. 2015 - Capesize dokme yuk, model deneyi': [
    ('tam tarama',                    [-2.0, -1.0, 0.0, 1.0], 'tam'),
    ('3 seviye, uclar dahil',         [-2.0, 0.0, 1.0],       'uclar'),
    ('3 seviye, bas ucu kirpilmis',   [-2.0, -1.0, 0.0],      'ic'),
 ],
 'Ziylan & Nas 2022 - 2478 TEU konteyner, model deneyi (ITTC-78)': [
    ('tam tarama',                    [-2.0, -1.0, 0.0, 1.0], 'tam'),
    ('3 seviye, uclar dahil',         [-2.0, 0.0, 1.0],       'uclar'),
    ('3 seviye, bas ucu kirpilmis',   [-2.0, -1.0, 0.0],      'ic'),
    ('3 seviye, kic ucu kirpilmis',   [-1.0, 0.0, 1.0],       'ic'),
 ],
 'Korkmaz vd. 2023 - RoPax, model deneyi, 17 kn': [
    ('tam tarama',                    [-1.5, 0.0, 1.5], 'tam'),
    ('2 seviye, bas ucu kirpilmis',   [-1.5, 0.0],      'ic'),
 ],
 'Martic vd. 2024 - KCS, sig su (h/T 1.78)': [
    ('tam tarama',                    [-0.4, -0.2, 0.0, 0.2, 0.4], 'tam'),
    ('3 seviye, uclar dahil',         [-0.4, 0.0, 0.4],            'uclar'),
    ('3 seviye, dar aralik',          [-0.2, 0.0, 0.2],            'dar'),
 ],
}


def mekanizma(optlar):
    """Kacirma mekanizmasini ayristirir.

    Her (tasarim, isletme noktasi) cifti u" c gruptan birine girer:
      bulundu    : gercek optimum seviyesi tasarimda var
      cozunurluk : gercek optimum tasarimin ARALIGI icinde ama o seviye orneklenmemis
      aralik     : gercek optimum tasarimin araliginin DISINDA
    Makalenin ana iddiasi bu ayrimda: aralik kacirmasi cozunurluk kacirmasindan
    pahali. Seviye sayisi ikisini de dogrudan belirlemiyor.
    """
    gruplar = {'bulundu': [], 'cozunurluk': [], 'aralik': []}
    for ds, opt in zip(VERI_SETLERI, optlar):
        tr = ds['trimler']
        for etiket, sec, kapsam in TASARIMLAR.get(ds['ad'], []):
            if kapsam == 'tam':
                continue
            idx = [tr.index(t) for t in sec]
            for k, row in ds['veri'].items():
                g = opt[k]
                j = min(idx, key=lambda m: row[m])
                bedel = (row[j] - row[g]) if ds['yanit'].endswith('[%]')                         else 100 * (row[j] - row[g]) / abs(row[g])
                if g in idx:
                    gruplar['bulundu'].append(bedel)
                elif min(sec) <= tr[g] <= max(sec):
                    gruplar['cozunurluk'].append(bedel)
                else:
                    gruplar['aralik'].append(bedel)
    print(chr(10) + '=' * 78)
    print('KACIRMA MEKANIZMASI - tum tasarim x isletme noktasi ciftleri havuzlanmis')
    print(f"{'grup':<44}{'cift':>7}{'ort.bedel':>12}{'en kotu':>11}")
    isim = {'bulundu': 'optimum seviyesi tasarimda var',
            'cozunurluk': 'COZUNURLUK kacirmasi (aralik icinde)',
            'aralik': 'ARALIK kacirmasi (aralik disinda)'}
    out = {}
    for g, v in gruplar.items():
        if not v:
            continue
        print(f"{isim[g]:<44}{len(v):>7}{sum(v)/len(v):>12.2f}{max(v):>11.2f}")
        out[g] = {'cift': len(v), 'ort': sum(v) / len(v), 'en_kotu': max(v)}
    if 'aralik' in out and 'cozunurluk' in out:
        print('   --> aralik kacirmasi, cozunurluk kacirmasindan %.1f kat pahali'
              % (out['aralik']['ort'] / out['cozunurluk']['ort']))
    return out


def kenar_ozet(optlar):
    """Veri setleri arasi ozet: optimum kenarda mi, ic noktada mi?"""
    print('\n' + '=' * 78)
    print('OPTIMUMUN KONUMU - VERI SETLERI ARASI OZET')
    print(f"{'veri seti':<48}{'nokta':>6}{'kenar':>7}{'ic':>5}  en iyi tau_bow")
    satirlar = []; tk = ti = 0
    for ds, opt in zip(VERI_SETLERI, optlar):
        tr = ds['trimler']; n = len(ds['veri'])
        k = sum(1 for i in opt.values() if i in (0, len(tr) - 1))
        eniyi = sorted({tr[i] for i in opt.values()})
        print(f"{ds['ad'][:46]:<48}{n:>6}{k:>7}{n-k:>5}  {eniyi}")
        satirlar.append({'ad': ds['ad'], 'nokta': n, 'kenar': k, 'ic': n - k,
                         'eniyi': eniyi, 'yanit': ds['yanit'], 'not': ds['not']})
        tk += k; ti += n - k
    print(f"{'TOPLAM':<48}{tk+ti:>6}{tk:>7}{ti:>5}")
    print(f"   --> isletme noktalarinin %{100*tk/(tk+ti):.0f}'inde optimum ARALIGIN UCUNDA")
    return satirlar


if __name__ == '__main__':
    import json

    optlar = [optimum_konumu(ds) for ds in VERI_SETLERI]
    ozet = kenar_ozet(optlar)
    mek = mekanizma(optlar)

    print('\n' + '=' * 78)
    print('AZALTILMIS TASARIMLARIN PERFORMANSI')
    print('bedel: yanit birimine gore % (yuzde yanitlarda yuzde puan)')

    tasarim_sonuc = []
    for ds, opt in zip(VERI_SETLERI, optlar):
        liste = TASARIMLAR.get(ds['ad'])
        if not liste:
            continue
        print(f"\n{ds['ad']}")
        print(f"{'tasarim':<34}{'trim':>5}{'yanlis':>10}{'ort.bedel':>12}{'en kotu':>11}")
        for etiket, sec, kapsam in liste:
            r = azaltilmis(ds, opt, sec, etiket)
            if r:
                r.update({'veriseti': ds['ad'], 'kapsam': kapsam, 'seviye': len(sec),
                          'trimler': sec, 'etiket': etiket})
                tasarim_sonuc.append(r)

    print(f"\n{'yanlis secimin yakit bedeli (Vasilev)':<34}{'gunluk':>16}{'yillik':>18}")
    yakit_sonuc = []
    for etiket, sec in [('3 seviye, uclar dahil', [-1.5, 0.0, 1.5]),
                        ('3 seviye, ic aralik', [-1.0, 0.0, 1.0]),
                        ('4 seviye, bildirimizin araligi', [-1.0, -0.5, 0.0, 0.5]),
                        ('3 seviye, dar aralik', [-0.5, 0.0, 0.5])]:
        yakit_sonuc.append(yakit(sec, etiket))

    with open('sonuclar.json', 'w', encoding='utf-8') as f:
        json.dump({'ozet': ozet, 'mekanizma': mek, 'tasarimlar': tasarim_sonuc, 'yakit': yakit_sonuc,
                   'veri': [{'ad': d['ad'], 'yanit': d['yanit'], 'trimler': d['trimler'],
                             'not': d['not'],
                             'veri': {str(k): v for k, v in d['veri'].items()}}
                            for d in VERI_SETLERI],
                   'dfoc_vasilev': {str(k): v for k, v in DFOC_VAS.items()}},
                  f, ensure_ascii=False, indent=1)
    print('\n--> sonuclar.json yazildi')
