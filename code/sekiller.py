# -*- coding: utf-8 -*-
"""Makale sekilleri. Veriler altkume_analizi.py'den alinir, yeniden hesaplanmaz."""
import os, sys, io, random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import altkume_analizi as A
import tam_altkume as T

# stdout'u altkume_analizi zaten utf-8'e sariyor; ikinci kez sarmak akisi kapatiyor
CIK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'sekiller')

# ---- dergi stili (T&F / SAOS: Times benzeri, gri tonda da okunur) ----
plt.rcParams.update({
    'font.family': 'STIXGeneral', 'mathtext.fontset': 'stix',
    'font.size': 8.5, 'axes.labelsize': 8.5, 'axes.titlesize': 8.5,
    'xtick.labelsize': 8, 'ytick.labelsize': 8, 'legend.fontsize': 7.5,
    'axes.linewidth': 0.6, 'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
    'xtick.direction': 'out', 'ytick.direction': 'out',
    'axes.spines.top': False, 'axes.spines.right': False,
    'lines.linewidth': 1.0, 'savefig.dpi': 400, 'figure.dpi': 140,
    'legend.frameon': False, 'axes.grid': False, 'hatch.linewidth': 0.5,
})
MAVI, TURUNCU, GRI, ACIK = '#1F6FB2', '#C1521D', '#555555', '#BBBBBB'
TAU = chr(964)
NL = chr(10)
EKSI = chr(8722)

ETIKET = {
 'Vasilev vd. 2024 - RO-RO 158 m, tam olcek CFD':
    ('Vasilev et al. (2024)', 'RO-RO, full-scale CFD', ' m'),
 'Kim vd. 2015 - 6500 TEU konteyner, model deneyi':
    ('Kim et al. (2015) a', '6500 TEU container, EFD', ' m'),
 'Kim vd. 2015 - Capesize dokme yuk, model deneyi':
    ('Kim et al. (2015) b', 'Capesize bulker, EFD', ' m'),
 'Korkmaz vd. 2023 - RoPax, model deneyi, 17 kn':
    ('Korkmaz et al. (2023)', 'RoPax, EFD + CFD', ' m'),
 'Martic vd. 2024 - KCS, sig su (h/T 1.78)':
    ('Martic et al. (2024)', 'KCS, shallow water', chr(176)),
 'Shivachev vd. 2017 - KCS 1:75, Fn 0.26':
    ('Shivachev et al. (2017)', 'KCS 1:75, EFD + CFD', chr(176)),
 'Ziylan & Nas 2022 - 2478 TEU konteyner, model deneyi (ITTC-78)':
    ('Ziylan and Nas (2022)', '2478 TEU container, EFD', ' m'),
}
SIRA = ['Vasilev vd. 2024 - RO-RO 158 m, tam olcek CFD',
        'Kim vd. 2015 - 6500 TEU konteyner, model deneyi',
        'Kim vd. 2015 - Capesize dokme yuk, model deneyi',
        'Korkmaz vd. 2023 - RoPax, model deneyi, 17 kn',
        'Martic vd. 2024 - KCS, sig su (h/T 1.78)',
        'Shivachev vd. 2017 - KCS 1:75, Fn 0.26',
        'Ziylan & Nas 2022 - 2478 TEU konteyner, model deneyi (ITTC-78)']
DS = {d['ad']: d for d in A.VERI_SETLERI}


def opt_idx(ds):
    return {k: min(range(len(v)), key=lambda m: v[m]) for k, v in ds['veri'].items()}


def bedel(ds, row, j, g):
    if ds['yanit'].endswith('[%]'):
        return row[j] - row[g]
    return 100.0 * (row[j] - row[g]) / abs(row[g])


def kaydet(fig, ad):
    for uz in ('pdf', 'png'):
        fig.savefig(os.path.join(CIK, ad + '.' + uz), bbox_inches='tight',
                    pad_inches=0.02)
    plt.close(fig)
    print('  ' + ad + '.pdf / .png')


# ===================================================== SEKIL 1
def sekil1():
    fig, ax = plt.subplots(figsize=(6.1, 3.1))
    for r, ad in enumerate(SIRA):
        ds = DS[ad]
        tr = ds['trimler']
        n = len(tr)
        y = len(SIRA) - 1 - r
        poz = [2.0 * i / (n - 1) - 1.0 for i in range(n)]
        ax.plot([-1, 1], [y, y], '-', color=ACIK, lw=0.8, zorder=1)
        for p in poz:
            ax.plot([p, p], [y - 0.10, y + 0.10], '-', color=ACIK, lw=0.8, zorder=1)
        opt = opt_idx(ds)
        hepsi = list(opt.values())
        sayac = {}
        kenar = 0
        for k, i in sorted(opt.items(), key=lambda t: str(t[0])):
            m = sayac.get(i, 0)
            sayac[i] = m + 1
            dy = (m - 0.5 * (hepsi.count(i) - 1)) * 0.115
            if i in (0, n - 1):
                kenar += 1
                ax.plot(poz[i], y + dy, 'o', ms=4.2, mfc=MAVI, mec='white',
                        mew=0.5, zorder=3)
            else:
                ax.plot(poz[i], y + dy, 's', ms=4.2, mfc='white', mec=TURUNCU,
                        mew=1.0, zorder=3)
        lab, alt, birim = ETIKET[ad]
        ax.text(-1.14, y + 0.12, lab, ha='right', va='center', fontsize=8)
        ax.text(-1.14, y - 0.20, alt, ha='right', va='center', fontsize=6.6, color=GRI)
        ax.text(1.09, y, '%d/%d' % (kenar, len(opt)), ha='left', va='center',
                fontsize=7.5, color=MAVI if kenar > len(opt) / 2.0 else GRI)
        rng = ('%+.3g to %+.3g%s' % (tr[0], tr[-1], birim)).replace('-', EKSI)
        ax.text(1.32, y, rng, ha='left', va='center', fontsize=6.6, color=GRI)
    ax.axvline(0, color=ACIK, lw=0.6, ls=(0, (3, 3)), zorder=0)
    ax.set_xlim(-1.08, 2.15)
    ax.set_ylim(-0.75, len(SIRA) - 0.25)
    ax.set_yticks([])
    ax.spines['left'].set_visible(False)
    ax.set_xticks([-1, -0.5, 0, 0.5, 1])
    ax.set_xticklabels(['stern end', '', 'even keel', '', 'bow end'])
    ax.set_xlabel('position of the optimum within the sampled trim range')
    ax.text(1.09, len(SIRA) - 0.48, 'at end', fontsize=6.6, color=GRI, ha='left')
    ax.text(1.32, len(SIRA) - 0.48, 'sampled range', fontsize=6.6, color=GRI, ha='left')
    ax.legend(handles=[
        Line2D([], [], marker='o', ls='none', ms=4.2, mfc=MAVI, mec='white', mew=0.5,
               label='range-bounded: the window limits the result,' + NL
                     + 'which gives a direction and not an optimum'),
        Line2D([], [], marker='s', ls='none', ms=4.2, mfc='white', mec=TURUNCU, mew=1.0,
               label='range-spanning: the optimum is located' + NL
                     + 'inside the window')],
        loc='lower center', bbox_to_anchor=(0.36, -0.46), ncol=2, handletextpad=0.4,
        labelspacing=0.5)
    kaydet(fig, 'Sekil1_optimum_konumu')


# ===================================================== SEKIL 2
def sekil2():
    """Tam sayim: butun altkumeler. (a) seviye sayisi x aralik kapsamasi,
    (b) ayni ayrim, yanit degiskeni turune gore."""
    hepsi = [p for v in T.HEPSI.values() for p in v]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.4, 2.9),
                                 gridspec_kw={'width_ratios': [1.0, 0.95],
                                              'wspace': 0.34})

    # --- (a) seviye sayisi, kapsama ayrik
    sev = sorted({p['seviye'] for p in hepsi})
    kaps, dis = [], []
    for s_ in sev:
        a = [p['bedel'] for p in hepsi if p['seviye'] == s_ and p['grup'] != 'aralik']
        b = [p['bedel'] for p in hepsi if p['seviye'] == s_ and p['grup'] == 'aralik']
        kaps.append(sum(a) / len(a) if a else float('nan'))
        dis.append(sum(b) / len(b) if b else float('nan'))
    a1.plot(sev, dis, '-', color=TURUNCU, marker='^', ms=5.5, mfc='white',
            mec=TURUNCU, mew=1.2, label='range excludes the optimum', zorder=3)
    a1.plot(sev, kaps, '-', color=MAVI, marker='o', ms=5.0, mfc=MAVI,
            mec='white', mew=0.6, label='range contains the optimum', zorder=3)
    for x, y in zip(sev, kaps):
        a1.text(x, y + 0.26, '%.2f' % y, ha='center', fontsize=6.6, color=MAVI)
    for x, y in zip(sev, dis):
        a1.text(x, y + 0.26, '%.2f' % y, ha='center', fontsize=6.6, color=TURUNCU)
    a1.set_xticks(sev)
    a1.set_xlim(1.6, max(sev) + 0.4)
    a1.set_ylim(-0.5, 7.2)
    a1.set_xlabel('number of trim levels in the design')
    a1.set_ylabel('mean penalty in the response (%)')
    a1.text(-0.20, 1.06, '(a)', transform=a1.transAxes, va='top', fontsize=8.5)
    a1.legend(loc='upper right', handletextpad=0.4, labelspacing=0.25,
              bbox_to_anchor=(1.02, 1.02))

    # --- (b) yanit turune gore ayni ayrim
    TUR_AD = {'guc': 'power-like' + NL + '(P$_B$, P$_D$, BHP)',
              'direnc': 'resistance' + NL + '(R$_T$)'}
    konum = 0
    etiketler = []
    for t in ('guc', 'direnc'):
        v = [p for ad, vv in T.HEPSI.items() if T.TUR[ad] == t for p in vv]
        for g, renk, isar in (('cozunurluk', MAVI, 'o'), ('aralik', TURUNCU, '^')):
            b = [p['bedel'] for p in v if p['grup'] == g]
            random.seed(11 + konum)
            for y in b:
                a2.plot(konum + random.uniform(-0.16, 0.16), y, 'o', ms=2.2,
                        mfc=renk, mec='none', alpha=0.28, zorder=2)
            o = sum(b) / len(b)
            a2.plot([konum - 0.3, konum + 0.3], [o, o], '-', color='black',
                    lw=1.4, zorder=4)
            a2.text(konum, o + 0.7, '%.2f%%' % o, ha='center', va='bottom',
                    fontsize=7.2)
            etiketler.append('resolution' if g == 'cozunurluk' else 'range')
            konum += 1
        konum += 0.6
    a2.set_xticks([0, 1, 2.6, 3.6])
    a2.set_xticklabels(etiketler, fontsize=7.2)
    a2.set_xlim(-0.6, 4.5)
    a2.set_ylim(-1.5, 29.0)
    a2.set_ylabel('penalty at a single operating point (%)')
    a2.text(-0.20, 1.06, '(b)', transform=a2.transAxes, va='top', fontsize=8.5)
    for x, t in ((0.5, 'guc'), (3.1, 'direnc')):
        a2.text(x, 27.6, TUR_AD[t].split(NL)[0], ha='center', fontsize=7.6)
        a2.text(x, 25.6, TUR_AD[t].split(NL)[1], ha='center', fontsize=6.8,
                color=GRI)
    kaydet(fig, 'Sekil2_seviye_mi_aralik_mi')
    return hepsi


# ===================================================== SEKIL 3
def sekil3():
    ds = DS[SIRA[0]]
    tr = ds['trimler']
    cek = [7.5, 8.0, 8.7]
    hiz = [12.5, 15.0, 18.0]
    tonlar = ['#8CBEDC', '#2E7EB8', '#0E3F63']
    isaret = ['o', 's', '^']
    fig, axs = plt.subplots(1, 3, figsize=(6.4, 2.4), sharey=True)
    j0 = tr.index(0.0)
    for c, (ax, T) in enumerate(zip(axs, cek)):
        for h, (V, ton, mk) in enumerate(zip(hiz, tonlar, isaret)):
            row = ds['veri'][(T, V)]
            y = [100.0 * (p - row[j0]) / row[j0] for p in row]
            ax.plot(tr, y, '-', color=ton, marker=mk, ms=3.6, mew=0.7,
                    mfc='white' if h else ton, mec=ton, label='%.1f kn' % V,
                    zorder=3)
            i = min(range(len(row)), key=lambda m: row[m])
            ax.plot(tr[i], y[i], 'o', ms=8.5, mfc='none', mec=TURUNCU, mew=1.1,
                    zorder=4)
        ax.axhline(0, color=ACIK, lw=0.6, zorder=1)
        ax.axvline(0, color=ACIK, lw=0.6, ls=(0, (3, 3)), zorder=1)
        ax.set_xlim(-1.8, 1.8)
        ax.set_xticks([-1.5, -0.75, 0, 0.75, 1.5])
        ax.set_xticklabels([EKSI + '1.5', EKSI + '0.75', '0', '0.75', '1.5'])
        ax.set_title('T = %.1f m' % T, pad=3)
        ax.set_xlabel('trim ' + TAU + ' (m, + by bow)')
        if c == 0:
            ax.set_ylabel('brake power relative' + NL + 'to even keel (%)')
    axs[0].plot([], [], 'o', ms=8.5, mfc='none', mec=TURUNCU, mew=1.1,
                label='optimum within' + NL + 'the sampled range')
    axs[0].legend(loc='lower left', handletextpad=0.5, labelspacing=0.3,
                  borderpad=0.1, bbox_to_anchor=(-0.02, -0.03))
    kaydet(fig, 'Sekil3_referans_trim_egrileri')


# ===================================================== SEKIL 4
def sekil4():
    ds = DS[SIRA[0]]
    tr = ds['trimler']
    guc = ds['veri']
    tas = [('three levels, ends included', [-1.5, 0.0, 1.5], MAVI),
           ('three levels, interior range', [-1.0, 0.0, 1.0], TURUNCU),
           ('four levels, narrow range', [-1.0, -0.5, 0.0, 0.5], TURUNCU),
           ('three levels, narrow range', [-0.5, 0.0, 0.5], TURUNCU)]
    fig, ax = plt.subplots(figsize=(4.6, 2.2))
    for r, (lab, sec, rnk) in enumerate(tas):
        idx = [tr.index(t) for t in sec]
        top = 0.0
        n = 0
        for k, dfoc in A.DFOC_VAS.items():
            j = min(idx, key=lambda m: guc[k][m])
            g = min(range(len(guc[k])), key=lambda m: guc[k][m])
            top += dfoc[j] - dfoc[g]
            n += 1
        yil = 280.0 * top / n
        y = len(tas) - 1 - r
        # her cubuk dogrudan etiketli; renk yedek kanal, tek basina tasiyici degil
        ax.barh(y, yil, height=0.46, color=rnk, edgecolor='none', zorder=3)
        ax.text(yil + 4, y, '%.0f t' % yil, va='center', fontsize=8)
        ax.text(-6, y, lab, ha='right', va='center', fontsize=8)
    ax.set_yticks([])
    ax.spines['left'].set_visible(False)
    ax.set_xlim(0, 300)
    ax.set_ylim(-0.6, len(tas) - 0.4)
    ax.set_xlabel('excess fuel consumption from selecting the wrong trim' + NL
                  + '(t/year, 280 sailing days)')
    kaydet(fig, 'Sekil4_yakit_bedeli')


# ===================================================== SEKIL 5
# Kaynak: Guney & Ince (2026) ICSOS2026-18, Tablo 4. Degerler bildirinin PDF
# metin katmanindan cikarilip teyit edildi. Trim seviyeleri {-1.0,-0.5,0,+0.5} m,
# bildirinin kendi isaretiyle verilmistir.
ICSOS = [
    ('Ilgaz',    'chemical tanker',  0.0, 65.7),
    ('Neptun',   'container',        0.5, 38.0),
    ('ELA-S',    'general cargo',   -1.0, 13.7),
    ('Alfa Sun', 'bulk carrier',    -1.0, 10.2),
]
ICSOS_SEVIYE = [-1.0, -0.5, 0.0, 0.5]


def sekil5():
    tr = ICSOS_SEVIYE
    fig, ax = plt.subplots(figsize=(5.4, 2.35))
    for r, (ad, tip, eniyi, yayilim) in enumerate(ICSOS):
        y = len(ICSOS) - 1 - r
        ax.plot([tr[0], tr[-1]], [y, y], '-', color=ACIK, lw=0.8, zorder=1)
        for t in tr:
            ax.plot([t, t], [y - 0.11, y + 0.11], '-', color=ACIK, lw=0.8, zorder=1)
        uc = eniyi in (tr[0], tr[-1])
        if uc:
            ax.plot(eniyi, y, 'o', ms=5.0, mfc=MAVI, mec='white', mew=0.5, zorder=3)
        else:
            ax.plot(eniyi, y, 's', ms=5.0, mfc='white', mec=TURUNCU, mew=1.1, zorder=3)
        ax.text(tr[0] - 0.07, y + 0.13, ad, ha='right', va='center', fontsize=8)
        ax.text(tr[0] - 0.07, y - 0.20, tip, ha='right', va='center', fontsize=6.6,
                color=GRI)
        ax.text(tr[-1] + 0.09, y, '%.1f%%' % yayilim, ha='left', va='center',
                fontsize=7.5, color=GRI)
    ax.text(tr[-1] + 0.09, len(ICSOS) - 0.50, 'spread in $C_T$',
            ha='left', fontsize=6.6, color=GRI)
    ax.set_xlim(tr[0] - 0.05, tr[-1] + 0.46)
    ax.set_ylim(-0.7, len(ICSOS) - 0.25)
    ax.set_yticks([])
    ax.spines['left'].set_visible(False)
    ax.set_xticks(tr)
    ax.set_xticklabels([(EKSI + '1.0'), (EKSI + '0.5'), '0', '+0.5'])
    ax.set_xlabel('trim level sampled by the L16 array ' + TAU
                  + ' (m, sign as defined in the source study)')
    ax.legend(handles=[
        Line2D([], [], marker='o', ls='none', ms=5.0, mfc=MAVI, mec='white', mew=0.5,
               label='best trim at an end of the window'),
        Line2D([], [], marker='s', ls='none', ms=5.0, mfc='white', mec=TURUNCU,
               mew=1.1, label='best trim at an interior level')],
        loc='lower center', bbox_to_anchor=(0.38, -0.62), ncol=2, handletextpad=0.4)
    kaydet(fig, 'Sekil5_ICSOS_taramasi')


# ============================================ ICSOS SEKILLERI
# Kaynak: Guney & Ince (2026) ICSOS2026-18, Tablo 3 ve Tablo 6.
# Trim isaretleri makalenin konvansiyonuna cevrildi (pozitif = basa trim);
# bildiride ayni degerler ters isaretle veriliyor.
ICSOS_TRIM = [-0.5, 0.0, 0.5, 1.0]
ICSOS_CT = {                       # C_T x 10^3, Tablo 3
    'Neptun':   ('container',       [2.48, 3.45, 3.31, 3.71], False),
    'Alfa Sun': ('bulk carrier',    [2.66, 2.63, 2.49, 2.40], False),
    'Ilgaz':    ('chemical tanker', [3.08, 2.75, 5.13, 3.50], True),
    'ELA-S':    ('general cargo',   [2.55, 2.30, 2.26, 2.23], False),
}
ICSOS_BETA = [('Speed', 0.94, 0.84), ('Draught', 0.01, 0.32), ('Trim', 0.10, 0.11)]


def sekil_icsos_trim():
    tonlar = ['#0E3F63', '#2E7EB8', '#C1521D', '#7FA8A0']
    isaret = ['o', 's', 'D', '^']
    fig, ax = plt.subplots(figsize=(4.9, 3.0))
    for (ad, (tip, ct, kesik)), ton, mk in zip(ICSOS_CT.items(), tonlar, isaret):
        if kesik:
            ax.plot(ICSOS_TRIM, ct, ls='none', marker=mk, ms=5.0, mfc='white',
                    mec=ton, mew=1.3, label=ad + ' (' + tip + ')', zorder=3)
        else:
            ax.plot(ICSOS_TRIM, ct, '-', color=ton, marker=mk, ms=4.4, mew=0.8,
                    mfc=ton, mec='white', label=ad + ' (' + tip + ')', zorder=3)
        i = min(range(4), key=lambda m: ct[m])
        ax.plot(ICSOS_TRIM[i], ct[i], 'o', ms=9.5, mfc='none', mec=TURUNCU,
                mew=1.2, zorder=4)
    ax.axvline(0, color=ACIK, lw=0.6, ls=(0, (3, 3)), zorder=1)
    ax.set_xticks(ICSOS_TRIM)
    ax.set_xticklabels([EKSI + '0.5', '0', '+0.5', '+1.0'])
    ax.set_xlim(-0.72, 1.45)
    ax.set_xlabel('trim level of the L16 array ' + TAU + ' (m, + by bow)')
    ax.set_ylabel('$C_T$ ' + chr(215) + ' 10$^{3}$')
    ax.plot([], [], 'o', ms=9.5, mfc='none', mec=TURUNCU, mew=1.2,
            label='lowest sampled cell')
    ax.legend(loc='upper right', handletextpad=0.5, labelspacing=0.3,
              borderpad=0.2, fontsize=7)
    kaydet(fig, 'Sekil_ICSOS_trim_tepkisi')


def sekil_icsos_beta():
    fig, ax = plt.subplots(figsize=(4.6, 2.1))
    y = range(len(ICSOS_BETA))
    h = 0.34
    for k, (ad, br, bc) in enumerate(ICSOS_BETA):
        ax.barh(k + h / 2, br, height=h, color=MAVI, edgecolor='none', zorder=3)
        ax.barh(k - h / 2, bc, height=h, color='#8CBEDC', edgecolor='none', zorder=3)
        ax.text(br + 0.015, k + h / 2, '%.2f' % br, va='center', fontsize=7.2)
        ax.text(bc + 0.015, k - h / 2, '%.2f' % bc, va='center', fontsize=7.2)
    ax.set_yticks(list(y))
    ax.set_yticklabels([a for a, _, _ in ICSOS_BETA])
    ax.set_xlim(0, 1.08)
    ax.set_xlabel('standardised regression coefficient |' + chr(946) + '|')
    ax.invert_yaxis()
    ax.legend(handles=[
        Line2D([], [], color=MAVI, lw=6, label='on $R_T$'),
        Line2D([], [], color='#8CBEDC', lw=6, label='on $C_T$')],
        loc='lower right', handlelength=1.1, handletextpad=0.5, fontsize=7.4)
    kaydet(fig, 'Sekil_ICSOS_beta')


if __name__ == '__main__':
    print('sekiller -> ' + os.path.abspath(CIK))
    sekil1()
    sekil2()
    sekil3()
    sekil4()
    sekil5()
    sekil_icsos_trim()
    sekil_icsos_beta()
    print('tamam')
