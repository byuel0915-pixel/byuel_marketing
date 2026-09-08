# -*- coding: utf-8 -*-
"""포폴 장표를 '화면 그대로' PDF로 뽑는다 (클릭 가능한 링크 + 영상 썸네일 포함).

Chrome 인쇄 엔진은 페이지 폭을 좁게 잡아 .pf-grid / .proj-grid 가 1단으로 무너진다
(프로필 장에서 사진이 페이지를 다 먹는 증상). 그래서 인쇄를 쓰지 않고 슬라이드를
한 장씩 데스크톱 뷰포트로 캡처해 PDF로 묶은 뒤, <a> 좌표를 뽑아 링크 주석을 얹는다.

사용: python3 tools/export-pdf.py [출력경로]
"""
import os, re, io, json, base64, subprocess, sys, urllib.request

SRC = "/Users/LG/Desktop/byuel_marketing/portfolio-v15.html"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/Users/LG/Desktop/박성진_포트폴리오_v2.pdf"
TMP = "/private/tmp/claude-501/-Users-LG-Desktop-mola/507dee7f-3928-4a6b-9190-946e29751682/scratchpad/exp2"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H, SCALE = 1512, 945, 2
PW, PH = 400 / 25.4 * 72, 250 / 25.4 * 72      # 400x250mm (pt)
K = PW / W                                      # CSS px -> pt

os.makedirs(TMP, exist_ok=True)
src = open(SRC, encoding="utf-8").read()

# ── 1. 영상 iframe -> 유튜브 썸네일 + 재생 배지 + 링크 ────────────────
def thumb_data_uri(vid):
    for name in ("oardefault", "maxresdefault", "hqdefault"):
        try:
            req = urllib.request.Request(
                "https://i.ytimg.com/vi/%s/%s.jpg" % (vid, name),
                headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req, timeout=15).read()
            if len(raw) > 3000:
                return "data:image/jpeg;base64," + base64.b64encode(raw).decode()
        except Exception:
            pass
    return None

VID_RE = re.compile(
    r'<div class="frame vid"><div class="shot"([^>]*)>'
    r'<iframe src="https://www\.youtube\.com/embed/([\w-]+)"[^>]*></iframe></div>'
    r'<a class="cap" href="([^"]+)"[^>]*>([^<]+)</a></div>')

def swap(m):
    style, vid, href, cap = m.groups()
    uri = thumb_data_uri(vid)
    if not uri:
        return m.group(0)
    return ('<div class="frame vid"><a class="shot" %s href="%s" target="_blank" rel="noopener">'
            '<img src="%s" alt="%s" /><span class="ytplay"></span></a>'
            '<a class="cap" href="%s" target="_blank" rel="noopener">%s</a></div>'
            % (style, href, uri, cap.replace(' ↗', ''), href, cap))

src, n_thumb = VID_RE.subn(swap, src)
print("영상 썸네일 교체:", n_thumb, "건")

EXTRA_CSS = """<style>
#bar,#jump{display:none!important}
html,body{overflow:hidden!important}
.frame.vid .shot{position:relative;text-decoration:none}
.frame.vid .shot img{object-fit:contain}
.ytplay{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
  width:52px;height:52px;border-radius:50%;background:rgba(0,0,0,.55);
  border:2px solid rgba(255,255,255,.92);display:flex;align-items:center;justify-content:center}
.ytplay::after{content:"";width:0;height:0;margin-left:4px;
  border-left:17px solid #fff;border-top:10px solid transparent;border-bottom:10px solid transparent}
/* 썸네일로 못 바꾼 영상 프레임은 캡처에서 죽은 화면이라 숨긴다 */
.frame.vid:not(:has(img)){display:none!important}
.frames:not(:has(.frame:not(.vid))):not(:has(img)){display:none!important}
</style>"""

LINK_JS = """<script>window.addEventListener('load',function(){setTimeout(function(){
var o=[];document.querySelectorAll('a[href]').forEach(function(a){
  var r=a.getBoundingClientRect();
  if(r.width<3||r.height<3||r.bottom<0||r.top>window.innerHeight) return;
  o.push({x:r.left,y:r.top,w:r.width,h:r.height,u:a.href});});
var p=document.createElement('pre');p.id='LK';p.textContent=JSON.stringify(o);
document.body.appendChild(p);},1200);});</script>"""

n = src.count('<section class="slide')
shots, links = [], []
for i in range(1, n + 1):
    only = "<style>.slide{display:none!important}.slide:nth-of-type(%d){display:flex!important}</style>" % i
    body = src.replace("</head>", EXTRA_CSS + only + "</head>")
    page, png = TMP + "/s%02d.html" % i, TMP + "/s%02d.png" % i
    open(page, "w", encoding="utf-8").write(body)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=%d" % SCALE, "--window-size=%d,%d" % (W, H),
                    "--virtual-time-budget=9000", "--screenshot=" + png,
                    "file://" + page], capture_output=True)
    shots.append(png)
    # 같은 페이지에 좌표 수집 스크립트만 얹어 링크 위치를 뽑는다
    lpage = TMP + "/l%02d.html" % i
    open(lpage, "w", encoding="utf-8").write(body.replace("</body>", LINK_JS + "</body>"))
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--window-size=%d,%d" % (W, H), "--virtual-time-budget=9000",
                        "--dump-dom", "file://" + lpage], capture_output=True, text=True)
    m = re.search(r'<pre id="LK">(.*?)</pre>', r.stdout, re.S)
    import html as _h
    links.append(json.loads(_h.unescape(m.group(1))) if m else [])

import fitz
from PIL import Image
doc = fitz.open()
total = 0
for png, ls in zip(shots, links):
    im = Image.open(png).convert("RGB")
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=88, optimize=True)
    pg = doc.new_page(width=PW, height=PH)
    pg.insert_image(fitz.Rect(0, 0, PW, PH), stream=buf.getvalue())
    for l in ls:
        rect = fitz.Rect(l["x"] * K, l["y"] * K, (l["x"] + l["w"]) * K, (l["y"] + l["h"]) * K)
        pg.insert_link({"kind": fitz.LINK_URI, "from": rect, "uri": l["u"]})
        total += 1
doc.save(OUT, deflate=True)
print("pages:", doc.page_count, "| 링크:", total, "개 |",
      round(os.path.getsize(OUT) / 1024 / 1024, 1), "MB ->", OUT)
