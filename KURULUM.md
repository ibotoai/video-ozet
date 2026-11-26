# video-ozet kurulumu (yapay zeka ajanı için talimat)

Bu dosyayı okuyan sen, kullanıcının yapay zeka ajanısın. Kullanıcı büyük olasılıkla kod bilmiyor. Adımları sırayla uygula, her adımın sonucunu kontrol et, kullanıcıya sade Türkçeyle (ya da kullanıcının dilinde) ne yaptığını söyle.

## Kurallar

- Yönetici izni (`sudo`, "Yönetici olarak çalıştır") gerektiren bir şeyi kullanıcıya sormadan yapma.
- İnternetten betik indirip doğrudan çalıştırma (`curl ... | sh`, `iwr ... | iex` gibi). Yalnız bu dosyada yazan resmi kaynakları kullan.
- Bilgisayar açılınca kendiliğinden çalışan hiçbir şey kurma.
- Paketleri yalnız aracın kendi klasöründeki sanal ortama (`.venv`) kur; sistem Python'una kurma.
- Bir adım başarısız olursa tahmin yürütüp başka yollar deneme; hatayı kullanıcıya göster ve bu dosyadaki "Sorun çözme" bölümüne bak.

## 0. Çalışabilir misin?

Bu kurulum için senin kullanıcının bilgisayarında komut çalıştırabilmen gerekir (Claude Code, Codex, Gemini CLI, Cursor, GitHub Copilot, Antigravity gibi). Komut çalıştıramıyorsan (ör. tarayıcıdaki sohbet penceresi, Claude Cowork), dur ve kullanıcıya şunu söyle: "Bu araç senin bilgisayarında çalışır; bilgisayarında komut çalıştırabilen bir yapay zeka aracında (Claude Code, Codex ...) bu istemi tekrar ver."

## 1. Kurulum klasörünü seç

Hangi araçta çalışıyorsan, skill o aracın kendi skill klasörüne kurulur (`~` kullanıcının ana klasörü; Windows'ta `C:\Users\<kullanıcı>`):

| Sen hangi araçsın | Kurulum klasörü |
|---|---|
| Claude Code (terminal ya da Claude masaüstü uygulamasının Code sekmesi) | `~/.claude/skills/video-ozet` |
| OpenAI Codex, Gemini CLI, Cursor | `~/.agents/skills/video-ozet` |
| GitHub Copilot (VS Code, Copilot CLI) | `~/.copilot/skills/video-ozet` |
| Google Antigravity | `~/.gemini/config/skills/video-ozet` |

Listede olmayan bir araçsan kullanıcıya hangi klasörü kullanacağını sor. Bu klasöre aşağıda `SKILL_DIR` denir.

`SKILL_DIR` zaten varsa üzerine yazma: kurulum yapılmış demektir, "Güncelleme" bölümüne geç.

## 2. Kodu indir

Sürüm: `v1.0.0`. Kaynak yalnız `https://github.com/ibotoai/video-ozet`.

`git` varsa:

```
git clone --depth 1 --branch v1.0.0 https://github.com/ibotoai/video-ozet.git "SKILL_DIR"
```

`git` yoksa, şu arşivi indir ve aç; içinden çıkan `video-ozet-1.0.0` klasörünün içeriğini `SKILL_DIR`'e taşı:

```
https://github.com/ibotoai/video-ozet/archive/refs/tags/v1.0.0.zip
```

Kontrol: `SKILL_DIR/SKILL.md` ve `SKILL_DIR/scripts/hazirla.py` var olmalı.

## 3. Python 3.11 - 3.14

Uygun bir Python ara, bulduğun ilk uygun komutta dur:

- Windows: `py -3.13`, `py -3.12`, `py -3.14`, `py -3.11`, sonra `python` (her birini `--version` ile dene).
- macOS ve Linux: `python3.13`, `python3.12`, `python3.14`, `python3.11`, sonra `python3`.

Sürüm 3.11, 3.12, 3.13 ya da 3.14 olmalı. Bulduğun komuta aşağıda `PY` denir.

Uygun Python yoksa:

- **Windows:** kullanıcıya sor, onay verirse: `winget install -e --id Python.Python.3.13 --scope user` (yönetici izni istemez). Sonra yeni bir terminalde `py -3.13 --version` ile kontrol et.
- **macOS:** kullanıcıdan Python 3.13'ü resmi siteden kurmasını iste: `https://www.python.org/downloads/macos/` sayfasındaki "Stable Releases" listesinde en üstteki **Python 3.13.x** satırının "macOS 64-bit universal2 installer" bağlantısı (3.14 ya da 3.15 değil, 3.13). Kurulum bilgisayar şifresini kullanıcının kendisi girmesini ister. Kurulunca `python3.13 --version` ile kontrol et. macOS'un kendi `python3`'ü genelde 3.9'dur, yetmez.
- **Linux:** kullanıcıya sor, onay verirse paket yöneticisiyle kur (ör. `sudo apt install python3 python3-venv`). Bu adım şifre ister.

## 4. Sanal ortam ve paketler

`SKILL_DIR` içinde:

```
PY -m venv .venv
```

Sonra (Windows'ta `.venv\Scripts\python.exe`, macOS/Linux'ta `.venv/bin/python`; aşağıda `VPY`):

```
VPY -m pip install -r requirements.txt
```

Paketlerin hepsi PyPI'den, sürümleri `requirements.txt` içinde sabittir (pip'i ya da başka paketi ayrıca güncelleme). ffmpeg ayrıca kurulmaz; `imageio-ffmpeg` paketiyle gelir.

## 5. Kontrol testi

```
VPY scripts/kontrol.py
```

Her satır `TAMAM`, `UYARI` ya da `HATA` ile başlar; son satır `SONUC: HAZIR` ya da `SONUC: SORUN VAR` der. Çıktıyı kullanıcıya kısaca aktar.

- `SONUC: HAZIR` ise kurulum bitti.
- OCR satırı `UYARI` ise araç çalışır ama ekrandaki yazıları okuyamaz ya da Türkçe karakterleri kaçırabilir; "Sorun çözme" bölümündeki OCR maddesini kullanıcıya anlat. Bu kurulumu durdurmaz.
- `HATA` varsa "Sorun çözme" bölümüne bak; çözemezsen hatayı olduğu gibi kullanıcıya göster.

## 6. Kullanıcıya söyle

Kurulum bittiğinde kullanıcıya şunları söyle:

- Kurulum klasörü (`SKILL_DIR`).
- Nasıl kullanılır: "Bir videoya bakmamı istediğinde bu aracı kendiliğimden kullanacağım. İstersen 'video-ozet ile şu videoya bak' de."
- Sınır: araç sesi dinlemez, yalnız görüntüye ve ekrandaki yazıya bakar.
- Bazı araçlar yeni skill'i görmek için yeniden başlatılmak ister (Claude Code'da `/reload-skills`, Gemini CLI'da `/skills reload`, diğerlerinde yeni oturum).

## Güncelleme

Kullanıcı güncelleme isterse:

1. Son sürümü öğren: `https://github.com/ibotoai/video-ozet/releases/latest` sayfasındaki sürüm adı (ör. `v1.1.0`); aşağıda `<sürüm>`. Kurulu sürümle aynıysa güncelleme gerekmez, kullanıcıya söyle.
2. Önce yeni sürümün kurulum dosyasını oku: `https://github.com/ibotoai/video-ozet/blob/<sürüm>/KURULUM.md`. Orada farklı bir adım (ör. yeni Python aralığı) varsa onu uygula.
3. Eski kurulumun adını değiştir: `SKILL_DIR` klasörünü aynı yerde `video-ozet-eski` yap (bu ad doluysa sonuna tarih ekle, ör. `video-ozet-eski-2027-01-15`).
4. Adım 2-5'i yeni sürümle uygula: git komutunda `v1.0.0` yerine `<sürüm>`; arşiv yolunda `https://github.com/ibotoai/video-ozet/archive/refs/tags/<sürüm>.zip`, içinden çıkan klasör `video-ozet-<sürüm başındaki v olmadan>`.
5. Kontrol testi `SONUC: HAZIR` derse eski klasörü kullanıcıya sorarak sil.
6. Adım 4-5'te herhangi bir şey başarısız olursa (indirme, sanal ortam, paket kurulumu ya da test): yarım kalan yeni klasörü sil, `video-ozet-eski` klasörünün adını geri `video-ozet` yap ve hatayı kullanıcıya göster. Eski sürüm çalışmaya devam eder.

## Kaldırma

`SKILL_DIR` klasörünü silmek yeterli. Araç başka bir yere dosya yazmaz (yalnız kullanıldığı klasörde `video-ozet-cikti/` açar).

## Sorun çözme

- **`py`, `python` ya da `python3` bulunamıyor:** adım 3.
- **Windows'ta `winget` yok:** kullanıcıdan Python 3.13'ü `https://www.python.org/downloads/windows/` adresinden kurmasını iste; kurulumda "Add python.exe to PATH" kutusunu işaretlesin.
- **pip paket bulamıyor ("No matching distribution"):** Python sürümü 3.11-3.14 dışında ya da işlemci mimarisi desteklenmiyor. `PY --version` çıktısını kullanıcıya göster.
- **OCR uyarısı (Windows):** Windows'ta Türkçe OCR dili yüklü değilse araç İngilizce OCR'a düşer. Kullanıcı isterse: Ayarlar > Saat ve dil > Dil ve bölge > Türkçe'yi ekle (dil paketiyle birlikte OCR da gelir). Zorunlu değil.
- **OCR uyarısı (Linux):** OCR için `tesseract` gerekir; kullanıcı isterse `sudo apt install tesseract-ocr tesseract-ocr-tur`. Zorunlu değil.
- **OCR uyarısı (macOS):** macOS'un yerleşik metin tanıma özelliği kullanılır; macOS 13 ve sonrası gerekir.
