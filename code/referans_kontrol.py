# -*- coding: utf-8 -*-
"""Her kaynagi, ona yapilan atiflarla ve kaynagin PDF'iyle yan yana koyan
kontrol klasorunu uretir. Amac: elle dogrulanabilsin.

PDF eslestirmesi kaynaklar/00_INDEKS.md'ye dayanan elle kurulmus haritadan
gelir. Otomatik DOI aramasi denendi ve yanlis sonuc verdi: bir kaynagin DOI'si,
o kaynagi ATIF YAPAN PDF'in kaynakcasinda da geciyor (Box 1988 -> kendi
bildirimiz gibi). Bu yuzden harita elle yazildi.
"""
import io, os, re, glob, shutil, sys, unicodedata


def sade(t):
    """Turkce harfleri ASCII'ye indir. NFKD noktasiz i'yi cozmuyor, elle esle."""
    t = t.replace('ı', 'i').replace('İ', 'I')
    d = unicodedata.normalize('NFKD', t)
    return ''.join(c for c in d if not unicodedata.combining(c))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
MAKALE = os.path.join(KOK, 'makale')
PDFDIZIN = os.path.join(KOK, 'kaynaklar')
CIK = r'C:\Users\mcagr\Desktop\Referans_Kontrol'

# Cumle sinirlari: "et al.", "Fig.", "Eq.", "vs.", bas harf kisaltmalari ve
# ondalik ayirici nokta sinir sayilmaz; sonrasinda buyuk harf aranir.
SINIR = re.compile(
    r'(?<!\bal)(?<!\bFig)(?<!\bEq)(?<!\bTab)(?<!\bvs)(?<!\bapprox)'
    r'(?<!\bcf)(?<!\bi\.e)(?<!\be\.g)(?<![A-Z])(?<!\d)'
    r'\.\s+(?=[A-Z(—])')

# Onceki calismada tam metinden teyit edilmis / edilememis sayisal iddialar.
TEYIT = {
    'Seok2019': ('OK', 'Tarama 16 kosu, yanit yuzeyi 32 kosu ("Thirty cases") tam '
                       'metinden teyit edildi. Dogrulama kosusu uyumu ~%1; makalede '
                       'onceden %1.2 yaziyordu, duzeltildi. PDF elimizde yok, teyit '
                       'tam metin uzerinden yapildi.'),
    'Miao2020': ('DUZELTILDI', "HATA BULUNDU: kaynakcada yazdigimiz baslik ('Hull form "
                               "optimization of a container ship based on Kriging "
                               "surrogate model with cross-validation') bu DOI'ye ait "
                               'degildi. Crossref kaydina gore dogru baslik "Hull Form '
                               'Optimization Based on an NM+CFD Integrated Method for '
                               'KCS". Duzeltildi. Metindeki atif nitel (ardisik/uyarlanir '
                               'semalar daha ucuza daha iyi optimuma ulasiyor), NM+CFD '
                               'calismasi bunu destekliyor, sayisal deger baglanmamis.'),
    'AnantKishore2017': ('OK', "Crossref kaydinda soyadi 'Anant Kishore', adi 'Ravi'. "
                               "Literaturde cogu zaman 'Kishore RA' olarak aniliyor. "
                               'Yayincinin kendi kaydi esas alindi, metin ici atif da '
                               'ona gore yazildi. Baska bir bicim tercih edilirse tek '
                               'satirlik degisiklik.'),
    'Mentese2021': ('OK', "Yazar sirasi celiskisi cozuldu: Crossref deposu tek yazar "
                          "olarak 'BAYRAKTAR, Seyfettin' kaydetmis, ama derginin "
                          "makale sayfasi hem kunyesinde ('by Arif Mentese and "
                          "Seyfettin Bayraktar') hem onerilen atifinda ('Mentese, Arif "
                          "and Bayraktar, Seyfettin (2021)') Mentese'yi ilk yazar "
                          'veriyor. Dergi sayfasi esas alindi.'),
    'Avila2024': ('OK', 'Yil, derginin kendi onerdigi kunyeden (sayi 4(2), 2024). '
                        'Crossref cevrimici yayin yili 2025 gosteriyor; fark beklenen.'),
    'Saral2024': ('OK', 'Yil, derginin kendi onerdigi kunyeden (sayi 4(2), 2024). '
                        'Crossref cevrimici yayin yili 2025 gosteriyor; fark beklenen.'),
    'Palavar2025': ('OK', 'Yil, derginin kendi onerdigi kunyeden (sayi 5(2), 2025). '
                          'Crossref cevrimici yayin yili 2026 gosteriyor; fark beklenen.'),
    'Roy2010': ('OK', 'Open Library: Ranjit K. Roy, Society of Manufacturing Engineers, '
                      "2010 teyitli. Teyit edilemeyen '2nd ed.' ibaresi kunyeden "
                      'cikarildi.'),
    'Hou2024': ('OK', '%3.35 ve %0.36 degerleri tam metinden teyit edildi.'),
    'Serani2024': ('OK', 'Ortogonal dizi payi %5, tasarimin %27\'sinde '
                         'belirtilmemis, dogrulama kosulari tablolanmamis - '
                         'derlemenin kendisinden teyit edildi.'),
    'Mahmoodi2023': ('DUZELTILDI', 'Baslangicta "sig su" olarak yazilmisti; kaynak '
                                   'derin suda VLCC. Metin duzeltildi.'),
    'Liu2022': ('EDILEMEDI', "PDF CID kodlu, metin katmani okunamadi. Sayisal deger "
                             'iceren cumle metinden cikarildi, iddia nitel birakildi.'),
    'Wei2024': ('EDILEMEDI', "PDF CID kodlu, metin katmani okunamadi. Sayisal deger "
                             'iceren cumle metinden cikarildi, iddia nitel birakildi.'),
    'Kuo2009': ('EDILEMEDI', 'Ucretli, PDF alinamadi. 3^7=2187 tam sayim ve Taguchi '
                             'optimumunun 366. sirada olmasi iddiasi ikincil '
                             'kaynaklardan; ELLE TEYIT EDILMELI.'),
    'Box1988': ('EDILEMEDI', 'Ucretli. S/N orani elestirisi iddiasi nitel, '
                             'genel kabul goren bir degerlendirme; teyit onerilir.'),
    'Sacks1989': ('EDILEMEDI', 'Project Euclid sayfasi bot erisiminde bos dondu. '
                               'Deterministik bilgisayar deneylerinde saf hata '
                               'teriminin olmadigi iddiasi nitel.'),
}

# Acik erisimli ama otomatik istemciye kapali kaynaklarin dogrudan PDF adresi.
# Tarayicidan tiklayinca iniyor; curl/WebFetch'e sunucu 403 veriyor.
DOGRUDAN_PDF = {
 'Karabulut2026': 'https://commons.yildiz.edu.tr/cgi/viewcontent.cgi?article=1046&context=seatific',
 'Palavar2025':   'https://commons.yildiz.edu.tr/cgi/viewcontent.cgi?article=1045&context=seatific',
 'Pereira2025':   'https://commons.yildiz.edu.tr/cgi/viewcontent.cgi?article=1034&context=seatific',
 'Saral2024':     'https://commons.yildiz.edu.tr/cgi/viewcontent.cgi?article=1029&context=seatific',
 'Avila2024':     'https://commons.yildiz.edu.tr/cgi/viewcontent.cgi?article=1031&context=seatific',
 'Mocellin2024':  'https://commons.yildiz.edu.tr/cgi/viewcontent.cgi?article=1024&context=seatific',
 'Ozselek2024':   'https://commons.yildiz.edu.tr/cgi/viewcontent.cgi?article=1025&context=seatific',
 'Ciplakkaya2023': 'https://commons.yildiz.edu.tr/cgi/viewcontent.cgi?article=1020&context=seatific',
 'Yurtseven2023': 'https://commons.yildiz.edu.tr/cgi/viewcontent.cgi?article=1021&context=seatific',
 'Cakici2021':    'https://commons.yildiz.edu.tr/cgi/viewcontent.cgi?article=1001&context=seatific',
 'Mentese2021':   'https://commons.yildiz.edu.tr/cgi/viewcontent.cgi?article=1002&context=seatific',
 'Seok2019':      'https://www.mdpi.com/2077-1312/7/7/226/pdf',
 'Sacks1989':     'https://projecteuclid.org/journals/statistical-science/volume-4/'
                  'issue-4/Design-and-Analysis-of-Computer-Experiments/'
                  '10.1214/ss/1177012413.pdf',
}

# soyad+yil -> (dosyalar, uyari)
HARITA = {
    'Seok2019': (['seok2019_doe_rsm.pdf'], ''),

    'Karabulut2026': (['seatific_karabulut2026_tugboat.pdf'], ''),
    'Palavar2025':   (['seatific_palavar2025_suboff.pdf'], ''),
    'Pereira2025':   (['seatific_pereira2025_movingmesh.pdf'], ''),
    'Saral2024':     (['seatific_saral2024_bulbousbow.pdf'], ''),
    'Avila2024':     (['seatific_avila2024_overtopping.pdf'], ''),
    'Mocellin2024':  (['seatific_mocellin2024_waves.pdf'], ''),
    'Ozselek2024':   (['seatific_ozselek2024_owc.pdf'], ''),
    'Ciplakkaya2023': (['seatific_ciplakkaya2023_autosub.pdf'], ''),
    'Yurtseven2023': (['seatific_yurtseven2023_ductedcpp.pdf'], ''),
    'Cakici2021':    (['seatific_cakici2021_heave.pdf'], ''),
    'Mentese2021':   (['seatific_mentese2021_cylinders.pdf'], ''),
    'Adizue2025':    (['adizue2025_doe_ml.pdf'], ''),
    'Campbell2022': (['campbell2022.pdf', 'campbell2022_soton.pdf'], ''),
    'Drouet2017':   (['drouet2017_trim_in_waves.pdf'], ''),
    'Guney2026':    (['00_BIZIM_BILDIRI_ICSOS2026.pdf'], 'Kendi konferans bildirimiz.'),
    'Hou2024':      (['hou2024_constrained_sampling.pdf'], ''),
    'Kim2015':      (['kriso2015_snak.pdf'], 'Korece metin, tablolar Ingilizce.'),
    'Korkmaz2023':  (['korkmaz2023.pdf'], ''),
    'Martic2024':   (['applsci6570.pdf'], ''),
    'Miao2020':     (['miao_wan2018_EGO.pdf'],
                     'DIKKAT: kunye 2020 (Int J Comput Methods, doi 10.1142/...), '
                     'elimdeki PDF 2018 OpenFOAM Workshop bildirisi. Ayni ekibin iki '
                     'ayri yayini olabilir. Metindeki "30 RANS + 10 EI" sayisi 2018 '
                     "PDF'inden teyit edildi; kunyenin hangi yayina ait oldugu ELLE "
                     'KONTROL EDILMELI.'),
    'Reichel2014':  (['reichel2014b.pdf'], ''),
    'Serani2024':   (['serani2024_scoping_review.pdf'], ''),
    'Shivachev2017': (['shivachev2017.pdf', 'shivachev_thesis.pdf'],
                      'Tez, ayni calismanin genis hali.'),
    'Vasilev2024':  (['jmse1265.pdf'],
                     'Tablo 8-9 sutun basliklari yayinda hatali etiketli; makalede '
                     'dipnotla belirtildi.'),
    'Yu2021':       (['yu2021_stern_appendage.pdf'], ''),
    'Ziylan2022':   (['ziylan2022b.pdf'], ''),
}

shutil.rmtree(CIK, ignore_errors=True)
os.makedirs(os.path.join(CIK, 'kaynak_pdf'))

# ---- makale metni: paragraflar + tablo satirlari ayri isaretli
PARCA = []   # (bolum, tur, metin)
for f in sorted(glob.glob(os.path.join(MAKALE, '0[0-5]*.md'))):
    s = io.open(f, encoding='utf-8').read()
    bolum = os.path.basename(f).replace('.md', '')
    for kesit in re.split(r'\n(?=#)', s):
        mb = re.match(r'#+\s*([\d.]+)', kesit)
        if mb:
            bolum = mb.group(1)
        mt = re.search(r'\*\*(Table\s+\d+)', kesit)
        tablo_adi = mt.group(1) if mt else 'tablo'
        for p in re.split(r'\n\s*\n', kesit):
            for satir in p.split('\n'):
                if satir.strip().startswith('|'):
                    if not re.match(r'^\s*\|[\s|:-]*\|\s*$', satir):
                        PARCA.append((bolum, tablo_adi, ' '.join(satir.split())))
            duz = ' '.join(l for l in p.split('\n')
                           if not l.strip().startswith('|'))
            duz = ' '.join(duz.split())
            if duz and not duz.startswith('#') and not duz.startswith('**Table') \
                    and not duz.startswith('**Figure'):
                PARCA.append((bolum, 'metin', duz))

kay = io.open(os.path.join(MAKALE, '08_references.md'), encoding='utf-8').read()
bloklar = [b.strip() for b in re.split(r'\n\s*\n', kay.split('# References', 1)[1])
           if b.strip()]

satirlar = []
for i, blok in enumerate(bloklar, 1):
    tek = ' '.join(blok.split())
    m = re.match(r"(?:\u26a0 )?([A-Za-z\u00c0-\u024f'-]+)[^.]*?\.\s*((?:1[89]|20)\d\d)[ab]?\.", tek)
    if not m:
        print('AYRISTIRILAMADI: ' + tek[:60])
        continue
    soyad, yil = m.group(1), m.group(2)
    md = re.search(r'doi:(\S+?)(?:\s|$|\])', tek)
    doi = md.group(1).rstrip('.') if md else ''

    # --- atiflar: soyad ile yil 90 karakter icinde mi
    atiflar = []
    gorulen = set()
    for bolum, tur, p in PARCA:
        for mm in re.finditer(re.escape(soyad), p):
            if yil not in p[mm.start():mm.start() + 90]:
                continue
            if tur == 'metin':
                sinir = [0] + [b.end() for b in SINIR.finditer(p)] + [len(p)]
                bas = max(x for x in sinir if x <= mm.start())
                son = min(x for x in sinir if x > mm.start())
                alinti = p[bas:son].strip()
            else:
                alinti = p
            if alinti not in gorulen:
                gorulen.add(alinti)
                atiflar.append((bolum, tur, alinti))
            break

    anah = re.sub(r'[^A-Za-z]', '', sade(soyad.replace('\u0107', 'c'))) + yil
    dosyalar, uyari = HARITA.get(anah, ([], ''))
    dosyalar = [d for d in dosyalar if os.path.exists(os.path.join(PDFDIZIN, d))]

    kls = '%02d_%s_%s' % (i, re.sub(r"[^A-Za-z]", '', sade(soyad)) or 'kaynak', yil)
    os.makedirs(os.path.join(CIK, kls), exist_ok=True)
    g = ['# %s %s' % (soyad, yil), '', '## Kaynakcadaki kunye', '', '```', tek, '```', '']
    if doi:
        g += ['Dogrulama linki: https://doi.org/' + doi, '']
    g += ['## Kaynak dosyasi', '']
    if dosyalar:
        for d in dosyalar:
            shutil.copy(os.path.join(PDFDIZIN, d), os.path.join(CIK, 'kaynak_pdf', d))
            g.append('- `kaynak_pdf/%s`' % d)
    elif anah in DOGRUDAN_PDF:
        g.append('- **PDF YOK** - acik erisimli, dogrudan indirme adresi:')
        g.append('')
        g.append('  ' + DOGRUDAN_PDF[anah])
        g.append('')
        g.append('  (Sunucu otomatik indiriciyi engelliyor, tarayicidan aciliyor.)')
    else:
        g.append('- **PDF YOK** - yukaridaki DOI linkinden veya universite '
                 'erisiminden indirilmeli')
    if uyari:
        g += ['', '> **' + uyari + '**']
    durum, aciklama = TEYIT.get(anah, ('', ''))
    if durum:
        etiket = {'OK': 'Onceden teyit edildi',
                  'DUZELTILDI': 'Hata bulundu ve duzeltildi',
                  'EDILEMEDI': 'TEYIT EDILEMEDI - elle kontrol gerekli'}[durum]
        g += ['', '## Teyit durumu: %s' % etiket, '', aciklama]
    g += ['', '## Makalede nerede, ne icin kullanilmis', '']
    if atiflar:
        for bolum, tur, c in atiflar:
            yer = 'Bolum %s' % bolum if tur == 'metin' else '%s (Bolum %s)' % (tur, bolum)
            g += ['**%s**' % yer, '', '> ' + c, '']
    else:
        g += ['- **Metinde atif bulunamadi** - kaynakca fazlasi olabilir, kontrol et', '']
    g += ['## Kontrol', '',
          '- [ ] Kunye dogru: yazarlar, yil, dergi, cilt/sayi, sayfa, DOI',
          '- [ ] Yukaridaki cumlenin soyledigi sey kaynakta gercekten var',
          '- [ ] Sayisal deger varsa kaynaktan teyit edildi', '', 'Not: ', '']
    io.open(os.path.join(CIK, kls, 'KONTROL.md'), 'w', encoding='utf-8').write('\n'.join(g))
    satirlar.append((i, soyad, yil, len(atiflar),
                     dosyalar[0] if dosyalar else 'YOK', doi, bool(uyari), kls, durum))

eksik = [s for s in satirlar if s[4] == 'YOK']
atifsiz = [s for s in satirlar if s[3] == 0]
uyarili = [s for s in satirlar if s[6]]

L = ['# Referans kontrol listesi', '',
     'Her kaynak icin ayri klasor. Icinde: kaynakcadaki kunye, DOI linki, varsa',
     "kaynagin PDF'i (`kaynak_pdf/` altinda), ve makalede o kaynaga yapilan",
     'atiflarin tam cumleleri bolum numarasiyla. En altta isaretlenecek kutular.', '',
     '| # | Kaynak | Yil | Atif | PDF | Teyit | Uyari |',
     '|---|---|---|---|---|---|---|']
SIM = {'OK': 'teyitli', 'DUZELTILDI': 'duzeltildi', 'EDILEMEDI': '**ELLE**', '': '-'}
for i, soyad, yil, na, pdf, doi, uy, kls, durum in satirlar:
    L.append('| %d | [%s](%s/KONTROL.md) | %s | %d | %s | %s | %s |'
             % (i, soyad, kls, yil, na, pdf, SIM[durum], 'VAR' if uy else ''))

elle = [s for s in satirlar if s[8] == 'EDILEMEDI']
L += ['', '## Oncelikli kontrol gerekenler', '']
if elle:
    L.append('**Teyit edilemedi, elle kontrol gerekli** (en onemlisi bunlar):')
    for s in elle:
        L.append('- %s %s -> `%s/KONTROL.md`' % (s[1], s[2], s[7]))
    L.append('')
if uyarili:
    L.append('**Kunye/PDF uyusmazligi:**')
    for s in uyarili:
        L.append('- %s %s -> `%s/KONTROL.md`' % (s[1], s[2], s[7]))
    L.append('')
if atifsiz:
    L.append('**Metinde atif bulunamadi** (kaynakca fazlasi olabilir):')
    for s in atifsiz:
        L.append('- %s %s' % (s[1], s[2]))
    L.append('')
if eksik:
    L.append("**PDF'i olmayan, DOI'den teyit edilecek kaynaklar:**")
    for s in eksik:
        L.append('- %s %s%s' % (s[1], s[2],
                                ('  https://doi.org/' + s[5]) if s[5] else '  (DOI yok)'))
    L.append('')

L += ['## Ozet', '', '- Toplam kaynak: %d' % len(satirlar),
      '- PDF eslesen: %d' % (len(satirlar) - len(eksik)),
      '- PDF eksik: %d' % len(eksik),
      '- Metinde atifi bulunamayan: %d' % len(atifsiz), '',
      '## Nasil kullanilir', '',
      '1. Yukaridaki tablodan kaynaga tikla, KONTROL.md acilir.',
      '2. Kunyeyi DOI linkinden veya PDF ilk sayfasindan karsilastir.',
      '3. Makaleden alinan cumleyi oku, kaynakta o bilgi gercekten var mi bak.',
      '4. Kutulari isaretle; aykiri bir sey varsa Not satirina yaz.', '',
      '## Not: elimizde olup kaynakcada olmayan PDF\'ler', '',
      'Bunlar veri cikarmak icin indirildi, makalede atif yapilmadi:', '']
kullanilan = {d for dosyalar, _ in HARITA.values() for d in dosyalar}
for p in sorted(os.path.basename(x) for x in glob.glob(os.path.join(PDFDIZIN, '*.pdf'))):
    if p not in kullanilan:
        L.append('- `%s`' % p)

io.open(os.path.join(CIK, '00_KONTROL_LISTESI.md'), 'w', encoding='utf-8').write('\n'.join(L))

# --- acik erisimli PDF'leri indiren betik. Sunucu otomatik istemciyi 403'luyor,
#     tarayici kimligiyle gelen istek geciyor; kullanici kendi makinesinde calistirir.
ad_map = {}
for i, soyad, yil, na, pdf, doi, uy, kls, durum in satirlar:
    a = re.sub(r'[^A-Za-z]', '', sade(soyad)) + yil
    if a in DOGRUDAN_PDF and pdf == 'YOK':
        ad_map[a] = (kls, DOGRUDAN_PDF[a])

PS = ['# Acik erisimli kaynak PDF\'lerini indirir.',
      '# Calistirmak icin: PowerShell ac, bu klasore gel, .\\indir.ps1 yaz.',
      '',
      '$ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"',
      '$hedef = Join-Path $PSScriptRoot "kaynak_pdf"',
      'if (-not (Test-Path $hedef)) { New-Item -ItemType Directory $hedef | Out-Null }',
      '']
for a, (kls, url) in sorted(ad_map.items()):
    PS += ['Write-Host "indiriliyor: %s"' % a,
           'try {',
           '  Invoke-WebRequest -Uri "%s" -UserAgent $ua '
           '-OutFile (Join-Path $hedef "%s.pdf") -ErrorAction Stop' % (url, a),
           '} catch { Write-Host "  olmadi: $_" }',
           '']
PS += ['Write-Host ""',
       'Write-Host "Biten dosyalar kaynak_pdf klasorunde."']
io.open(os.path.join(CIK, 'indir.ps1'), 'w', encoding='utf-8').write('\n'.join(PS))
print('indirme betigi: %d acik erisimli kaynak' % len(ad_map))
print('klasor: %s' % CIK)
print('kaynak %d | PDF var %d | PDF yok %d | atifsiz %d | uyarili %d'
      % (len(satirlar), len(satirlar) - len(eksik), len(eksik), len(atifsiz), len(uyarili)))
