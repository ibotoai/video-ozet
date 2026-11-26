import argparse
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import hazirla
import ocr


def args():
    return argparse.Namespace(fps=1, esik=4, dil='tr', ocr_fps=0)


def test_vision_kutu():
    assert ocr.vision_kutu((0.1, 0.2, 0.3, 0.4), 1000, 500) == [100, 200, 400, 400]


def test_ocr_yok_ve_isaretler(tmp_path, monkeypatch):
    kaynak = tmp_path/'kareler'
    kaynak.mkdir()
    Image.new('RGB', (600, 800), 'black').save(kaynak/'001.png')
    Image.new('RGB', (600, 800), 'gray').save(kaynak/'002.png')
    Image.new('RGB', (600, 800), 'gray').save(kaynak/'003.png')
    monkeypatch.setattr(hazirla, 'ocr', lambda *a: {})
    monkeypatch.setattr(hazirla, 'arka_uc_durumu', lambda *a: (None, None, ocr.UYARI))
    cikti = tmp_path/'cikti'
    cikti.mkdir()
    satirlar, _, kolaj = hazirla.ozet_yaz_kare(kaynak, cikti, args())
    metin = '\n'.join(satirlar)
    assert metin.startswith(ocr.UYARI)
    assert 'siyah' in metin and 'bulanik' in metin
    assert 'birlesince 2 farkli an' in metin
    assert kolaj[0][1][0]*kolaj[0][1][1] <= 3_600_000


def test_tasma_ocr(tmp_path):
    ad, dil, _ = ocr.arka_uc_durumu('tr')
    if not ad:
        pytest.skip('OCR kurulu değil')
    im = Image.new('RGB', (800, 300), 'white')
    d = ImageDraw.Draw(im)
    d.text((1, 80), 'MERHABA DUNYA', font=ImageFont.load_default(size=90), fill='black')
    yol = tmp_path/'tasma.png'
    im.save(yol)
    sonuc = ocr.ocr([yol], 'tr')[str(yol.resolve())]
    assert not sonuc.get('hata'), sonuc.get('hata')
    assert hazirla.isaretler(sonuc), sonuc


def _klasor(kok, ad, boyutlar):
    klasor = kok / ad
    klasor.mkdir()
    for i, (g, y, renk) in enumerate(boyutlar, 1):
        im = Image.new('RGB', (g, y), renk)
        ImageDraw.Draw(im).rectangle([g // 4, y // 4, g // 2, y // 2], fill='white')
        im.save(klasor / f'{i:03d}.png')
    return klasor


def _calistir(*arg):
    import subprocess
    betik = Path(__file__).resolve().parents[1] / 'scripts' / 'hazirla.py'
    return subprocess.run([sys.executable, str(betik), *map(str, arg)], capture_output=True, text=True, encoding='utf-8')


def test_turkce_bosluklu_yol_karisik_boyut_bozuk_dosya(tmp_path):
    klasor = _klasor(tmp_path, 'Çalışma klasörü ğüş', [(640, 360, 'navy'), (360, 640, 'darkred'), (500, 500, 'darkgreen')])
    (klasor / '004.png').write_bytes(b'bozuk dosya')
    (klasor / 'alt.png').mkdir()
    cikti = tmp_path / 'çıktı yolu'
    p = _calistir(klasor, '--cikti', cikti)
    assert p.returncode == 0, p.stderr
    ozet = (cikti / 'ozet.md').read_text(encoding='utf-8')
    assert 'farkli boyutlarda' in ozet
    assert 'atlandi: 004.png' in ozet
    assert '001.png' in ozet and (cikti / 'kolaj_1.jpg').is_file()


def test_mp4_adli_klasor_gorsel_klasoru_sayilir(tmp_path):
    klasor = _klasor(tmp_path, 'tatil.mp4', [(320, 240, 'navy'), (320, 240, 'darkred')])
    p = _calistir(klasor, '--cikti', tmp_path / 'c')
    assert p.returncode == 0, p.stderr
    assert 'kare klasoru' in (tmp_path / 'c' / 'ozet.md').read_text(encoding='utf-8')


@pytest.mark.parametrize('arg', [['--fps', '0'], ['--fps', 'nan'], ['--esik', '300'], ['--ocr-fps', '-1']])
def test_gecersiz_ayar_anlasilir_hata(tmp_path, arg):
    klasor = _klasor(tmp_path, 'k', [(100, 100, 'navy')])
    p = _calistir(klasor, *arg)
    assert p.returncode != 0 and 'Traceback' not in p.stderr, p.stderr


def test_olmayan_ve_desteklenmeyen_dosya(tmp_path):
    p = _calistir(tmp_path / 'yok.mp4')
    assert p.returncode != 0 and 'Bulunamadi' in p.stderr
    metin = tmp_path / 'not.txt'
    metin.write_text('x')
    p = _calistir(metin)
    assert p.returncode != 0 and 'Desteklenmeyen' in p.stderr


def test_ocr_hatasi_yazi_yok_gibi_gorunmez(tmp_path, monkeypatch):
    klasor = _klasor(tmp_path, 'k', [(300, 300, 'navy'), (300, 300, 'darkred')])
    monkeypatch.setattr(hazirla, 'arka_uc_durumu', lambda *a: ('Deneme OCR', 'tr', None))
    monkeypatch.setattr(hazirla, 'ocr', lambda yollar, dil: {str(Path(y).resolve()): {'satirlar': [], 'hata': 'motor coktu'} for y in yollar})
    cikti = tmp_path / 'c'
    cikti.mkdir()
    satirlar, _, _ = hazirla.ozet_yaz_kare(klasor, cikti, args())
    metin = '\n'.join(satirlar)
    assert 'OCR hatasi (motor coktu)' in metin
    assert '(yazi yok)' not in metin


def test_numara_sirasi():
    yollar = [Path('k_1000000.jpg'), Path('k_999999.jpg'), Path('k_000002.jpg')]
    assert [p.name for p in sorted(yollar, key=hazirla.numara)] == ['k_000002.jpg', 'k_999999.jpg', 'k_1000000.jpg']


def test_hepsi_bozuk_klasor(tmp_path):
    klasor = tmp_path / 'k'
    klasor.mkdir()
    (klasor / '001.png').write_bytes(b'bozuk')
    cikti = tmp_path / 'c'
    p = _calistir(klasor, '--cikti', cikti)
    assert p.returncode != 0 and '001.png' in p.stderr and 'Traceback' not in p.stderr
    assert not cikti.exists()
