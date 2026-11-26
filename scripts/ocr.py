import csv
import io
import json
import shutil
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path
from PIL import Image

UYARI = 'Bu bilgisayarda OCR bulunamadı; ekrandaki yazılar özete girmedi, kolajdan oku.'


def vision_kutu(kutu, g, y):
    x, alt, genislik, yukseklik = kutu
    return [round(x*g), round((1-alt-yukseklik)*y), round((x+genislik)*g), round((1-alt)*y)]


@lru_cache(maxsize=None)
def arka_uc_durumu(dil):
    if sys.platform == 'win32':
        try:
            komut = "[void][Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime]; [Windows.Media.Ocr.OcrEngine]::AvailableRecognizerLanguages | ForEach-Object { $_.LanguageTag }"
            diller = subprocess.run(['powershell.exe', '-NoProfile', '-Command', komut], capture_output=True, text=True, check=True).stdout.splitlines()
            sec = next((x for x in diller if x.lower() == dil.lower()), None) or next((x for x in diller if x.lower().split('-')[0] == dil.lower().split('-')[0]), None)
            sec = sec or next((x for x in diller if x.lower() == 'en-us'), None) or next(iter(diller), None)
            return ('Windows OCR', sec, None if sec and sec.lower().split('-')[0] == dil.lower().split('-')[0] else (f'OCR dili {dil} bulunamadı; {sec} kullanılıyor.' if sec else UYARI)) if sec else (None, None, UYARI)
        except (OSError, subprocess.SubprocessError):
            return None, None, UYARI
    if sys.platform == 'darwin':
        try:
            import Vision
            import ocrmac
            req = Vision.VNRecognizeTextRequest.alloc().init()
            diller, hata = req.supportedRecognitionLanguagesAndReturnError_(None)
            if hata or not diller:
                return None, None, UYARI
            hedef = 'tr-TR' if dil.lower().startswith('tr') else dil
            sec = next((str(x) for x in diller if str(x).lower() == hedef.lower()), None)
            sec = sec or next((str(x) for x in diller if str(x).lower() == 'en-us'), None) or str(diller[0])
            return 'Apple Vision', sec, None if sec.lower() == hedef.lower() else f'OCR dili {hedef} bulunamadı; {sec} kullanılıyor.'
        except Exception:
            return None, None, UYARI
    exe = shutil.which('tesseract')
    if exe:
        try:
            diller = [x.strip() for x in subprocess.run([exe, '--list-langs'], capture_output=True, text=True, check=True).stdout.splitlines()[1:] if x.strip() and x.strip() != 'osd']
            istenen = ['tur', 'eng'] if dil.lower().startswith('tr') else [dil, 'eng']
            sec = '+'.join(x for x in istenen if x in diller)
            if not sec and diller:
                sec = diller[0]
            if sec:
                return 'Tesseract', sec, None if istenen[0] in sec.split('+') else f'OCR dili {istenen[0]} bulunamadı; {sec} kullanılıyor.'
        except (OSError, subprocess.SubprocessError):
            pass
    return None, None, UYARI


def ocr(yollar, dil):
    ad, dil, _ = arka_uc_durumu(dil)
    if not ad or not yollar:
        return {}
    if ad == 'Windows OCR':
        with tempfile.TemporaryDirectory() as t:
            liste, cikti = Path(t)/'liste.txt', Path(t)/'ocr.jsonl'
            liste.write_text('\n'.join(str(Path(y).resolve()) for y in yollar), encoding='utf-8')
            try:
                subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(Path(__file__).with_name('win_ocr.ps1')), '-Liste', str(liste), '-Cikti', str(cikti), '-Dil', dil], check=True, capture_output=True)
                return {str(Path(d['yol']).resolve()): d for d in (json.loads(s) for s in cikti.read_text(encoding='utf-8-sig').splitlines())}
            except (OSError, subprocess.SubprocessError, ValueError) as e:
                hata = getattr(e, 'stderr', b'') or b''
                hata = (hata.decode('utf-8', 'replace') if isinstance(hata, bytes) else str(hata)).strip()[-300:] or str(e)
                return {str(Path(y).resolve()): {'satirlar': [], 'hata': hata} for y in yollar}
    sonuc = {}
    for yol in yollar:
        yol = str(Path(yol).resolve())
        with Image.open(yol) as im:
            g, y = im.size
        kayit = {'g': g, 'y': y, 'satirlar': []}
        try:
            if ad == 'Apple Vision':
                from ocrmac import ocrmac
                for metin, guven, kutu in ocrmac.OCR(yol, language_preference=[dil]).recognize():
                    kayit['satirlar'].append({'metin': metin, 'kutu': vision_kutu(kutu, g, y)})
            else:
                p = subprocess.run(['tesseract', yol, '-', '-l', dil, 'tsv'], capture_output=True, text=True, encoding='utf-8', check=True)
                gruplar = {}
                for satir in csv.DictReader(io.StringIO(p.stdout), delimiter='\t'):
                    metin = satir['text'].strip()
                    if not metin: continue
                    anahtar = tuple(satir[x] for x in ('page_num', 'block_num', 'par_num', 'line_num'))
                    x, yy, w, h = (int(satir[k]) for k in ('left', 'top', 'width', 'height'))
                    gruplar.setdefault(anahtar, []).append((metin, x, yy, x+w, yy+h))
                for kelimeler in gruplar.values():
                    kayit['satirlar'].append({'metin': ' '.join(k[0] for k in kelimeler), 'kutu': [min(k[1] for k in kelimeler), min(k[2] for k in kelimeler), max(k[3] for k in kelimeler), max(k[4] for k in kelimeler)]})
        except Exception as e:
            kayit['hata'] = str(e)
        sonuc[yol] = kayit
    return sonuc
