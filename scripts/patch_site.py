from pathlib import Path

p = Path("index.html")
s = p.read_text(encoding="utf-8")

pairs = [
    ("v0.6", "v0.7"),
    (".pdfwrap iframe{display:block;width:100%;height:58vh;min-height:480px;border:0}", ".pdfwrap img{display:block;width:100%;height:auto;border:0;background:#fff}"),
    ("@media(max-width:620px){.pdfwrap iframe{height:52vh;min-height:420px}.answers", "@media(max-width:620px){.answers"),
    ('href="https://www.jswa.go.jp/kentei/pdf/r7mondai_seito/mondai_3syu.pdf" target="_blank" rel="noopener">公式PDFを別画面で開く', 'href="./r7_mondai_3syu_official.pdf" target="_blank" rel="noopener">公式PDFを別画面で開く'),
    ('<iframe id="officialPdf" title="令和7年度 第3種 公式問題PDF" src=""></iframe>', '<a id="pageLink" href="./r7_pages/page-002.jpg" target="_blank" rel="noopener"><img id="officialPage" alt="令和7年度 第3種 公式問題ページ" src="./r7_pages/page-002.jpg"></a>'),
    ("※GoogleのPDFビューア経由で公式問題を表示しています。表示されない場合は上の「公式PDFを別画面で開く」を押してください。", "※日本下水道事業団の公式問題PDFを、スマホ表示用にページ画像へ変換して表示しています。画像をタップすると拡大できます。"),
    ('const PDF="https://www.jswa.go.jp/kentei/pdf/r7mondai_seito/mondai_3syu.pdf";\nconst PDF_VIEWER="https://docs.google.com/gview?embedded=1&url="+encodeURIComponent(PDF);', 'const PDF="./r7_mondai_3syu_official.pdf";\nlet PAGE_MAP={};'),
    (" document.getElementById('officialPdf').src=PDF_VIEWER;", " const page=PAGE_MAP[String(x.q)]||approxPage(x.q);\n const pageSrc='./r7_pages/page-'+String(page).padStart(3,'0')+'.jpg';\n document.getElementById('officialPage').src=pageSrc;\n document.getElementById('officialPage').alt='令和7年度 第3種 公式問題 問'+x.q+' 掲載ページ';\n document.getElementById('pageLink').href=pageSrc;"),
    ('<div class="notice"><b>問題本文・図表は日本下水道事業団の公式PDFをそのまま表示します。</b><br>このサイト側で問題文を作り替えません。下のPDFで「問○」を読んで、1〜4を押してください。</div>', '<div class="notice"><b>問題本文・図表は日本下水道事業団の令和7年度 第51回 第3種・公式問題です。</b><br>このサイト側で問題文を作り替えません。公式PDFを表示用画像へ変換し、問番号に対応する本物のページを表示します。<br><span class="muted">出典：地方共同法人 日本下水道事業団「令和7年度 第51回 下水道技術検定 問題 第3種」</span></div>'),
]

for old, new in pairs:
    s = s.replace(old, new)

old_init = """(function init(){
 const s=document.getElementById('qSelect');
 QUESTIONS.forEach(x=>{const o=document.createElement('option');o.value=x.q;o.textContent=x.q;s.appendChild(o)});
 updateStat();render();
})();"""

new_init = """(async function init(){
 const s=document.getElementById('qSelect');
 QUESTIONS.forEach(x=>{const o=document.createElement('option');o.value=x.q;o.textContent=x.q;s.appendChild(o)});
 try{
   const r=await fetch('./r7_page_map.json',{cache:'no-store'});
   if(r.ok){const j=await r.json();PAGE_MAP=j.question_to_page||{}}
 }catch(e){}
 updateStat();render();
})();"""

s = s.replace(old_init, new_init)
p.write_text(s, encoding="utf-8")
print("patched index.html")
