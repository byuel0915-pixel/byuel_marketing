# -*- coding: utf-8 -*-
"""포폴 장표를 '화면 그대로' PDF로 뽑는다 (클릭 가능한 링크 + 영상 썸네일 포함).

- Chrome 인쇄 엔진은 페이지 폭을 좁게 잡아 .pf-grid / .proj-grid 가 1단으로 무너진다
  (프로필 장에서 사진이 페이지를 다 먹는 증상). 그래서 인쇄를 쓰지 않고 캡처한다.
- 캡처와 <a> 좌표는 반드시 '한 번의 Chrome 실행'에서 같이 받아야 한다. --dump-dom 을
  따로 돌리면 레이아웃 뷰포트 높이가 달라져(945 vs 858) 100svh 기준 위치가 밀린다.
- 좌표는 슬라이드 박스 기준으로 정규화하고, 이미지도 그 박스로 크롭한다.

사용: python3 tools/export-pdf.py [출력경로]
"""
import os, re, io, json, base64, subprocess, sys, urllib.request, html as _html

SRC = "/Users/LG/Desktop/byuel_marketing/portfolio-v15.html"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/Users/LG/Desktop/박성진_포트폴리오_v2.pdf"
TMP = "/private/tmp/claude-501/-Users-LG-Desktop-mola/507dee7f-3928-4a6b-9190-946e29751682/scratchpad/exp3"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H, SCALE = 1512, 945, 2
PAGE_W_MM = 400.0

os.makedirs(TMP, exist_ok=True)
src = open(SRC, encoding="utf-8").read()

# ── 1. 영상 iframe -> 유튜브 썸네일 + 재생 배지 + 링크 ────────────────
def thumb_data_uri(vid):
    for name in ("oardefault", "maxresdefault", "hqdefault"):
        try:
            req = urllib.request.Request("https://i.ytimg.com/vi/%s/%s.jpg" % (vid, name),
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
.frame.vid:not(:has(img)){display:none!important}
.frames:not(:has(.frame:not(.vid))):not(:has(img)){display:none!important}
/* 뷰포트 높이 의존 제거 — 캡처 시점과 측정 시점의 layout viewport(945 vs 858)가
   달라 100svh 중앙정렬이 밀리는 문제를 막는다 */
.slide{min-height:945px!important;height:945px!important}
.frames{height:349px!important}
.frame .cap{font-size:12.2px!important}
</style>"""

MEAS_JS = """<script>window.addEventListener('load',function(){setTimeout(function(){
var s=document.querySelector('.slide[data-cap]');var b=s.getBoundingClientRect();
var o={box:[b.left,b.top,b.width,b.height],links:[]};
document.querySelectorAll('a[href]').forEach(function(a){var r=a.getBoundingClientRect();
  if(r.width<3||r.height<3) return;
  o.links.push({x:r.left-b.left,y:r.top-b.top,w:r.width,h:r.height,u:a.href});});
var p=document.createElement('pre');p.id='M';p.textContent=JSON.stringify(o);
document.body.appendChild(p);},1500);});</script>"""

n = src.count('<section class="slide')
pages = []
for i in range(1, n + 1):
    only = ("<style>.slide{display:none!important}"
            ".slide:nth-of-type(%d){display:flex!important}</style>") % i
    body = src.replace("</head>", EXTRA_CSS + only + "</head>").replace("</body>", MEAS_JS + "</body>")
    # 측정 대상 슬라이드 표시
    k = [m.start() for m in re.finditer(r'<section class="slide', body)][i - 1]
    body = body[:k] + '<section data-cap="1" class="slide' + body[k + len('<section class="slide'):]
    page, png = TMP + "/s%02d.html" % i, TMP + "/s%02d.png" % i
    open(page, "w", encoding="utf-8").write(body)
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=%d" % SCALE, "--window-size=%d,%d" % (W, H),
                        "--virtual-time-budget=9000", "--screenshot=" + png,
                        "--dump-dom", "file://" + page], capture_output=True, text=True)
    m = re.search(r'<pre id="M">(.*?)</pre>', r.stdout, re.S)
    if not m:
        raise SystemExit("슬라이드 %d 측정 실패" % i)
    pages.append((png, json.loads(_html.unescape(m.group(1)))))

import fitz
from PIL import Image
doc = fitz.open()
total = 0
for png, meta in pages:
    bx, by, bw, bh = meta["box"]
    im = Image.open(png).convert("RGB")
    im = im.crop((int(bx * SCALE), int(by * SCALE),
                  int((bx + bw) * SCALE), int((by + bh) * SCALE)))
    pw = PAGE_W_MM / 25.4 * 72
    ph = pw * bh / bw
    k = pw / bw                        # CSS px -> pt
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=88, optimize=True)
    pg = doc.new_page(width=pw, height=ph)
    pg.insert_image(fitz.Rect(0, 0, pw, ph), stream=buf.getvalue())
    for l in meta["links"]:
        pg.insert_link({"kind": fitz.LINK_URI, "uri": l["u"],
                        "from": fitz.Rect(l["x"] * k, l["y"] * k,
                                          (l["x"] + l["w"]) * k, (l["y"] + l["h"]) * k)})
        total += 1
doc.save(OUT, deflate=True)
print("pages:", doc.page_count, "| 링크:", total, "개 |",
      round(os.path.getsize(OUT) / 1024 / 1024, 1), "MB ->", OUT)
