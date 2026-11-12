#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File1pdfedit static site generator.

Usage:   python build.py
Custom domain later?   SITE_URL=https://example.com python build.py
Output goes to ./public  (this is the folder Cloudflare Pages publishes).
"""
import os, json, shutil, hashlib, pathlib, html as _html
from content import TOOLS, COMMON_FAQ, FREE_FAQ, HOME_STEPS, HOME_GUIDE, HOME_FAQ

# =====================  EDIT THESE SETTINGS  =====================
SITE_NAME = "File1pdfedit"
SITE_URL = os.environ.get("SITE_URL", "https://file1pdfedit.pages.dev").rstrip("/")
CONTACT_EMAIL = "your-email@example.com"        # <-- put your real email (shown on Contact page)
LAST_UPDATED = "2026-11-12"                      # used in sitemap lastmod and legal pages

ADSENSE_CLIENT = ""      # e.g. "ca-pub-1234567890123456"  (leave empty until AdSense approves you)
ADSENSE_SLOT = ""        # optional: ad unit id for the manual banner slots, e.g. "1234567890"
ADSTERRA_BANNER_HTML = ""   # paste an Adsterra banner (iframe/script) snippet here
ADSTERRA_EXTRA_HTML = ""    # optional extra Adsterra code placed before </body> (e.g. Social Bar)

GOOGLE_VERIFICATION = ""   # content value of <meta name="google-site-verification"> (optional)
BING_VERIFICATION = ""     # content value of <meta name="msvalidate.01"> (optional)
CF_BEACON_TOKEN = ""       # Cloudflare Web Analytics token (optional, free)
INDEXNOW_KEY = "f1c0a7d94b2e4f6a8c3d5e7b9a1c2d4e"   # any 8-128 hex chars; file /<key>.txt is generated
# =================================================================

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "public"
SRC = ROOT / "src"
CATS = {"org": "Organize", "cnv": "Convert", "opt": "Optimize", "ins": "Inspect", "edt": "Edit"}

LOGO = ('<svg viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="14" fill="#d92d20"/>'
        '<path d="M18 10h20l12 12v32a2 2 0 0 1-2 2H18a2 2 0 0 1-2-2V12a2 2 0 0 1 2-2z" fill="#fff"/>'
        '<path d="M38 10l12 12H40a2 2 0 0 1-2-2z" fill="#f4b4ae"/>'
        '<path d="M24 34h18M24 41h18M24 48h11" stroke="#d92d20" stroke-width="3.5" stroke-linecap="round"/></svg>')

esc = lambda s: _html.escape(str(s), quote=True)

def asset_ver(name):
    return hashlib.md5((SRC / name).read_bytes()).hexdigest()[:8]
CSS_V, JS_V = asset_ver("style.css"), asset_ver("app.js")

def url(path):
    return SITE_URL + path

def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"

def ad():
    if ADSENSE_CLIENT and ADSENSE_SLOT:
        return ('<div class="ad"><ins class="adsbygoogle" style="display:block" data-ad-client="%s" data-ad-slot="%s" '
                'data-ad-format="auto" data-full-width-responsive="true"></ins>'
                '<script>(adsbygoogle=window.adsbygoogle||[]).push({});</script></div>') % (ADSENSE_CLIENT, ADSENSE_SLOT)
    if ADSTERRA_BANNER_HTML:
        return '<div class="ad">%s</div>' % ADSTERRA_BANNER_HTML
    return ""

def head(path, title, desc, schemas=(), noindex=False):
    canon = url(path)
    robots = "noindex,follow" if noindex else "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"
    h = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         "<title>%s</title>" % esc(title),
         '<meta name="description" content="%s">' % esc(desc),
         '<meta name="robots" content="%s">' % robots]
    if not noindex:
        h.append('<link rel="canonical" href="%s">' % canon)
    h += ['<meta name="theme-color" content="#d92d20">',
          '<link rel="icon" href="/favicon.ico" sizes="32x32">',
          '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
          '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
          '<link rel="manifest" href="/site.webmanifest">',
          '<meta property="og:site_name" content="%s">' % SITE_NAME,
          '<meta property="og:type" content="website">',
          '<meta property="og:title" content="%s">' % esc(title),
          '<meta property="og:description" content="%s">' % esc(desc),
          '<meta property="og:url" content="%s">' % canon,
          '<meta property="og:image" content="%s/og-image.png">' % SITE_URL,
          '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">',
          '<meta name="twitter:card" content="summary_large_image">',
          '<meta name="twitter:title" content="%s">' % esc(title),
          '<meta name="twitter:description" content="%s">' % esc(desc),
          '<meta name="twitter:image" content="%s/og-image.png">' % SITE_URL]
    if GOOGLE_VERIFICATION:
        h.append('<meta name="google-site-verification" content="%s">' % esc(GOOGLE_VERIFICATION))
    if BING_VERIFICATION:
        h.append('<meta name="msvalidate.01" content="%s">' % esc(BING_VERIFICATION))
    h.append('<link rel="stylesheet" href="/assets/style.css?v=%s">' % CSS_V)
    h += [ld(s) for s in schemas]
    if ADSENSE_CLIENT:
        h.append('<script async src="https://pagead2.googleapis.com/pagead/js/adsbygoogle.js?client=%s" crossorigin="anonymous"></script>' % ADSENSE_CLIENT)
    h.append("</head>")
    return "".join(h)

def header(cur):
    def a(href, label, cls=""):
        c = ' aria-current="page"' if href == cur else ""
        k = ' class="%s"' % cls if cls else ""
        return '<a href="%s"%s%s>%s</a>' % (href, k, c, label)
    nav = "".join([a("/compress-pdf/", "Compress PDF"), a("/merge-pdf/", "Merge PDF"), a("/split-pdf/", "Split PDF"),
                   a("/image-to-pdf/", "Image to PDF"), a("/about/", "About"), a("/#tools", "All tools", "cta")])
    return ('<a class="skip" href="#main">Skip to content</a><header class="site-header"><div class="wrap bar">'
            '<a class="brand" href="/" aria-label="%s home">%s<span>File1<b>pdf</b>edit</span></a>'
            '<button id="navToggle" type="button" aria-expanded="false" aria-controls="nav">Menu</button>'
            '<nav id="nav" aria-label="Main">%s</nav></div></header>') % (SITE_NAME, LOGO, nav)

def footer():
    tl = "".join('<li><a href="/%s/">%s</a></li>' % (t["slug"], esc(t["name"])) for t in TOOLS)
    extra = ADSTERRA_EXTRA_HTML or ""
    return ('<footer class="site-footer"><div class="wrap"><div class="fcols">'
            '<div><h2>%s</h2><p>Free online PDF tools that run in your browser. Your files are never uploaded.</p></div>'
            '<div><h2>PDF tools</h2><ul class="two">%s</ul></div>'
            '<div><h2>Company</h2><ul><li><a href="/about/">About</a></li><li><a href="/contact/">Contact</a></li>'
            '<li><a href="/privacy-policy/">Privacy Policy</a></li><li><a href="/terms-of-use/">Terms of Use</a></li>'
            '<li><a href="/sitemap.xml">Sitemap</a></li></ul></div></div>'
            '<p class="copy">&copy; 2026 %s. All rights reserved.</p></div></footer>'
            '<script src="/assets/app.js?v=%s" defer></script>%s%s</body></html>') % (
            SITE_NAME, tl, SITE_NAME, JS_V, beacon(), extra)

def beacon():
    if not CF_BEACON_TOKEN:
        return ""
    return '<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon=\'{"token": "%s"}\'></script>' % CF_BEACON_TOKEN

def faq_html(faqs):
    items = "".join("<details><summary>%s</summary><p>%s</p></details>" % (esc(q), esc(a)) for q, a in faqs)
    return '<div class="faq">%s</div>' % items

def faq_schema(faqs):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}

def crumbs_schema(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": url(p)} for i, (n, p) in enumerate(items)]}

def steps_html(steps):
    return '<ol class="steps">%s</ol>' % "".join("<li><strong>%s</strong><span>%s</span></li>" % (esc(a), esc(b)) for a, b in steps)

def write(rel, text):
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

# ---------------------------------------------------------------- home
def build_home():
    title = "Free Online PDF Tools – Compress, Merge, Split | File1pdfedit"
    desc = ("Free online PDF tools: compress, merge, split, rotate, convert images to PDF and more. "
            "Fast, private and done in your browser – no upload, no sign-up.")
    tiles = "".join(
        '<li><a class="tile k-%s" href="/%s/"><span class="ico" aria-hidden="true">%s</span><strong>%s</strong><span class="d">%s</span></a></li>'
        % (t["cat"], t["slug"], t["icon"], esc(t["name"]), esc(t["card"])) for t in TOOLS)
    guide = "".join("<h3>%s</h3><p>%s</p>" % (esc(h), esc(p)) for h, p in HOME_GUIDE)
    schemas = [
        {"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": url("/"),
         "description": desc, "inLanguage": "en"},
        {"@context": "https://schema.org", "@type": "Organization", "name": SITE_NAME, "url": url("/"),
         "logo": url("/android-chrome-512x512.png")},
        {"@context": "https://schema.org", "@type": "ItemList", "name": "PDF tools",
         "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": t["name"], "url": url("/%s/" % t["slug"])} for i, t in enumerate(TOOLS)]},
        faq_schema(HOME_FAQ)]
    main_html = (
            '<main id="main"><div class="wrap">'
            '<div class="intro"><h1>Free online PDF tools</h1><p class="lead">Pick a tool, drop your file, download the result. Private and free, right in your browser.</p></div>'
            '<ul class="grid" id="tools">%s</ul>%s'
            '<section class="block" id="how-to"><h2>How to use the website tools</h2><p class="lead">Work with PDFs in 3 steps</p>%s</section>'
            '<section class="block guide" id="guide"><h2>Guide</h2>%s</section>'
            '<section class="block" id="faq"><h2>FAQ</h2>%s</section>'
            "</div></main>") % (tiles, ad(), steps_html(HOME_STEPS), guide, faq_html(HOME_FAQ))
    write("index.html", head("/", title, desc, schemas) + "<body>" + header("/") + main_html + footer())

# ---------------------------------------------------------------- tool pages
def build_tool(t):
    path = "/%s/" % t["slug"]
    faqs = list(t["faqs"]) + [COMMON_FAQ, FREE_FAQ]
    multi = t["key"] in ("img2pdf", "merge", "counter", "info")
    accept = (".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" if t["key"] == "img2pdf" else ".pdf,application/pdf")
    others = [o for o in TOOLS if o["slug"] != t["slug"]]
    related = "".join('<li><a href="/%s/">%s</a></li>' % (o["slug"], esc(o["name"])) for o in others)
    schemas = [
        {"@context": "https://schema.org", "@type": "WebApplication", "name": t["name"] + " – " + SITE_NAME, "url": url(path),
         "description": t["desc"], "applicationCategory": "UtilitiesApplication", "operatingSystem": "Any",
         "browserRequirements": "Requires JavaScript", "isAccessibleForFree": True,
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}},
        crumbs_schema([("Home", "/"), (t["name"], path)]),
        faq_schema(faqs)]
    guide = "".join("<p>%s</p>" % esc(p) for p in t["guide"])
    main_html = (
        '<main id="main"><div class="wrap">'
        '<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / %s</nav>'
        '<div class="tool-head"><h1>%s</h1><p class="lead">%s</p></div>'
        '<div class="workspace k-%s" id="workspace" data-tool="%s">'
        '<div class="dropzone" id="dropzone" role="button" tabindex="0" aria-label="%s">'
        '<span class="big" aria-hidden="true">%s</span><strong>%s</strong>'
        '<span class="btn" aria-hidden="true">Choose file%s</span><small>or drag and drop. %s</small>'
        '<input type="file" id="fileInput" accept="%s"%s hidden></div>'
        '<div id="panel"><ul class="files" id="fileList"></ul><div class="opts" id="opts"></div>'
        '<div class="actions"><button class="btn" id="runBtn" type="button">Run</button>'
        '<button class="btn ghost" id="clearBtn" type="button">Start over</button></div></div>'
        '<div class="progress" id="progress" aria-hidden="true"><i></i></div>'
        '<div id="status" role="status" aria-live="polite"></div><div id="result" aria-live="polite"></div>'
        '<p class="privacy-note">Private: your files are processed on your device and never uploaded.</p>'
        '<noscript><p class="err">Please turn on JavaScript to use this tool.</p></noscript></div>%s'
        '<section class="block" id="how-to"><h2>How to use %s</h2>%s</section>'
        '<section class="block guide" id="guide"><h2>%s guide and tips</h2>%s</section>'
        '<section class="block" id="faq"><h2>%s FAQ</h2>%s</section>'
        '<section class="block"><h2>More PDF tools</h2><ul class="related">%s</ul></section>'
        "</div></main>") % (
        esc(t["name"]), esc(t["h1"]), esc(t["lead"]), t["cat"], t["key"], esc(t["drop"]), t["icon"], esc(t["drop"]),
        "s" if multi else "", esc(t["hint"]), accept, " multiple" if multi else "",
        ad(), esc(t["name"]), steps_html(t["steps"]), esc(t["name"]), guide, esc(t["name"]), faq_html(faqs), related)
    write("%s/index.html" % t["slug"], head(path, t["title"], t["desc"], schemas) + "<body>" + header(path) + main_html + footer())

# ---------------------------------------------------------------- info pages
def info_page(path, title, desc, h1, inner, extra_schema=()):
    schemas = [crumbs_schema([("Home", "/"), (h1, path)])] + list(extra_schema)
    main_html = (
            '<main id="main"><div class="wrap prose">'
            '<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / %s</nav><h1>%s</h1>%s</div></main>') % (esc(h1), esc(h1), inner)
    write(path.strip("/") + "/index.html", head(path, title, desc, schemas) + "<body>" + header(path) + main_html + footer())

def build_info_pages():
    tool_list = "".join('<li><a href="/%s/">%s</a> - %s</li>' % (t["slug"], esc(t["name"]), esc(t["card"])) for t in TOOLS)
    info_page("/about/", "About File1pdfedit – Free Private PDF Tools",
        "Learn about File1pdfedit, a free set of PDF tools that run in your browser so your files stay private.", "About File1pdfedit",
        "<p class=\"lead\">File1pdfedit is a collection of free online PDF tools that work entirely in your web browser.</p>"
        "<h2>Why we built it</h2><p>Many PDF websites ask you to upload private documents to a server, create an account or pay to remove a watermark. "
        "We wanted a simple alternative: open the page, drop a file, get the result.</p>"
        "<h2>How it works</h2><p>When you use a tool, your browser reads the file and does the work locally with open-source JavaScript libraries. "
        "Your document is never sent to our servers, which makes the tools fast and keeps sensitive files private.</p>"
        "<h2>What you can do</h2><ul>%s</ul>"
        "<h2>How the site is funded</h2><p>File1pdfedit is free to use. We display advertising to cover the time it takes to build and maintain the tools. "
        "See our <a href=\"/privacy-policy/\">Privacy Policy</a> for details.</p>"
        "<h2>Get in touch</h2><p>Found a problem or have an idea for a new tool? Visit our <a href=\"/contact/\">contact page</a>.</p>" % tool_list)

    info_page("/contact/", "Contact File1pdfedit – Support and Feedback",
        "Contact File1pdfedit with questions, bug reports, feature ideas or business enquiries.", "Contact us",
        "<p class=\"lead\">We read every message. Tell us what is working, what is broken, or which tool you would like to see next.</p>"
        "<h2>Email</h2><p><a href=\"mailto:%s\">%s</a></p>"
        "<h2>What to include</h2><ul><li>The tool you were using</li><li>Your browser and device (for example Chrome on Android)</li>"
        "<li>What you expected and what happened instead</li></ul>"
        "<p>Please do not attach private documents to your email. We usually reply within a few business days.</p>" % (esc(CONTACT_EMAIL), esc(CONTACT_EMAIL)))

    info_page("/privacy-policy/", "Privacy Policy – File1pdfedit",
        "How File1pdfedit handles your files, cookies, advertising and analytics. Your PDFs are processed locally and never uploaded.", "Privacy Policy",
        "<p><em>Last updated: %(d)s</em></p>"
        "<p>This Privacy Policy explains how %(n)s (&ldquo;we&rdquo;, &ldquo;our&rdquo;) handles information when you use %(u)s.</p>"
        "<h2>Your files</h2><p>All PDF and image processing happens inside your web browser on your own device. Files you select are not uploaded to, "
        "stored on or viewed by our servers.</p>"
        "<h2>Information we collect</h2><p>We do not ask you to create an account and we do not collect your name or email address through the tools. "
        "If you contact us by email, we keep your message and address only to reply to you.</p>"
        "<p>Like most websites, our hosting provider (Cloudflare) may process technical data such as IP address, browser type and pages requested "
        "to deliver the site and protect it from abuse. We may use privacy-friendly analytics to count visits.</p>"
        "<h2>Cookies and advertising</h2><p>We show ads provided by third-party advertising partners, which may include Google AdSense and Adsterra. "
        "These partners may use cookies, web beacons and similar technologies to serve ads based on your visits to this and other websites.</p>"
        "<ul><li>Google, as a third-party vendor, uses cookies to serve ads on this site. Google&rsquo;s use of advertising cookies enables it and its partners "
        "to serve ads based on your visit to this site and other sites on the internet.</li>"
        "<li>You can opt out of personalized advertising by visiting <a href=\"https://www.google.com/settings/ads\" rel=\"noopener\">Google Ads Settings</a>.</li>"
        "<li>You can learn more about how Google uses data at <a href=\"https://policies.google.com/technologies/partner-sites\" rel=\"noopener\">policies.google.com/technologies/partner-sites</a>.</li>"
        "<li>You can also opt out of some third-party vendors&rsquo; use of cookies at <a href=\"https://www.aboutads.info\" rel=\"noopener\">aboutads.info</a>.</li></ul>"
        "<p>If you are in the European Economic Area, the United Kingdom or Switzerland, you may be shown a consent message so you can choose how your data is used for advertising.</p>"
        "<h2>Third-party libraries</h2><p>The tools load open-source libraries (pdf-lib, PDF.js and JSZip) from the cdnjs content delivery network when you use a tool. "
        "Your browser contacts that network to download the code. Your documents are not sent to it.</p>"
        "<h2>Children</h2><p>This site is not directed to children under 13 and we do not knowingly collect personal information from them.</p>"
        "<h2>Your rights</h2><p>Depending on where you live, you may have rights to access, correct or delete personal data. "
        "Because we hold almost no personal data, there is usually little to delete, but you can contact us at any time.</p>"
        "<h2>Changes</h2><p>We may update this policy and will change the date above when we do.</p>"
        "<h2>Contact</h2><p>Questions about this policy? Email <a href=\"mailto:%(e)s\">%(e)s</a> or visit the <a href=\"/contact/\">contact page</a>.</p>"
        % dict(d=LAST_UPDATED, n=SITE_NAME, u=SITE_URL, e=esc(CONTACT_EMAIL)))

    info_page("/terms-of-use/", "Terms of Use – File1pdfedit",
        "The terms that apply when you use File1pdfedit and its free online PDF tools.", "Terms of Use",
        "<p><em>Last updated: %(d)s</em></p>"
        "<p>By using %(n)s you agree to these terms. If you do not agree, please do not use the site.</p>"
        "<h2>Use of the service</h2><p>You may use the tools for personal and commercial purposes. You must not use the site to break the law, "
        "infringe other people&rsquo;s rights, or try to disrupt or attack the service.</p>"
        "<h2>Your content</h2><p>You keep all rights to your files. Because processing happens on your device, we do not receive or store your files. "
        "You are responsible for having the right to process the documents you use.</p>"
        "<h2>No warranty</h2><p>The tools are provided &ldquo;as is&rdquo; without warranties of any kind. We do not guarantee that results will be error-free "
        "or suitable for a particular purpose. Always keep a copy of your original files and check the output before relying on it.</p>"
        "<h2>Limitation of liability</h2><p>To the fullest extent permitted by law, %(n)s is not liable for any loss or damage arising from your use of the site or its tools, "
        "including loss of data.</p>"
        "<h2>Advertising and third-party links</h2><p>The site displays advertising and may link to third-party websites. We are not responsible for their content or practices.</p>"
        "<h2>Changes</h2><p>We may change the tools or these terms at any time. Continued use after a change means you accept the new terms.</p>"
        "<h2>Contact</h2><p>Questions? Visit our <a href=\"/contact/\">contact page</a>.</p>" % dict(d=LAST_UPDATED, n=SITE_NAME))

def build_404():
    tl = "".join('<li><a href="/%s/">%s</a></li>' % (t["slug"], esc(t["name"])) for t in TOOLS)
    main_html = ('<main id="main"><div class="wrap prose"><h1>Page not found</h1><p>That page does not exist or has moved. Try one of our tools:</p>'
            '<ul class="related">%s</ul><p><a class="btn" href="/">Go to the homepage</a></p></div></main>') % tl
    write("404.html", head("/404.html", "Page not found – File1pdfedit", "The page you are looking for does not exist.", noindex=True) + "<body>" + header("") + main_html + footer())

# ---------------------------------------------------------------- SEO files
def build_seo_files():
    urls = ["/"] + ["/%s/" % t["slug"] for t in TOOLS] + ["/about/", "/contact/", "/privacy-policy/", "/terms-of-use/"]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append("<url><loc>%s</loc><lastmod>%s</lastmod></url>" % (url(u), LAST_UPDATED))
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm) + "\n")
    write("robots.txt", "User-agent: *\nAllow: /\n\nUser-agent: Mediapartners-Google\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE_URL)
    write("site.webmanifest", json.dumps({"name": SITE_NAME, "short_name": SITE_NAME, "start_url": "/", "display": "standalone",
        "background_color": "#f3f6fb", "theme_color": "#d92d20",
        "icons": [{"src": "/android-chrome-192x192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "/android-chrome-512x512.png", "sizes": "512x512", "type": "image/png"}]}, indent=2))
    write("_headers",
          "/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n\n"
          "/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n\n"
          "/*.png\n  Cache-Control: public, max-age=604800\n\n"
          "/sitemap.xml\n  Cache-Control: public, max-age=3600\n  Content-Type: application/xml; charset=utf-8\n")
    if ADSENSE_CLIENT:
        write("ads.txt", "google.com, %s, DIRECT, f08c47fec0942fa0\n" % ADSENSE_CLIENT.replace("ca-", ""))
    elif (OUT / "ads.txt").exists():
        (OUT / "ads.txt").unlink()
    for old in OUT.glob("*.txt"):          # remove stale IndexNow key files
        if old.name not in ("robots.txt", "ads.txt") and len(old.stem) >= 8 and old.stem != INDEXNOW_KEY:
            old.unlink()
    write("%s.txt" % INDEXNOW_KEY, INDEXNOW_KEY)

def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    shutil.copy(SRC / "style.css", OUT / "assets" / "style.css")
    shutil.copy(SRC / "app.js", OUT / "assets" / "app.js")
    build_home()
    for t in TOOLS:
        build_tool(t)
    build_info_pages()
    build_404()
    build_seo_files()
    print("Built %d pages for %s into %s" % (len(TOOLS) + 6, SITE_URL, OUT))
    if "example.com" in CONTACT_EMAIL:
        print("WARNING: set CONTACT_EMAIL in build.py before publishing.")

if __name__ == "__main__":
    main()
