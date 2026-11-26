import importlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
hatalar = 0

def bildir(durum, mesaj):
    global hatalar
    print(f'{durum}: {mesaj}')
    if durum == 'HATA': hatalar += 1

bildir('TAMAM' if (3, 11) <= sys.version_info[:2] <= (3, 14) else 'HATA', f'Python {sys.version.split()[0]}')
moduller = {}
for ad in ('PIL', 'numpy', 'imageio_ffmpeg'):
    try:
        m = importlib.import_module(ad)
        moduller[ad] = m
        bildir('TAMAM', f'{ad} {m.__version__}')
    except Exception as e:
        bildir('HATA', f'{ad}: {e}')
try:
    ffmpeg = moduller['imageio_ffmpeg'].get_ffmpeg_exe()
    subprocess.run([ffmpeg, '-version'], capture_output=True, check=True)
    bildir('TAMAM', 'ffmpeg çalışıyor')
except Exception as e:
    ffmpeg = None
    bildir('HATA', f'ffmpeg: {e}')
from ocr import arka_uc_durumu
ad, dil, uyari = arka_uc_durumu('tr')
# CI'da OCR'in gercekten calistigini zorunlu kilar
zorunlu = os.environ.get('VIDEO_OZET_OCR_ZORUNLU') == '1'
bildir(('HATA' if zorunlu and not ad else 'UYARI') if uyari else 'TAMAM', f'OCR: {ad or "yok"}, dil: {dil or "yok"}' + (f' ({uyari})' if uyari else ''))
try:
    from PIL import Image, ImageDraw, ImageFont
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        for i, (yazi, renk) in enumerate(zip(('MERHABA DUNYA', 'VIDEO OZET TESTI', 'IKINCI SAHNE', 'SON'), ('#101060', '#a02020', '#40a040', '#e0e0e0'))):
            im = Image.new('RGB', (720, 1280), renk)
            d = ImageDraw.Draw(im)
            d.text((40, 550), yazi, font=ImageFont.load_default(size=65), fill='black' if i == 3 else 'white')
            im.save(t / f'{i:02}.png')
        video = t / 'test.mp4'
        for codec in ('libx264', 'mpeg4'):
            sonuc = subprocess.run([ffmpeg, '-v', 'error', '-y', '-framerate', '0.5', '-i', str(t/'%02d.png'), '-r', '10', '-c:v', codec, '-pix_fmt', 'yuv420p', str(video)], capture_output=True)
            if sonuc.returncode == 0: break
        if sonuc.returncode: raise RuntimeError('Test videosu kodlanamadı')
        cikti = t/'cikti'
        p = subprocess.run([sys.executable, str(Path(__file__).with_name('hazirla.py')), str(video), '--cikti', str(cikti)], capture_output=True, text=True, encoding='utf-8')
        if p.returncode: raise RuntimeError(p.stderr or p.stdout)
        ozet = (cikti/'ozet.md').read_text(encoding='utf-8')
        if not (cikti/'kolaj_1.jpg').is_file(): raise RuntimeError('Kolaj bulunamadı')
        an = re.search(r'birlesince (\d+) farkli an', ozet)
        if not an or not 3 <= int(an[1]) <= 6: raise RuntimeError('Farklı an sayısı 3-6 arasında değil')
        es = re.search(r'okumak ~([\d,]+), bu özet \+ kolajlar ~([\d,]+)', ozet)
        if not es or int(es[2].replace(',', '')) >= int(es[1].replace(',', '')): raise RuntimeError('Token tasarrufu doğrulanamadı')
        if ad and 'MERHABA' not in ozet.upper(): raise RuntimeError('OCR MERHABA yazısını okuyamadı')
        if ad and 'yazi akisi' not in ozet: raise RuntimeError('Yazı akışı bölümü yok')
        bildir('TAMAM', f'Öz test: {es[0]}, {an[1]} farklı an')
except Exception as e:
    bildir('HATA', f'Öz test: {e}')
print('SONUC: HAZIR' if not hatalar else f'SONUC: SORUN VAR ({hatalar} hata)')
sys.exit(bool(hatalar))
