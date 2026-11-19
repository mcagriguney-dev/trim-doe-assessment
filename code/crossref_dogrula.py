# -*- coding: utf-8 -*-
"""Kaynakcadaki her DOI'yi Crossref'ten cekip yazdigimizla karsilastirir.

Hocanin uyarisina (yapay zeka yayin uydurabilir) dogrudan cevap: her kunyenin
gercekten var oldugu ve yazar/yil/cilt/sayi/sayfa bilgilerinin dogrulugu
yayincinin kendi kaydindan teyit edilir. Paywall'a takilmaz, metin degil
ustveri cekilir.

Kullanim: python crossref_dogrula.py   (sonuc Referans_Kontrol klasorune yazilir)
"""
import io, json, os, re, subprocess, sys, time, unicodedata

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
REF = os.path.join(KOK, 'makale', '08_references.md')
CIK = r'C:\Users\mcagr\Desktop\Referans_Kontrol'
ONBELLEK = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.crossref')
os.makedirs(ONBELLEK, exist_ok=True)


def sade(t):
    t = t.replace('\u0131', 'i').replace('\u0130', 'i')
    d = unicodedata.normalize('NFKD', t)
    d = ''.join(c for c in d if not unicodedata.combining(c)).lower()
    return re.sub(r'[^a-z0-9]+', ' ', d).strip()


def crossref(doi):
    yol = os.path.join(ONBELLEK, re.sub(r'[^A-Za-z0-9.]', '_', doi) + '.json')
    if not os.path.exists(yol):
        subprocess.run(['curl', '-s', '-m', '30', '-A', 'citation-check/1.0',
                        'https://api.crossref.org/works/' + doi, '-o', yol],
                       check=False)
        time.sleep(0.3)
    try:
        d = json.load(io.open(yol, encoding='utf-8'))
    except Exception:
        return None
    return d.get('message') if d.get('status') == 'ok' else None


s = io.open(REF, encoding='utf-8').read()
bloklar = [' '.join(b.split()) for b in
           re.split(r'\n\s*\n', s.split('# References', 1)[1]) if b.strip()]

rapor = ['# Crossref capraz kontrolu', '',
         'Kaynakcadaki her DOI yayincinin kendi kaydindan (Crossref API) cekildi ve',
         "makalede yazdigimizla karsilastirildi. Amac: kunyenin gercekten var oldugunu",
         've yazar/yil/cilt/sayi/sayfa bilgilerinin dogrulugunu teyit etmek.', '']
tablo = ['| Kaynak | DOI | Var mi | Yil | Cilt/Sayi | Sayfa | Baslik |',
         '|---|---|---|---|---|---|---|']
sorunlu, doisiz = [], []

for blok in bloklar:
    ilk = blok.split('.')[0][:34]
    md = re.search(r'doi:(\S+?)(?:\s|$|\])', blok)
    if not md:
        doisiz.append(blok)
        continue
    doi = md.group(1).rstrip('.')
    m = crossref(doi)
    if not m:
        tablo.append('| %s | `%s` | **BULUNAMADI** | - | - | - | - |' % (ilk, doi))
        sorunlu.append((blok, doi, ['Crossref kaydi bulunamadi']))
        continue

    notlar = []
    # yil
    bizim_yil = re.search(r'\.\s*((?:1[89]|20)\d\d)[ab]?\.', blok)
    by = bizim_yil.group(1) if bizim_yil else '?'
    cy = ''
    for k in ('published-print', 'published-online', 'issued'):
        if m.get(k, {}).get('date-parts', [[None]])[0][0]:
            cy = str(m[k]['date-parts'][0][0])
            break
    yil_ok = (by == cy)
    if not yil_ok:
        notlar.append('yil: biz %s, Crossref %s' % (by, cy))

    # cilt / sayi
    cv, ci = m.get('volume', ''), m.get('issue', '')
    bizim_cs = re.search(r'\.\s*(\d+)(?:\((\d+[^)]*)\))?:', blok)
    bv = bizim_cs.group(1) if bizim_cs else ''
    bi = (bizim_cs.group(2) if bizim_cs and bizim_cs.group(2) else '')
    cs_ok = (not cv) or (bv == cv)
    if cv and bv and bv != cv:
        notlar.append('cilt: biz %s, Crossref %s' % (bv, cv))
    if ci and bi and bi.split('\u2013')[0] != ci.split('-')[0]:
        notlar.append('sayi: biz %s, Crossref %s' % (bi, ci))

    # sayfa
    cp = m.get('page', '') or m.get('article-number', '')
    # Sayfa yalniz "cilt(sayi):" kalibinin ardinda aranir; yoksa "doi:10" yakalanir.
    bizim_sayfa = (re.search(r'[\dA-Za-z\u2013\-]+', blok[bizim_cs.end():])
                   if bizim_cs else None)
    bp = bizim_sayfa.group(0) if bizim_sayfa else ''
    norm = lambda x: re.sub(r'[^0-9]', '', x.split('\u2013')[0].split('-')[0])
    sayfa_ok = (not cp) or (not bp) or (norm(bp) == norm(cp))
    if cp and bp and not sayfa_ok:
        notlar.append('sayfa: biz %s, Crossref %s' % (bp, cp))

    # baslik
    ct = (m.get('title') or [''])[0]
    baslik_ok = False
    if ct:
        ct_s, blok_s = sade(ct), sade(blok)
        baslik_ok = ct_s[:60] in blok_s
        if not baslik_ok:
            ortak = sum(1 for w in set(ct_s.split()) if w in blok_s.split())
            baslik_ok = ortak >= 0.75 * len(set(ct_s.split()))
        if not baslik_ok:
            notlar.append('baslik farkli -> Crossref: "%s"' % ct)

    # yazarlar
    yz = m.get('author') or []
    eksik = [a.get('family', '') for a in yz[:6]
             if a.get('family') and sade(a['family']) not in sade(blok)]
    if eksik:
        notlar.append('yazar metinde gorunmuyor: ' + ', '.join(eksik))

    isaret = lambda b: 'OK' if b else '**FARKLI**'
    tablo.append('| %s | `%s` | var | %s | %s | %s | %s |'
                 % (ilk, doi, isaret(yil_ok), isaret(cs_ok), isaret(sayfa_ok),
                    isaret(baslik_ok)))
    if notlar:
        sorunlu.append((blok, doi, notlar))

# Bunlar gercek hata degil: dergi sayisinin yili ile Crossref'teki cevrimici
# yayin yili farkli. Derginin kendi onerdigi kunyedeki yil kullanildi.
ACIKLANAN = {
 '10.29187/2792-0771.1031':
   'dergi sayisi 4(2) 2024, Crossref cevrimici yayin 2025',
 '10.29187/2792-0771.1045':
   'dergi sayisi 5(2) 2025, Crossref cevrimici yayin 2026',
 '10.29187/2792-0771.1029':
   'dergi sayisi 4(2) 2024, Crossref cevrimici yayin 2025',
}
bilinen = [t for t in sorunlu if t[1] in ACIKLANAN]
sorunlu = [t for t in sorunlu if t[1] not in ACIKLANAN]

rapor += tablo
rapor += ['', '## Incelenmesi gerekenler', '']
if sorunlu:
    for blok, doi, notlar in sorunlu:
        rapor += ['### ' + blok.split('.')[0][:60], '', '```', blok, '```', '']
        for n in notlar:
            rapor.append('- ' + n)
        rapor += ['', 'https://doi.org/' + doi, '']
else:
    rapor.append('Hicbir uyusmazlik yok.')

if bilinen:
    rapor += ['', '## Bilinen ve aciklanmis farklar (duzeltme gerekmez)', '',
              "Derginin kendi onerdigi kunyedeki yil kullanildi:", '']
    for blok, doi, notlar in bilinen:
        rapor.append('- **%s** - %s' % (blok.split('.')[0][:46], ACIKLANAN[doi]))

if doisiz:
    rapor += ['', '## DOI\'si olmayan kaynaklar (Crossref ile teyit edilemez)', '',
              'Bunlar elle kontrol edilmeli:', '']
    for b in doisiz:
        rapor += ['- ' + b]

rapor += ['', '## Ozet', '',
          '- DOI ile teyit edilen: %d' % (len(bloklar) - len(doisiz)),
          '- Uyusmazlik bulunan: %d' % len(sorunlu),
          '- Bilinen/aciklanmis fark: %d' % len(bilinen),
          "- DOI'siz, elle kontrol gereken: %d" % len(doisiz)]

os.makedirs(CIK, exist_ok=True)
io.open(os.path.join(CIK, '00_CROSSREF_KONTROLU.md'), 'w',
        encoding='utf-8').write('\n'.join(rapor))
print('kaynak %d | DOI ile teyit %d | uyusmazlik %d | DOIsiz %d'
      % (len(bloklar), len(bloklar) - len(doisiz), len(sorunlu), len(doisiz)))
print('rapor: %s' % os.path.join(CIK, '00_CROSSREF_KONTROLU.md'))
