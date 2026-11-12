"""Regenerates favicon + social image into ./public (needs: pip install pillow). Optional."""
from PIL import Image, ImageDraw, ImageFont
import pathlib
OUT = pathlib.Path(__file__).parent / "public"
RED, WHITE, SOFT = (217, 45, 32), (255, 255, 255), (244, 180, 174)

def logo(size):
    s = size * 4  # supersample
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); k = s / 64
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=14 * k, fill=RED)
    d.polygon([(18*k,10*k),(38*k,10*k),(50*k,22*k),(50*k,54*k),(48*k,56*k),(18*k,56*k),(16*k,54*k),(16*k,12*k)], fill=WHITE)
    d.polygon([(38*k,10*k),(50*k,22*k),(40*k,22*k),(38*k,20*k)], fill=SOFT)
    for y, x2 in ((34, 42), (41, 42), (48, 35)):
        d.line([(24*k, y*k), (x2*k, y*k)], fill=RED, width=int(3.5*k))
        for x in (24, x2):
            d.ellipse([x*k-1.75*k, y*k-1.75*k, x*k+1.75*k, y*k+1.75*k], fill=RED)
    return im.resize((size, size), Image.LANCZOS)

svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#d92d20"/>'
       '<path d="M18 10h20l12 12v32a2 2 0 0 1-2 2H18a2 2 0 0 1-2-2V12a2 2 0 0 1 2-2z" fill="#fff"/>'
       '<path d="M38 10l12 12H40a2 2 0 0 1-2-2z" fill="#f4b4ae"/>'
       '<path d="M24 34h18M24 41h18M24 48h11" stroke="#d92d20" stroke-width="3.5" stroke-linecap="round"/></svg>')
(OUT / "favicon.svg").write_text(svg)
big = logo(256); big.save(OUT / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
logo(180).save(OUT / "apple-touch-icon.png"); logo(192).save(OUT / "android-chrome-192x192.png"); logo(512).save(OUT / "android-chrome-512x512.png")

# social share image 1200x630
bg = Image.new("RGB", (1200, 630), (243, 246, 251)); d = ImageDraw.Draw(bg)
d.rectangle([0, 0, 1200, 16], fill=RED)
bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
bg.paste(logo(150), (90, 110), logo(150))
d.text((270, 118), "File1pdfedit", font=ImageFont.truetype(bold, 84), fill=(20, 33, 61))
d.text((90, 320), "Free online PDF tools", font=ImageFont.truetype(bold, 62), fill=(217, 45, 32))
d.text((90, 410), "Compress, merge, split, rotate and convert PDFs.", font=ImageFont.truetype(reg, 36), fill=(86, 98, 122))
d.text((90, 470), "Private - runs in your browser. No upload.", font=ImageFont.truetype(reg, 36), fill=(86, 98, 122))
bg.save(OUT / "og-image.png", optimize=True)
print("icons ok")
