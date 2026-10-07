import json, re
from pathlib import Path

idx=Path("index.html").read_text(encoding="utf-8")
m=re.search(r"const QUESTIONS=(\[[\s\S]*?\]);\nconst PDF=",idx)
if not m:
    raise RuntimeError("R7 question metadata not found in current index")
r7=json.loads(m.group(1))
r6=json.loads(Path("r6_meta.json").read_text(encoding="utf-8"))["questions"]
if len(r7)!=60 or len(r6)!=60:
    raise RuntimeError(f"Unexpected counts R7={len(r7)} R6={len(r6)}")

R7=json.dumps(r7,ensure_ascii=False,separators=(",",":"))
R6=json.dumps(r6,ensure_ascii=False,separators=(",",":"))

html=r'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#087c91">
<title>下3トレーナー｜実過去問</title>
<style>
:root{--bg:#f3f7f8;--card:#fff;--ink:#17242a;--muted:#64777f;--line:#d5e0e3;--main:#087c91;--good:#0d8a5f;--bad:#c63f44;--warn:#d7780b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Hiragino Kaku Gothic ProN","Yu Gothic",Meiryo,sans-serif;line-height:1.55}
button,select{font:inherit}button{cursor:pointer}.shell{max-width:980px;margin:auto;padding:12px 12px 96px}
.hero{background:linear-gradient(135deg,#075f73,#0aa4b5);color:#fff;border-radius:22px;padding:18px;margin:5px 0 12px}.hero h1{margin:4px 0;font-size:1.5rem}.hero p{margin:4px 0;color:#eaffff}.badge{display:inline-block;background:#fff;color:#086a7d;padding:3px 8px;border-radius:999px;font-weight:900;font-size:.72rem;margin-right:4px}
.card{background:#fff;border:1px solid var(--line);border-radius:18px;padding:14px;margin:10px 0;box-shadow:0 6px 20px rgba(20,60,70,.06)}
h2{font-size:1.08rem;color:#075f73;margin:2px 0 10px}.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.btn{border:0;border-radius:12px;padding:10px 13px;font-weight:850;background:#e9f0f2;color:#21404b}.btn.primary{background:var(--main);color:#fff}.btn.good{background:#e6f6ef;color:#08734e}.btn.bad{background:#fdecee;color:#a9242c}
select{border:1px solid #cbd8dc;background:#fff;border-radius:11px;padding:9px 10px}
.notice{background:#fff8df;border:1px solid #ead17a;border-radius:12px;padding:10px;font-size:.88rem}.muted{color:var(--muted);font-size:.84rem}
.viewer{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff}.viewer img{display:block;width:100%;height:auto}.viewer iframe{display:block;width:100%;height:62vh;min-height:520px;border:0;background:#fff}
.qhead{display:flex;justify-content:space-between;gap:8px;align-items:center}.qnum{font-weight:950;color:#075f73}
.answers{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:12px 0}.choice{border:2px solid #cbdadd;background:#fff;border-radius:14px;padding:14px;font-size:1.2rem;font-weight:950}.choice.correct{border-color:var(--good);background:#e9f8f1;color:#086a49}.choice.wrong{border-color:var(--bad);background:#fff0f1;color:#aa2830}
.reveal{display:none}.reveal.show{display:block}.box{border-left:5px solid var(--main);background:#f1fafb;border-radius:10px;padding:10px 11px;margin:8px 0}.trap{border-color:#718891;background:#f5f7f8}.memo{border-color:var(--warn);background:#fff4e7;font-weight:800}.formula{white-space:pre-wrap;background:#112d38;color:#f2fbfd;padding:9px 10px;border-radius:10px;font-family:ui-monospace,monospace;font-size:.85rem}
.progress{height:9px;background:#e1eaec;border-radius:999px;overflow:hidden}.progress i{display:block;height:100%;background:linear-gradient(90deg,#087c91,#0aa4b5);width:0}.navrow{display:flex;justify-content:space-between;gap:8px;margin-top:10px}
.bottom{position:fixed;left:0;right:0;bottom:0;background:rgba(255,255,255,.96);backdrop-filter:blur(10px);border-top:1px solid var(--line);padding:8px 12px calc(8px + env(safe-area-inset-bottom));z-index:30}.bottomin{max-width:980px;margin:auto;display:flex;justify-content:center;gap:8px}
.hidden{display:none!important}
@media(max-width:620px){.answers{grid-template-columns:repeat(2,1fr)}.viewer iframe{height:56vh;min-height:450px}}
</style>
</head>
<body>
<div class="shell">
<header class="hero">
<span class="badge">下水道技術検定 第3種</span><span class="badge">実過去問</span><span class="badge">v0.8</span>
<h1>💧 下3トレーナー</h1>
<p>本当に出た問題を解く。回答後にチャッピー解説。</p>
</header>

<div class="card">
<h2 id="yearHeading">令和7年度 第51回</h2>
<div id="sourceNotice" class="notice"></div>
<div class="row" style="margin-top:10px">
<label>年度
<select id="yearSelect" onchange="switchYear(this.value)">
<option value="R7">令和7年度・第51回</option>
<option value="R6">令和6年度・第50回</option>
</select></label>
<label>問<select id="qSelect"></select></label>
<button class="btn primary" onclick="goSelected()">この問へ</button>
<a id="sourceLink" class="btn" style="text-decoration:none" href="#" target="_blank" rel="noopener">問題を別画面で開く</a>
</div>
<div class="progress" style="margin-top:12px"><i id="prog"></i></div>
<div class="muted" id="stat">0 / 60問回答済み</div>
</div>

<div class="card">
<div class="qhead"><span class="qnum" id="qLabel">問1</span><span class="muted" id="cat"></span></div>
<div class="viewer">
<a id="r7PageLink" href="./r7_pages/page-002.jpg" target="_blank" rel="noopener"><img id="r7Page" alt="令和7年度 第3種 公式問題ページ" src="./r7_pages/page-002.jpg"></a>
<iframe id="r6Frame" class="hidden" title="令和6年度 第50回 第3種 実問題" src="./r6_archive.html#r6q1"></iframe>
</div>
<div class="muted" id="viewerNote" style="margin-top:7px"></div>

<div class="answers">
<button class="choice" data-a="1" onclick="answer(1)">1</button>
<button class="choice" data-a="2" onclick="answer(2)">2</button>
<button class="choice" data-a="3" onclick="answer(3)">3</button>
<button class="choice" data-a="4" onclick="answer(4)">4</button>
</div>

<div id="reveal" class="reveal">
<div class="box"><b id="correctLine"></b><br><span id="explain"></span></div>
<div id="formula" class="formula" style="display:none"></div>
<div class="box trap"><b>ここで引っかけ：</b> <span id="trap"></span></div>
<div class="box memo">🧠 <span id="memo"></span></div>
</div>

<div class="navrow">
<button class="btn" onclick="move(-1)">← 前の問</button>
<button class="btn primary" onclick="move(1)">次の問 →</button>
</div>
</div>

<div class="card">
<h2>収録状況</h2>
<p>✅ 令和7年度 第51回：日本下水道事業団の公式PDF原本を表示用画像化。</p>
<p>✅ 令和6年度 第50回：実問題の保存アーカイブを収録。問1〜60と正答60問を照合済み。</p>
<p class="muted">令和6年度は現在JS公式サイトで問題PDF本体が公開されていないため、保存アーカイブを使用しています。似た問題・生成問題への置換はしていません。</p>
</div>
</div>

<nav class="bottom"><div class="bottomin">
<button class="btn primary" onclick="window.scrollTo({top:0,behavior:'smooth'})">🏠 上へ</button>
<button class="btn" onclick="resetProgress()">履歴リセット</button>
</div></nav>

<script>
const R7_QUESTIONS=__R7__;
const R6_QUESTIONS=__R6__;
const SETS={R7:R7_QUESTIONS,R6:R6_QUESTIONS};
let PAGE_MAP={};
let currentYear=localStorage.getItem("gesuido3_year")||"R7";
if(!SETS[currentYear])currentYear="R7";
let QUESTIONS=SETS[currentYear];
let pos=0;

function stateKey(){return "gesuido3_real_"+currentYear+"_v08"}
function loadState(){try{return JSON.parse(localStorage.getItem(stateKey())||'{"answered":{}}')}catch(e){return {answered:{}}}}
let state=loadState();
function save(){localStorage.setItem(stateKey(),JSON.stringify(state));updateStat()}
function q(){return QUESTIONS[pos]}
function approxPage(n){return Math.max(2,Math.min(29,2+Math.floor((n-1)*27/59)))}

function rebuildQSelect(){
 const s=document.getElementById("qSelect");s.innerHTML="";
 QUESTIONS.forEach(x=>{const o=document.createElement("option");o.value=x.q;o.textContent=x.q;s.appendChild(o)});
}

function updateSourceUI(){
 const is7=currentYear==="R7";
 document.getElementById("yearHeading").textContent=is7?"令和7年度 第51回":"令和6年度 第50回";
 document.getElementById("sourceNotice").innerHTML=is7
 ? "<b>日本下水道事業団の公式問題そのものです。</b><br>公式PDF原本をスマホ表示用にページ画像化。問題文・図表は作り替えていません。<br><span class='muted'>出典：日本下水道事業団「令和7年度 第51回 下水道技術検定 問題 第3種」</span>"
 : "<b>令和6年度 第50回に実際に出題された問題です。</b><br>現在JS公式サイトでは問題PDF本体が公開終了しているため、保存されている実問題アーカイブを使用。問1〜60と正答を照合済みです。";
 const link=document.getElementById("sourceLink");
 link.href=is7?"./r7_mondai_3syu_official.pdf":"./r6_archive.html#r6q"+q().q;
 link.textContent=is7?"公式PDFを別画面で開く":"R6実問題を別画面で開く";
 document.getElementById("viewerNote").textContent=is7
 ? "画像をタップすると拡大できます。"
 : "保存アーカイブの実問題を表示しています。問番号を変えると該当問題へ移動します。";
}

function render(){
 const x=q(),is7=currentYear==="R7";
 document.getElementById("yearSelect").value=currentYear;
 document.getElementById("qLabel").textContent=(is7?"令和7年度 公式 ":"令和6年度 実問題 ")+"問"+x.q;
 document.getElementById("cat").textContent=x.category+"｜"+(is7?"第51回":"第50回");
 document.getElementById("qSelect").value=String(x.q);
 const r7=document.getElementById("r7Page"),r7l=document.getElementById("r7PageLink"),r6=document.getElementById("r6Frame");
 if(is7){
   const page=PAGE_MAP[String(x.q)]||approxPage(x.q);
   const src="./r7_pages/page-"+String(page).padStart(3,"0")+".jpg";
   r7.src=src;r7.alt="令和7年度 第3種 公式問題 問"+x.q+" 掲載ページ";r7l.href=src;
   r7l.classList.remove("hidden");r6.classList.add("hidden");
 }else{
   r7l.classList.add("hidden");r6.classList.remove("hidden");
   r6.src="./r6_archive.html#r6q"+x.q;
 }
 updateSourceUI();
 document.getElementById("reveal").classList.remove("show");
 document.querySelectorAll(".choice").forEach(b=>b.className="choice");
 const prev=state.answered[x.id];if(prev)showAnswer(prev.choice,false);
 updateStat();
 window.scrollTo({top:document.querySelector(".qhead").getBoundingClientRect().top+window.scrollY-10,behavior:"smooth"});
}
function answer(a){showAnswer(a,true)}
function showAnswer(a,record){
 const x=q();
 if(record){state.answered[x.id]={choice:a,correct:a===x.answer};save()}
 document.querySelector('.choice[data-a="'+x.answer+'"]').classList.add("correct");
 if(a!==x.answer)document.querySelector('.choice[data-a="'+a+'"]').classList.add("wrong");
 document.getElementById("correctLine").textContent="正答：("+x.answer+")";
 document.getElementById("explain").textContent=x.explain;
 document.getElementById("trap").textContent=x.trap||"設問の条件・主語・数値を確認。";
 document.getElementById("memo").textContent=x.memo||"";
 const f=document.getElementById("formula");if(x.formula){f.textContent=x.formula;f.style.display="block"}else f.style.display="none";
 document.getElementById("reveal").classList.add("show");
}
function move(d){pos=Math.max(0,Math.min(59,pos+d));render()}
function goSelected(){pos=Math.max(0,Math.min(59,Number(document.getElementById("qSelect").value)-1));render()}
function switchYear(y){
 currentYear=y;localStorage.setItem("gesuido3_year",y);QUESTIONS=SETS[y];pos=0;state=loadState();rebuildQSelect();render();
}
function updateStat(){
 const n=Object.keys(state.answered||{}).length;
 document.getElementById("stat").textContent=n+" / 60問回答済み";
 document.getElementById("prog").style.width=(n/60*100)+"%";
}
function resetProgress(){if(confirm(currentYear+"の回答履歴をリセットする？")){state={answered:{}};save();render()}}
(async function init(){
 try{const r=await fetch("./r7_page_map.json",{cache:"no-store"});if(r.ok){const j=await r.json();PAGE_MAP=j.question_to_page||{}}}catch(e){}
 rebuildQSelect();state=loadState();render();
})();
</script>
</body>
</html>'''.replace("__R7__",R7).replace("__R6__",R6)

Path("index.html").write_text(html,encoding="utf-8")
print("built v0.8",len(r7),len(r6))
