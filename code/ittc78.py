# -*- coding: utf-8 -*-
"""ITTC-57/78 cercevesinde CFD sonuclarinin bagimsiz dogrulamasi.

Mantik:
  1. Tablo 3'teki R_T ve C_T birbirine gore tutarli; S = R_T/(0.5 rho V^2 C_T)
     geri hesaplanir. Olasi bir olcek/birim kaymasi bu oranda birbirini goturur,
     yani S dogru cikiyorsa iki sutun tutarlidir.
  2. S, gemi ana boyutlariyla karsilastirilir (S/(L*B) ve Denny-Mumford).
  3. ITTC-57 surtunme cizgisi ve bir form faktoru ile C_T ayristirilir:
        C_W = C_T - (1+k) C_F
     Dogru bir CFD'de C_W pozitif olmali ve Froude sayisiyla artmali.
     Bu, ITTC-78 performans tahmin yonteminin dayandigi ayristirmanin ta kendisi.
  4. Ayni ayristirma, C_T sutununun olasi birim olceklerinde tekrarlanir;
     yalnizca bir olcek fiziksel sonuc verir.

Form faktoru: Watanabe yaklasimi, yalnizca L, B, T, C_B ister (elimizde var).
"""
import io, math, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

RHO = 1025.0          # kg/m3, deniz suyu 15 C
NU = 1.1892e-6        # m2/s
KN = 0.514444
G = 9.81
KS = 150e-6           # m, standart puruzluluk

# gemi: (L_OA, B, T_design, C_B, deplasman t)
GEMI = {
    'Neptun':   (99.99, 12.50, 4.27, 0.839, 4934),
    'Alfa Sun': (99.89, 16.60, 6.70, 0.755, 8143),
    'Ilgaz':    (99.95, 17.00, 5.50, 0.713, 6397),
    'ELA-S':    (104.42, 16.10, 5.80, 0.875, 8189),
}

# run, gemi, trim, su cekimi, V[kn], R_T(tablo), C_T(tablo)
KOSU = [
    (1, 'Neptun', 1.0, 4.48, 14.38, 19.18, 3.71),
    (2, 'Neptun', 0.5, 4.91, 13.13, 14.98, 3.31),
    (3, 'Neptun', 0.0, 3.63, 11.88, 10.77, 3.45),
    (4, 'Neptun', -0.5, 4.06, 10.63, 6.57, 2.48),
    (5, 'Alfa Sun', 1.0, 6.00, 10.00, 7.16, 2.40),
    (6, 'Alfa Sun', 0.5, 6.40, 11.00, 9.35, 2.49),
    (7, 'Alfa Sun', 0.0, 6.70, 12.00, 12.07, 2.63),
    (8, 'Alfa Sun', -0.5, 7.00, 13.00, 14.67, 2.66),
    (9, 'Ilgaz', 1.0, 5.23, 15.75, 23.75, 3.50),
    (10, 'Ilgaz', 0.5, 4.68, 17.25, 38.85, 5.13),
    (11, 'Ilgaz', 0.0, 6.33, 12.75, 13.72, 2.75),
    (12, 'Ilgaz', -0.5, 5.78, 14.25, 17.97, 3.08),
    (13, 'ELA-S', 1.0, 5.00, 9.00, 5.79, 2.23),
    (14, 'ELA-S', 0.5, 5.30, 10.00, 7.44, 2.26),
    (15, 'ELA-S', 0.0, 5.79, 11.00, 9.54, 2.30),
    (16, 'ELA-S', -0.5, 6.10, 12.00, 12.93, 2.55),
]

# Tablo 3'teki C_T sutununun etiketi "x 10^7". Denenen olcekler:
OLCEKLER = [('etiketteki gibi, C_T x 1e-7', 1e-7),
            ('C_T x 1e-5', 1e-5),
            ('C_T x 1e-3 (etiket 10^3 olmali)', 1e-3),
            ('C_T x 1e-2', 1e-2)]


def cf_ittc57(re):
    return 0.075 / (math.log10(re) - 2.0) ** 2


def form_faktoru(L, B, T, CB):
    """Watanabe yaklasimi: yalnizca ana boyutlardan (1+k)."""
    return 1.0 + 0.095 + 25.6 * CB / ((L / B) ** 2 * math.sqrt(B / T))


def dcf_puruzluluk(L, re):
    """ITTC-78 puruzluluk odenegi."""
    return 0.044 * ((KS / L) ** (1.0 / 3.0) - 10.0 * re ** (-1.0 / 3.0)) + 0.000125


print('=' * 74)
print('ADIM 1 - Tablo 3 kendi icinde tutarli mi?  S = R_T / (0.5 rho V^2 C_T)')
print('=' * 74)
print('Olcek kaymasi orani goturdugu icin S, etiketten bagimsiz tek bir deger.')
print()
print('%4s %-9s %6s %10s %9s %9s %9s' %
      ('kosu', 'gemi', 'V[kn]', 'S geri[m2]', 'S/(L*B)', 'S Denny', 'fark %'))
S_GERI = {}
for no, ad, tr, T, Vkn, RT, CT in KOSU:
    L, B, Td, CB, D = GEMI[ad]
    V = Vkn * KN
    S = RT / (0.5 * RHO * V * V * (CT * 1e-7))
    S_GERI[no] = S
    # Denny-Mumford: S = 1.7 L T + hacim / T
    hacim = D * 1000.0 / RHO
    s_denny = 1.7 * L * T + hacim / T
    print('%4d %-9s %6.2f %10.0f %9.3f %9.0f %9.1f'
          % (no, ad, Vkn, S, S / (L * B), s_denny, 100 * (S - s_denny) / s_denny))

print()
print('Yorum: S/(L*B) tipik olarak 1.0-1.6 araliginda olur. Denny-Mumford ile')
print('fark birkac yuzde ise iki sutun birbirine gore tutarli demektir.')

print()
print('=' * 74)
print('ADIM 2 - C_T hangi olcekte fiziksel?  C_W = C_T - (1+k) C_F')
print('=' * 74)
for ad_olcek, carp in OLCEKLER:
    cw_hepsi, negatif = [], 0
    for no, ad, tr, T, Vkn, RT, CT in KOSU:
        L, B, Td, CB, D = GEMI[ad]
        V = Vkn * KN
        Lpp = 0.95 * L
        re = V * Lpp / NU
        cf = cf_ittc57(re)
        k1 = form_faktoru(Lpp, B, T, CB)
        cw = CT * carp - k1 * cf
        cw_hepsi.append(cw)
        if cw <= 0:
            negatif += 1
    ort = sum(cw_hepsi) / len(cw_hepsi)
    print('%-34s C_W ort %+10.3e   negatif %2d/16  %s'
          % (ad_olcek, ort, negatif,
             'FIZIKSEL DEGIL' if negatif else 'tutarli'))

print()
print('=' * 74)
print('ADIM 3 - Fiziksel olcekte tam ITTC-57/78 ayristirmasi')
print('=' * 74)
CARP = 1e-3
print('C_T = %s x (tablo degeri).  (1+k): Watanabe' % CARP)
print()
print('%4s %-9s %6s %6s %8s %7s %9s %9s %8s' %
      ('kosu', 'gemi', 'Fn', 'Re e8', '(1+k)', 'C_F e3', '(1+k)C_F', 'C_W e3',
       'C_W/C_T'))
gemi_cw = {}
for no, ad, tr, T, Vkn, RT, CT in KOSU:
    L, B, Td, CB, D = GEMI[ad]
    V = Vkn * KN
    Lpp = 0.95 * L
    re = V * Lpp / NU
    fn = V / math.sqrt(G * Lpp)
    cf = cf_ittc57(re)
    k1 = form_faktoru(Lpp, B, T, CB)
    ct = CT * CARP
    cw = ct - k1 * cf
    gemi_cw.setdefault(ad, []).append((fn, cw, ct))
    print('%4d %-9s %6.3f %6.2f %8.3f %7.3f %9.3e %9.3f %8.1f%%'
          % (no, ad, fn, re / 1e8, k1, cf * 1e3, k1 * cf, cw * 1e3,
             100 * cw / ct))

print()
print('ADIM 4 - C_W Froude sayisiyla artiyor mu? (her gemi kendi icinde)')
print()
tutarli = 0
for ad in ('Neptun', 'Alfa Sun', 'Ilgaz', 'ELA-S'):
    veri = sorted(gemi_cw[ad])
    artis = all(veri[i][1] <= veri[i + 1][1] for i in range(len(veri) - 1))
    tutarli += 1 if artis else 0
    print('  %-9s Fn %.3f->%.3f   C_W e3 %s   %s'
          % (ad, veri[0][0], veri[-1][0],
             ' '.join('%.2f' % (v[1] * 1e3) for v in veri),
             'monoton artiyor' if artis else 'monoton DEGIL'))
print()
print('  %d/4 gemide C_W Froude sayisiyla monoton artiyor.' % tutarli)

print()
print('=' * 74)
print('ADIM 5 - ITTC-78 ile tam olcek direnc ve etkin guc')
print('=' * 74)
print('%4s %-9s %9s %9s %10s %10s' %
      ('kosu', 'gemi', 'R_T tablo', 'R_T [kN]', 'P_E [kW]', 'R_T/disp'))
for no, ad, tr, T, Vkn, RT, CT in KOSU:
    L, B, Td, CB, D = GEMI[ad]
    V = Vkn * KN
    Lpp = 0.95 * L
    re = V * Lpp / NU
    S = S_GERI[no]
    dcf = dcf_puruzluluk(Lpp, re)
    ct_s = CT * CARP + dcf
    rt = ct_s * 0.5 * RHO * V * V * S
    print('%4d %-9s %9.2f %9.1f %10.0f %10.2f'
          % (no, ad, RT, rt / 1e3, rt * V / 1e3, rt / (D * 1000 * 9.81) * 1e3))
print()
print('R_T [kN] sutunu, tablo degerinin 1e4 ile carpilmis hali olmali.')
print('Dogrulanacak: tablo sutun basliklari R_T icin x10^4 N, C_T icin x10^3.')
