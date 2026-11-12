# File1pdfedit – static PDF tools website

Plain HTML/CSS/JS. No frameworks, no build tools on Cloudflare. All PDF work runs in the visitor's browser.

## Folder layout
- `public/`    – the finished website (this is what Cloudflare publishes)
- `src/`       – style.css and app.js (the tool engine); `build.py` copies them into public/
- `content.py` – all tool text, FAQs, guides
- `build.py`   – page generator + settings (email, ads, SITE_URL). Re-run after any change: `python build.py`
- `indexnow.py`– optional: pings Bing/Yandex after each deploy

## Publish (free)
1. Edit `CONTACT_EMAIL` in build.py, then run `python build.py` (needs Python 3 only).
2. Create a GitHub repo, then in this folder:
   git init && git add . && git commit -m "First version" && git branch -M main
   git remote add origin https://github.com/YOUR-USER/file1pdfedit.git && git push -u origin main
3. Cloudflare dashboard > Workers & Pages > Create > Pages > Connect to Git > pick the repo.
   Framework preset: None. Build command: (empty). Build output directory: public. Save and Deploy.
4. Project name `file1pdfedit` gives https://file1pdfedit.pages.dev (if taken, pick another name and run
   `SITE_URL=https://yourname.pages.dev python build.py`, then commit and push).
5. Google Search Console > add property (URL prefix) > verify > Sitemaps > submit `sitemap.xml`. Use URL Inspection > Request indexing for the homepage and each tool page.
6. Bing Webmaster Tools > import from Search Console. Then run `python indexnow.py`.

## Ads
Set ADSENSE_CLIENT / ADSENSE_SLOT / ADSTERRA_BANNER_HTML in build.py, rebuild, commit, push.
