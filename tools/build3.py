import asyncio, pathlib, shutil, sys
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).parent
F = ROOT / "node_modules/@fontsource"
REF = pathlib.Path(__file__).resolve().parent.parent / "brand"
OUT = ROOT / "out3"

FONTS = "".join(
    f"@font-face{{font-family:{fam};font-weight:{w};font-style:{st};src:url('file://{F}/{pkg}/files/{pkg}-latin-{w}-{st}.woff2')}}"
    for fam, pkg, w, st in [
        ("CG", "cormorant-garamond", 300, "normal"), ("CG", "cormorant-garamond", 400, "normal"),
        ("CG", "cormorant-garamond", 300, "italic"), ("CG", "cormorant-garamond", 400, "italic"),
        ("JO", "jost", 400, "normal"), ("JO", "jost", 500, "normal")])

# Paleta Von Beauty (extraída do logo, fachada e referências)
BLACK, GRAF, ROSE, ROSE_ANT, ROSE_LIGHT, OFF = "#0E0D0E", "#2B2A2C", "#E9848D", "#B26A72", "#E6B5BE", "#F5F0EE"

CSS = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1080px;height:1350px;background:{BLACK}}}
.s{{position:relative;width:1080px;height:1350px;overflow:hidden;color:#fff;font-family:JO,sans-serif}}
.bg{{position:absolute;inset:0;background-size:cover;background-position:center}}
.shade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(14,13,14,.55) 0%,rgba(14,13,14,.05) 30%,rgba(14,13,14,.35) 52%,rgba(14,13,14,.96) 78%)}}
.dim{{position:absolute;inset:0;background:rgba(14,13,14,.72)}}
.in{{position:relative;height:100%;padding:90px 96px;display:flex;flex-direction:column;justify-content:space-between}}
.top{{display:flex;justify-content:space-between;align-items:center}}
.logo{{height:84px}}
.n{{font-size:22px;letter-spacing:.24em;color:{ROSE_LIGHT};font-weight:500}}
.mid{{display:flex;flex-direction:column;gap:34px}}
.label{{font-size:24px;letter-spacing:.34em;text-transform:uppercase;color:{ROSE_LIGHT};font-weight:500}}
.h1{{font-family:CG;font-weight:400;font-size:138px;line-height:.98}}
.h2{{font-family:CG;font-weight:400;font-size:112px;line-height:1.02}}
em{{font-style:italic;color:{ROSE}}}
.text{{font-family:CG;font-weight:400;font-size:66px;line-height:1.18}}
.body{{font-family:JO;font-weight:400;font-size:34px;line-height:1.45;color:#E9E2E3;max-width:820px}}
.num{{font-family:CG;font-style:italic;font-weight:300;font-size:220px;line-height:.8;color:{ROSE}}}
.rule{{width:120px;height:2px;background:{ROSE}}}
.bot{{display:flex;justify-content:space-between;align-items:center;font-size:21px;letter-spacing:.3em;text-transform:uppercase;color:#CFC6C8}}
.bot .line{{flex:1;height:1px;background:{ROSE};opacity:.7;margin:0 28px}}
.c{{align-items:center;text-align:center}}
.legal{{font-size:19px;letter-spacing:.1em;text-transform:uppercase;color:#BDB3B5;line-height:1.5}}
"""

LOGO_W = f"file://{REF}/logo_white.png"


def slide(mid, i, n, bg=None, mode="solid", base=BLACK, center=False, foot="Von Beauty · Estética avançada"):
    layer = ""
    if bg:
        layer = f'<div class="bg" style="background-image:url(file://{bg})"></div><div class="{"shade" if mode=="shade" else "dim"}"></div>'
    counter = f"{i:02d} / {n:02d}" if n > 1 else ""
    right = "Deslize" if i < n and n > 1 else ""
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>{FONTS}{CSS}</style></head><body>
<div class="s" style="background:{base}">{layer}<div class="in">
<div class="top"><img class="logo" src="{LOGO_W}"><span class="n">{counter}</span></div>
<div class="mid{' c' if center else ''}" style="{'margin-top:auto;margin-bottom:56px' if mode=='shade' else ''}">{mid}</div>
<div class="bot"><span>{foot}</span><span class="line"></span><span>{right}</span></div>
</div></div></body></html>"""


LOUNGE = REF / "crop_lounge.jpg"
SALA = REF / "crop_sala.jpg"
SALA2 = REF / "crop_sala2.jpg"

POSTS = {
    "26nov_toxina": [
        dict(bg=LOUNGE, mode="shade", mid='<p class="label">Toxina botulínica</p><h1 class="h1">6 coisas<br><em>antes de fazer.</em></h1>'),
        dict(mid='<span class="num">01</span><p class="text">Ela relaxa músculos de expressão e <em>suaviza linhas que aparecem quando você se mexe.</em></p>'),
        dict(base=GRAF, mid='<span class="num">02</span><h2 class="h2">Não é<br><em>preenchimento.</em></h2><p class="body">Não dá volume. Atua no movimento do músculo.</p>'),
        dict(mid='<span class="num">03</span><p class="text">Natural ou “congelado” <em>depende de técnica e dose certas.</em></p>'),
        dict(base=GRAF, mid='<span class="num">04</span><p class="text">O efeito é temporário <em>e a duração varia de pessoa para pessoa.</em></p>'),
        dict(bg=SALA, mode="dim", mid='<span class="num">05</span><h2 class="h2">Exija<br><em>procedência.</em></h2><p class="body">Pergunte o lote e a validade do produto antes da aplicação.</p>'),
        dict(mid='<span class="num">06</span><p class="text">Só com profissional habilitado, <em>após avaliação.</em></p>'),
        dict(bg=LOUNGE, mode="dim", center=True, mid='<div class="rule"></div><h2 class="h1">Salve<br><em>e envie</em></h2><p class="body" style="text-align:center">para quem está pensando em fazer.</p>'),
    ],
}


async def main(names):
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--allow-file-access-from-files"])
        pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        for name in names:
            d = OUT / name
            if d.exists():
                shutil.rmtree(d)
            d.mkdir(parents=True)
            sl = POSTS[name]
            for i, s in enumerate(sl, 1):
                kw = {k: v for k, v in s.items() if k != "mid"}
                f = d / f"_{i}.html"
                f.write_text(slide(s["mid"], i, len(sl), **kw), encoding="utf-8")
                await pg.goto(f"file://{f}")
                await pg.evaluate("document.fonts.ready")
                await pg.wait_for_timeout(200)
                await pg.screenshot(path=str(d / f"{i:02d}.png"))
                f.unlink()
        await b.close()

asyncio.run(main(sys.argv[1:] or list(POSTS)))
print("ok")
