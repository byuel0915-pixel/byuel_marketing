# -*- coding: utf-8 -*-
"""포폴 장표를 '화면 그대로' PDF로 뽑는다.

Chrome의 인쇄 엔진은 페이지 폭을 좁게 잡아 .pf-grid / .proj-grid 가 1단으로
무너진다(프로필 장에서 사진이 페이지를 다 먹는 증상). 그래서 인쇄를 쓰지 않고
슬라이드를 한 장씩 데스크톱 뷰포트로 캡처해 PDF로 묶는다.
"""
import os, re, subprocess, sys, io

SRC = "/Users/LG/Desktop/byuel_marketing/portfolio-v15.html"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/Users/LG/Desktop/박성진_포트폴리오.pdf"
TMP = "/private/tmp/claude-501/-Users-LG-Desktop-mola/507dee7f-3928-4a6b-9190-946e29751682/scratchpad/exp"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H, SCALE = 1512, 945, 2

os.makedirs(TMP, exist_ok=True)
src = open(SRC, encoding="utf-8").read()
n = src.count('<section class="slide')

shots = []
for i in range(1, n + 1):
    css = ("<style>#bar,#jump{display:none!important}"
           ".slide{display:none!important}"
           ".slide:nth-of-type(%d){display:flex!important}"
           "html,body{overflow:hidden!important}"
           # 영상 임베드는 캡처에서 죽은 프레임으로 남는다
           ".frame.vid{display:none!important}"
           ".frames:not(:has(.frame:not(.vid))){display:none!important}"
           "</style>") % i
    page = TMP + "/s%02d.html" % i
    png = TMP + "/s%02d.png" % i
    open(page, "w", encoding="utf-8").write(src.replace("</head>", css + "</head>"))
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=%d" % SCALE,
                    "--window-size=%d,%d" % (W, H),
                    "--virtual-time-budget=9000",
                    "--screenshot=" + png, "file://" + page], capture_output=True)
    shots.append(png)

import fitz
from PIL import Image
doc = fitz.open()
PW, PH = 400 / 25.4 * 72, 250 / 25.4 * 72   # 400x250mm
for png in shots:
    im = Image.open(png).convert("RGB")
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=88, optimize=True)
    pg = doc.new_page(width=PW, height=PH)
    pg.insert_image(fitz.Rect(0, 0, PW, PH), stream=buf.getvalue())
doc.save(OUT, deflate=True)
print("pages:", doc.page_count, "|", round(os.path.getsize(OUT) / 1024 / 1024, 1), "MB")
