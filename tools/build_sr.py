"""Stories (1080x1920) e Reels (9:16) no padrão Von Beauty."""
import asyncio, pathlib, subprocess, shutil, sys
from PIL import Image
from playwright.async_api import async_playwright
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import importlib.util
spec = importlib.util.spec_from_file_location("b3", pathlib.Path(__file__).parent / "build3.py")

ROOT = pathlib.Path(__file__).parent
REF = pathlib.Path(__file__).resolve().parent.parent / "brand"
F = ROOT / "node_modules/@fontsource"
OUT = ROOT / "out_sr"
FONTS = "".join(
    f"@font-face{{font-family:{fam};font-weight:{w};font-style:{st};src:url('file://{F}/{pkg}/files/{pkg}-latin-{w}-{st}.woff2')}}"
    for fam, pkg, w, st in [("CG", "cormorant-garamond", 300, "normal"), ("CG", "cormorant-garamond", 400, "normal"),
                            ("CG", "cormorant-garamond", 300, "italic"), ("CG", "cormorant-garamond", 400, "italic"),
                            ("JO", "jost", 400, "normal"), ("JO", "jost", 500, "normal")])
BLACK, GRAF, ROSE, ROSE_ANT, ROSE_LIGHT, OFF = "#0E0D0E", "#2B2A2C", "#E9848D", "#B26A72", "#E6B5BE", "#F5F0EE"
THEME = {
    "dark": dict(bg=BLACK, fg="#FFFFFF", em=ROSE, label=ROSE_LIGHT, body="#E9E2E3", logo="logo_white.png", line=ROSE),
    "graf": dict(bg=GRAF, fg="#FFFFFF", em=ROSE, label=ROSE_LIGHT, body="#E9E2E3", logo="logo_white.png", line=ROSE),
    "light": dict(bg=OFF, fg="#2B2A2C", em=ROSE_ANT, label=ROSE_ANT, body="#4A4446", logo="logo_dark.png", line=ROSE_ANT),
    "blush": dict(bg="#EBD3D6", fg="#2B2A2C", em=ROSE_ANT, label="#8E5560", body="#4A4446", logo="logo_dark.png", line=ROSE_ANT),
}


def css(t, W, H):
    return f"""*{{box-sizing:border-box;margin:0;padding:0}}body{{width:{W}px;height:{H}px;background:transparent}}
.s{{position:relative;width:{W}px;height:{H}px;overflow:hidden;color:{t['fg']};font-family:JO}}
.bg{{position:absolute;inset:0;background-size:cover;background-position:center}}
.dim{{position:absolute;inset:0;background:rgba(14,13,14,.62)}}
.in{{position:relative;height:100%;padding:220px 100px 300px;display:flex;flex-direction:column;justify-content:space-between}}
.logo{{height:96px;align-self:center}}
.mid{{display:flex;flex-direction:column;gap:40px;align-items:center;text-align:center}}
.label{{font-size:30px;letter-spacing:.34em;text-transform:uppercase;color:{t['label']};font-weight:500}}
.h1{{font-family:CG;font-weight:400;font-size:150px;line-height:.98}}
.h2{{font-family:CG;font-weight:400;font-size:118px;line-height:1.02}}
em{{font-style:italic;color:{t['em']}}}
.body{{font-size:40px;line-height:1.45;color:{t['body']};max-width:860px}}
.rule{{width:120px;height:2px;background:{t['line']}}}
.pill{{border:2px solid {t['line']};padding:26px 46px;font-size:30px;letter-spacing:.28em;text-transform:uppercase;font-weight:500}}
.card{{font-family:CG;font-weight:400;font-size:120px;line-height:1.02;text-align:center;color:#fff;text-shadow:0 4px 40px rgba(0,0,0,.55)}}
.card em{{color:{ROSE}}}"""


def page(mid, theme="dark", bg=None, W=1080, H=1920, overlay_only=False):
    t = THEME[theme]
    if overlay_only:
        return f"""<!doctype html><html><head><meta charset="utf-8"><style>{FONTS}{css(t, W, H)}</style></head><body>
<div class="s" style="display:flex;align-items:center;justify-content:center;padding:0 90px">{mid}</div></body></html>"""
    layer = f'<div class="bg" style="background-image:url(file://{bg})"></div><div class="dim"></div>' if bg else ""
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{FONTS}{css(t, W, H)}</style></head><body>
<div class="s" style="background:{t['bg']}">{layer}<div class="in"><img class="logo" src="file://{REF}/{t['logo'] if not bg else 'logo_white.png'}">
<div class="mid">{mid}</div><div></div></div></div></body></html>"""


def vertical_crop(src, x, out):
    im = Image.open(src).convert("RGB")
    h = im.height; w = int(h * 9 / 16)
    im.crop((x, 0, x + w, h)).resize((1080, 1920), Image.LANCZOS).save(out, quality=92)
    return out


async def shoot(pg, html, path, transparent=False):
    f = path.with_suffix(".html"); f.write_text(html, encoding="utf-8")
    await pg.goto(f"file://{f}"); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(200)
    await pg.screenshot(path=str(path), omit_background=transparent); f.unlink()


def make_reel(bg_jpg, overlays, times, out_mp4, dur):
    """bg com zoom lento + overlays PNG com fade."""
    inputs = ["-loop", "1", "-t", str(dur), "-i", str(bg_jpg)]
    for o in overlays:
        inputs += ["-loop", "1", "-t", str(dur), "-i", str(o)]
    fps = 30; frames = dur * fps
    flt = [f"[0:v]scale=1188:2112,zoompan=z='1+0.08*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps={fps},"
           f"eq=brightness=-0.10:saturation=0.95,format=yuv420p[v0]"]
    last = "v0"
    for i, (a, b) in enumerate(times, 1):
        flt.append(f"[{i}:v]format=rgba,fade=t=in:st={a}:d=0.5:alpha=1,fade=t=out:st={b-0.5}:d=0.5:alpha=1[o{i}]")
        flt.append(f"[{last}][o{i}]overlay=0:0:enable='between(t,{a},{b})'[v{i}]")
        last = f"v{i}"
    # trilha ambiente suave sintetizada (acorde baixo + ruído leve) para o Reel não ficar mudo
    audio = ["-f", "lavfi", "-t", str(dur), "-i",
             "sine=f=220:sample_rate=44100,volume=0.025[a1];sine=f=277.18,volume=0.02[a2];sine=f=329.63,volume=0.018[a3];anoisesrc=color=pink:amplitude=0.01[a4];[a1][a2][a3][a4]amix=inputs=4"]
    cmd = ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(flt), "-map", f"[{last}]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(fps), "-t", str(dur), "-an", str(out_mp4)]
    subprocess.run(cmd, check=True)


async def build_26():
    d = OUT / "26nov"; shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    salav = vertical_crop(REF / "renders/s-024.jpg", 1300, d / "_bg_sala.jpg")
    loungev = vertical_crop(REF / "renders/r-014.jpg", 350, d / "_bg_lounge.jpg")
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        # Stories
        await shoot(pg, page('<p class="label">Novo no feed</p><h1 class="h1">Toxina:<br><em>6 coisas antes<br>de fazer.</em></h1><div class="rule"></div><p class="body">Leia, salve e envie para quem está pensando em fazer.</p>', "light"), d / "story1_13h.png")
        await shoot(pg, page('<p class="label">Responda este story</p><h2 class="h2">Você já fez<br><em>toxina<br>botulínica?</em></h2><div class="rule"></div><p class="pill">Responda Sim ou Não</p>', "dark", bg=salav), d / "story2_16h.png")
        await shoot(pg, page('<p class="label">Amanhã · Black Friday Von</p><h2 class="h2">Uma condição<br><em>que não se repete.</em></h2><div class="rule"></div><p class="body">Toxina botulínica com valor especial e apenas 10 vagas. Ative as notificações.</p>', "blush"), d / "story3_20h.png")
        # Reel overlays (transparentes)
        cards = ['<p class="card">Natural<br>ou <em>congelado?</em></p>',
                 '<p class="card">A diferença<br>está na <em>técnica</em></p>',
                 '<p class="card">e na <em>dose certa.</em></p>',
                 f'<div style="display:flex;flex-direction:column;align-items:center;gap:44px"><img src="file://{REF}/logo_white.png" style="height:130px"><p class="card" style="font-size:64px">Avaliação com<br><em>profissional habilitado</em></p></div>']
        ov = []
        for i, c in enumerate(cards):
            path = d / f"_ov{i}.png"; await shoot(pg, page(c, "dark", overlay_only=True), path, transparent=True); ov.append(path)
        # Capa do Reel (feed 4:5 mostra o centro)
        await shoot(pg, page('<p class="label">Toxina botulínica</p><h1 class="h1">Natural<br>ou <em>congelado?</em></h1>', "dark", bg=loungev), d / "reel_capa.png")
        await b.close()
    make_reel(loungev, ov, [(0.2, 3.4), (3.4, 6.6), (6.6, 9.4), (9.4, 13)], d / "reel_19h.mp4", 13)
    for f in d.glob("_*"):
        f.unlink()

asyncio.run(build_26())
print("ok")
