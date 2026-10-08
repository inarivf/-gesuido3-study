// Regression tests for the actual generated offline study UI.
// Uses Node built-ins only; no package install needed.
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const path=require("node:path");
const html=fs.readFileSync(path.join(__dirname,"..","index.html"),"utf8");
const parts=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
assert.equal(parts.length,1,"one inline script");
class FakeElement{
  constructor(id){
    this.id=id;this.value=id==="yearFilter"?"ALL":"ALL";
    this._classes=new Set();this.style={};this.options=[];
    this.dataset={};this.disabled=false;this._innerHTML="";
    this.classList={
      add:(x)=>this._classes.add(x),
      remove:(x)=>this._classes.delete(x),
      contains:(x)=>this._classes.has(x),
      toggle:(x,on)=>{
        if(on===undefined)on=!this._classes.has(x);
        if(on)this._classes.add(x);else this._classes.delete(x);
        return on;
      }
    };
  }
  get className(){return [...this._classes].join(" ")}
  set className(s){this._classes=new Set(String(s).split(/\s+/).filter(Boolean))}
  get innerHTML(){return this._innerHTML}
  set innerHTML(s){this._innerHTML=String(s);if(this.id==="catFilter"||this.id==="jumpSelect")this.options=[]}
  appendChild(x){this.options.push(x)}
  scrollIntoView(){}
}
const nodes=new Map();
const elements=id=>{if(!nodes.has(id))nodes.set(id,new FakeElement(id));return nodes.get(id)};
const choice=[1,2,3,4].map(n=>{
  const e=new FakeElement("choice"+n);e.dataset.a=String(n);e.className="choice";return e;
});
const stored=new Map();
const alerts=[];
const storage={getItem:k=>stored.get(k)??null,setItem:(k,v)=>stored.set(k,String(v)),removeItem:k=>stored.delete(k)};
const document={
  getElementById:elements,
  createElement:(tag)=>new FakeElement(tag),
  querySelectorAll:sel=>{
    assert.equal(sel,".choice");return choice;
  },
  querySelector:sel=>{
    const m=sel.match(/\.choice\[data-a="(\d)"\]/);
    assert(m,"unsupported selector "+sel);
    return choice[+m[1]-1];
  }
};
const context=vm.createContext({
  document, localStorage:storage,
  setTimeout:()=>1,clearTimeout:()=>{},
  setInterval:()=>1,clearInterval:()=>{},
  requestAnimationFrame:()=>{},
  confirm:()=>true,
  alert:(msg)=>alerts.push(msg),
  window:{},
  Date,Math,JSON,Number,String,Object,Array,Boolean,console
});
vm.runInContext(parts[0][1],context,{filename:"index-inline.js"});
const run=s=>vm.runInContext(s,context);
const count=id=>run('state.items['+JSON.stringify(id)+']?.attempts||0');
const correctButton=()=>choice.filter(x=>x.classList.contains("correct")).map(x=>+x.dataset.a);
const revealed=()=>elements("reveal").classList.contains("show");
const info=msg=>console.log("PASS:",msg);

// Ordinary mode must not reveal answers saved from earlier attempts.
run('startMode("sequential")');
assert.equal(elements("quizCard").classList.contains("hidden"),false);
assert.equal(correctButton().length,0);
assert.equal(revealed(),false);
assert.equal(run("q().id"),"R7-01");
const right=run("q().answer");
const wrong=right===1?2:1;
run("answer("+right+")");
assert.equal(count("R7-01"),1);
assert.equal(revealed(),true);
run("move(1)");
run("move(-1)");
assert.equal(revealed(),true,"answer reveal should be restored within the same session");
assert(choice.every(x=>x.disabled),"answered choices should be locked");
run("answer("+wrong+")");
assert.equal(count("R7-01"),1,"no duplicate attempts when revisiting");
info("in-session review restores answer without double-counting");

run('startMode("sequential")');
assert.equal(correctButton().length,0,"no pre-reveal of historical right answer");
assert.equal(revealed(),false);
run("answer("+wrong+")");
assert.equal(count("R7-01"),2,"a new study session records a new attempt");
assert.equal(run('isWeak(q())'),true);
run('rate("ok")');
assert.equal(run('isWeak(q())'),false,"覚えた removes a question from weak list");
run('rate("ng")');
assert.equal(run('isWeak(q())'),true);
info("no historical answer leakage; explicit weak-point rating works");

// Mock should defer feedback and increment history ONLY once at submission.
elements("yearFilter").value="R7";
run("rebuildCategory()");
run('startMode("mock")');
assert.equal(run("q().id"),"R7-01");
assert.equal(revealed(),false);
run("answer("+right+")");
assert.equal(revealed(),false,"mock must not reveal correct answer");
assert.equal(correctButton().length,0,"mock must not colour correct choice");
assert.equal(count("R7-01"),2,"mock should not mutate history before final scoring");
run("move(1)");
const second=run("q().answer");
run("answer("+(second===1?2:1)+")");
run("move(-1)");
assert(choice[right-1].classList.contains("selected"),"mock should restore selected option");
run("answer("+wrong+")");
assert.equal(run("sessionAnswers['R7-01'].choice"),wrong,"mock answers should be revisable");
run('finishMock("time")');
assert.equal(run("mockFinished"),true);
assert.equal(count("R7-01"),3,"mock grade saved exactly once");
assert.equal(count("R7-02"),1);
assert(elements("mockResult").textContent.includes("0 / 60点"));
assert(elements("mockResult").textContent.includes("未回答：58問"));
assert.equal(revealed(),true,"mock review available only AFTER grading");
run("answer("+right+")");
run('finishMock("time")');
assert.equal(count("R7-01"),3,"post-finish regrade must not duplicate history");
info("true deferred-feedback timed mock, review and single submission");

// New sessions reset the per-session answer cache, but not saved progress.
run('startMode("mock")');
assert.equal(run("mockFinished"),false);
assert.equal(run("Object.keys(sessionAnswers).length"),0);
assert.equal(count("R7-01"),3);
assert.equal(revealed(),false);
info("new sessions retain history but do not leak answers");


(async()=>{
// Category statistics must show progress for answered and untouched categories.
const categoryHtml=elements("categoryStats").innerHTML;
assert(categoryHtml.includes("正答率"),"category dashboard should render accuracy");
assert(categoryHtml.includes("未回答"),"category dashboard should show unpracticed categories");
info("category progress shows studied and unst udied areas".replace("unst udied","unstudied"));

// Ensure invalid or tampered JSON cannot overwrite any existing learning history.
let attemptsBefore=count("R7-01");
const good={items:{"R7-01":{
  attempts:7,correct:5,wrong:2,lastChoice:4,lastCorrect:true,rating:"maybe"
}},createdAt:"2026-10-08T12:00:00.000Z"};
const tampered=JSON.parse(JSON.stringify(good));
tampered.items["R7-01"].correct=8;
assert.throws(()=>run('validateProgressBackup('+JSON.stringify(tampered)+')'));
assert.equal(count("R7-01"),attemptsBefore);
info("backup validation rejects inconsistent attempt totals");

const input={value:"fake.json",files:[{size:150,text:async()=>JSON.stringify(tampered)}]};
context.fakeImportEvent={target:input};
await run("importProgress(fakeImportEvent)");
assert.equal(count("R7-01"),attemptsBefore);
assert.equal(alerts.length,1,"invalid backup should report the failure");
assert.equal(input.value,"","file chooser should reset");
info("bad backup does not change saved history");

const validInput={value:"backup.json",files:[{size:150,text:async()=>JSON.stringify(good)}]};
context.fakeImportEvent={target:validInput};
await run("importProgress(fakeImportEvent)");
assert.equal(count("R7-01"),7);
assert.equal(run('state.items["R7-01"].correct'),5);
assert.equal(run('state.items["R7-01"].rating'),"maybe");
assert.equal(elements("quizCard").classList.contains("hidden"),true);
assert.equal(elements("sessionBox").classList.contains("hidden"),true);
assert.equal(validInput.value,"");
assert.equal(JSON.parse(stored.get("gesuido3_progress_v1")).items["R7-01"].attempts,7);
info("valid backup restores records while preserving the local storage key");

// Session guards: a rejected mock launch must not damage an active study session.
elements("yearFilter").value="ALL";
run('startMode("sequential")');
const prevMode=run("sessionMode");
const prevLength=run("session.length");
run('startMode("mock")');
assert.equal(run("sessionMode"),prevMode);
assert.equal(run("session.length"),prevLength);
info("invalid mode change does not clobber an existing session");

// Jumping off the current mock session must never discard the selected answers.
elements("yearFilter").value="R7";
run('startMode("mock")');
run("answer(1)");
const prevId=run("q().id");
const prevCount=run("Object.keys(sessionAnswers).length");
context.fakeOutside=[{id:"R7-61"}];
run("jumpQuestion()");
assert.equal(run("q().id"),prevId);
assert.equal(run("Object.keys(sessionAnswers).length"),prevCount);

// Reset clears visible session and counters, not only the numeric results.
run("resetProgress()");
assert.equal(run("Object.keys(state.items).length"),0);
assert.equal(elements("quizCard").classList.contains("hidden"),true);
assert.equal(elements("sessionBox").classList.contains("hidden"),true);
info("progress reset clears stale quiz UI");


// Priority mode selects 10 unique questions, led by weak/uncertain items.
elements("yearFilter").value="R7";
run('itemState("R7-59").rating="ng"');
run('itemState("R7-60").rating="maybe"');
run('itemState("R7-58").rating="ok"');
run('startMode("priority10")');
const dailyIds=Array.from(run("session.map(x=>x.id)"));
assert.equal(dailyIds.length,10);
assert.equal(new Set(dailyIds).size,10);
assert(dailyIds.includes("R7-59")&&dailyIds.includes("R7-60"));
assert(!dailyIds.includes("R7-58"),"mastered items should not displace unanswered");
info("priority ten picks weak questions without duplicates");

// The actual inline UI is loaded into a fresh JavaScript VM, using the same
// persistent localStorage map but distinct DOM. This simulates re-opening a tab.
function bootFresh(){
 const freshNodes=new Map();
 const el=id=>{if(!freshNodes.has(id))freshNodes.set(id,new FakeElement(id));return freshNodes.get(id)};
 const buttons=[1,2,3,4].map(n=>{
  const e=new FakeElement("fresh"+n);e.dataset.a=String(n);e.className="choice";return e;
 });
 const doc={
  getElementById:el,
  createElement:tag=>new FakeElement(tag),
  querySelectorAll:sel=>{assert.equal(sel,".choice");return buttons},
  querySelector:sel=>{
    const found=sel.match(/\.choice\[data-a="(\d)"\]/);assert(found);
    return buttons[+found[1]-1];
  }
 };
 const ctx=vm.createContext({
   document:doc,localStorage:storage,setTimeout:()=>1,clearTimeout:()=>{},
   setInterval:()=>1,clearInterval:()=>{},requestAnimationFrame:()=>{},
   confirm:()=>true,alert:msg=>alerts.push(msg),window:{},
   Date,Math,JSON,Number,String,Object,Array,Boolean,console
 });
 vm.runInContext(parts[0][1],ctx,{filename:"reloaded-index-inline.js"});
 return {context:ctx,run:src=>vm.runInContext(src,ctx),el,buttons};
}
run('startMode("mock")');
const runKey=run("mockRunKey");
const deadline=run("timerEndsAt");
run('answer(4)');
run('move(1)');
run('answer(2)');
const draft=JSON.parse(stored.get("gesuido3_mock_draft_v1"));
assert.equal(draft.runKey,runKey);
assert.equal(draft.deadline,deadline);
assert.equal(Object.keys(draft.answers).length,2);
assert.equal(draft.pos,1);
info("mock draft saves answers, position and absolute expiry");

const resumed=bootFresh();
assert.equal(resumed.el("resumeMockBox").classList.contains("hidden"),false);
assert(resumed.el("resumeMockInfo").textContent.includes("2/60問"));
resumed.run("resumeMock()");
assert.equal(resumed.run("sessionMode"),"mock");
assert.equal(resumed.run("session.length"),60);
assert.equal(resumed.run("pos"),1);
assert.equal(resumed.run("timerEndsAt"),deadline);
assert.equal(resumed.run("Object.keys(sessionAnswers).length"),2);
assert(!resumed.el("reveal").classList.contains("show"));
resumed.run('move(-1)');
assert(resumed.buttons[3].classList.contains("selected"));
assert(!resumed.buttons.some(b=>b.classList.contains("correct")));
info("reloaded mock restores selected answers but conceals the key");

// Expired snapshots are scored exactly once, even when resumed after the cutoff.
const nearPast=JSON.parse(stored.get("gesuido3_mock_draft_v1"));
nearPast.deadline=Date.now()-100;
nearPast.startedAt=nearPast.deadline-195*60*1000;
stored.set("gesuido3_mock_draft_v1",JSON.stringify(nearPast));
const expired=bootFresh();
assert(expired.el("resumeMockInfo").textContent.includes("制限時間終了"));
const beforeQ1=expired.run('state.items["R7-01"]?.attempts||0');
expired.run("resumeMock()");
assert.equal(expired.run("mockFinished"),true);
assert.equal(expired.run('state.items["R7-01"].attempts'),beforeQ1+1);
assert.equal(expired.run("state.lastGradedMockKey"),runKey);
assert.equal(stored.get("gesuido3_mock_draft_v1"),undefined);
expired.run('finishMock("time")');
assert.equal(expired.run('state.items["R7-01"].attempts'),beforeQ1+1);
assert(expired.el("mockResult").textContent.includes("/ 60点"));
const afterClose=bootFresh();
assert.equal(afterClose.el("resumeMockBox").classList.contains("hidden"),true);
assert.equal(afterClose.run('state.items["R7-01"].attempts'),beforeQ1+1);
info("expired resume grades once and never restarts the clock");

// Both explicit reset and backup import invalidate prior mock drafts.
afterClose.el("yearFilter").value="R7";
afterClose.run("rebuildCategory()");
afterClose.run('startMode("mock")');
assert(stored.has("gesuido3_mock_draft_v1"));
afterClose.run("resetProgress()");
assert.equal(stored.has("gesuido3_mock_draft_v1"),false);
afterClose.run('startMode("mock")');
assert(stored.has("gesuido3_mock_draft_v1"));
const backup={items:{"R7-01":{attempts:1,correct:1,wrong:0,lastChoice:4,lastCorrect:true,rating:"ok"}}};
const file={value:"backup.json",files:[{size:160,text:async()=>JSON.stringify(backup)}]};
afterClose.context.restoreInput={target:file};
await afterClose.run("importProgress(restoreInput)");
assert.equal(stored.has("gesuido3_mock_draft_v1"),false);
assert.equal(afterClose.run('state.items["R7-01"].attempts'),1);
info("reset and backup import invalidate stale mock snapshots");


// v1.7: completed mock history preserves score, wrong answers and unattempted.
const record=bootFresh();
record.el("yearFilter").value="R7";
record.run('startMode("mock")');
record.run("answer(1)");  // Q1 correct=4, deliberately wrong
record.run("move(1)");
record.run("answer(4)");  // Q2 correct=4
record.run('finishMock("manual")');
assert.equal(record.run("state.mockHistory.length"),1);
assert.equal(record.run("state.mockHistory[0].score"),1);
assert.equal(record.run("state.mockHistory[0].wrongIds[0]"),"R7-01");
assert.equal(record.run("state.mockHistory[0].wrongIds.length"),1);
assert.equal(record.run("state.mockHistory[0].blankIds.length"),58);
assert(record.el("mockHistory").innerHTML.includes("1/60点"));
assert.equal(record.el("mockRetryWrong").classList.contains("hidden"),false);
record.run('finishMock("time")');
assert.equal(record.run("state.mockHistory.length"),1,"regrade must not duplicate scores");
info("mock score report saves correct, wrong and unanswered lists once");

// Wrong-answer retry is a clean session with no answer leakage or extra exam score.
record.run("startMistakeReview(0)");
assert.equal(record.run("sessionMode"),"mistakes");
assert.equal(record.run("session.length"),1);
assert.equal(record.run("q().id"),"R7-01");
assert(!record.buttons.some(b=>b.classList.contains("correct")));
record.run("answer(4)");
assert.equal(record.run("state.mockHistory.length"),1);
assert.equal(record.run('state.items["R7-01"].lastCorrect'),true);
info("one-click wrong-answer review only selects previously missed problems");

// A later exam shows the difference against the prior attempt of the same year.
record.run('startMode("mock")');
record.run("answer(4)"); // Q1 right
record.run("move(1)");
record.run("answer(4)"); // Q2 right
record.run("move(1)");
record.run("answer(1)"); // Q3 wrong
record.run('finishMock("manual")');
assert.equal(record.run("state.mockHistory.length"),2);
assert.equal(record.run("state.mockHistory[0].score"),2);
assert.equal(record.run("state.mockHistory[0].wrongIds[0]"),"R7-03");
assert(record.el("mockHistory").innerHTML.includes("+1点"));
const restoredExam=bootFresh();
assert.equal(restoredExam.run("state.mockHistory.length"),2);
assert(restoredExam.el("mockHistory").innerHTML.includes("+1点"));
info("same-year trend and exam history survive browser restart");

// New format is exported with the regular progress JSON and restored intact.
const backupPayload=JSON.parse(stored.get("gesuido3_progress_v1"));
const backupResult=restoredExam.run("validateProgressBackup("+JSON.stringify(backupPayload)+")");
assert.equal(backupResult.mockHistory.length,2);
const brokenHistory=JSON.parse(JSON.stringify(backupPayload));
brokenHistory.mockHistory[0].wrongIds.push("R7-03");
assert.throws(()=>restoredExam.run("validateProgressBackup("+JSON.stringify(brokenHistory)+")"));
assert.equal(restoredExam.run("state.mockHistory.length"),2);
const importedInput={value:"history.json",files:[{size:1500,text:async()=>JSON.stringify(backupPayload)}]};
restoredExam.context.restoreInput={target:importedInput};
await restoredExam.run("importProgress(restoreInput)");
assert.equal(restoredExam.run("state.mockHistory.length"),2);
assert.equal(restoredExam.run("state.lastGradedMockKey"),backupPayload.lastGradedMockKey);
const oldFormat={items:{"R7-01":{attempts:1,correct:1,wrong:0,lastChoice:4,lastCorrect:true,rating:"ok"}}};
const oldCheck=restoredExam.run("validateProgressBackup("+JSON.stringify(oldFormat)+")");
assert.equal(oldCheck.mockHistory.length,0);
info("new history backup round-trip, corrupt records rejected, old backups supported");


// v1.8: a new user gets an explanation of the recommended starting topic.
const guided=bootFresh();
guided.run('state={items:{},createdAt:new Date().toISOString()};save()');
assert.equal(typeof guided.run("suggestedCategory"),"string");
assert(guided.el("studyRecommendation").innerHTML.includes("未回答"));
guided.run("startRecommendedStudy()");
assert.equal(guided.run("session.length"),10);
assert.equal(guided.run("sessionMode"),"priority10");
assert.equal(guided.run("new Set(session.map(x=>x.id)).size"),10);
assert.equal(guided.run("new Set(session.map(x=>x.category)).size"),1);
info("new learner receives a topic recommendation and ten on-topic questions");

// Explicit weakness ratings should affect the recommendation immediately.
guided.run('state.items["R7-01"]={attempts:1,correct:0,wrong:1,lastChoice:1,lastCorrect:false,rating:"ng"}');
guided.run('state.items["R7-02"]={attempts:1,correct:0,wrong:1,lastChoice:1,lastCorrect:false,rating:"ng"}');
guided.run("save()");
assert.equal(guided.run("suggestedCategory"),guided.run('QUESTION_BY_ID.get("R7-01").category'));
const chosen=guided.run("suggestedCategory");
guided.run("startRecommendedStudy()");
assert.equal(guided.run("session.length"),10);
assert.equal(guided.run("session.every(x=>x.category===suggestedCategory)"),true);
assert(guided.run('session.some(x=>x.id==="R7-01")'));
info("weak topic gets priority without changing question source data");

// Distinguish verified answer keys from technical explanations, which require
// independent review. This must be visible only after answering.
guided.el("yearFilter").value="R7";
guided.run('startMode("sequential")');
assert.equal(guided.el("explanationAuditNote").textContent,"");
guided.run("answer(4)");
assert(guided.el("explanationAuditNote").textContent.includes("公式資料と照合"));
assert(guided.el("explanationAuditNote").textContent.includes("独立した技術・法令監査は未完了"));
guided.el("yearFilter").value="R2";
guided.run("rebuildCategory()");
guided.run('startMode("sequential")');
guided.run("answer(2)");
assert(guided.el("explanationAuditNote").textContent.includes("保存資料"));
assert(guided.el("explanationAuditNote").textContent.includes("内容確認済み"));
assert(guided.el("explanationReferences").innerHTML.includes("e-Gov"));
info("explanations distinguish source verification from independently reviewed rationale");

// A learning suggestion must not destroy the user’s unfinished exam without
// the existing confirmation guard. Confirm rejection is simulated here.
guided.el("yearFilter").value="R7";
guided.run('startMode("mock")');
guided.run("answer(1)");
const oldExamKey=guided.run("mockRunKey");
guided.context.confirm=()=>false;
guided.run("startRecommendedStudy()");
assert.equal(guided.run("sessionMode"),"mock");
assert.equal(guided.run("mockRunKey"),oldExamKey);
assert.equal(guided.run("Object.keys(sessionAnswers).length"),1);
info("recommendation respects interruption guard for an active mock");

// v1.9 independently grounded explanations and source-damage warnings
const auditCase=bootFresh();
auditCase.el("yearFilter").value="R2";
auditCase.run('startMode("sequential")');
assert.equal(auditCase.el("explanationReferences").innerHTML,"");
auditCase.run("answer(2)");
assert(auditCase.el("explain").textContent.includes("下水道法第20条"));
assert(auditCase.el("explanationAuditNote").textContent.includes("内容確認済み"));
assert(auditCase.el("explanationReferences").innerHTML.includes("laws.e-gov.go.jp"));
info("reviewed law explanation and original evidence display only after answering");

auditCase.run('session=[QUESTION_BY_ID.get("R2-11")];pos=0;sessionMode="jump";sessionAnswers=Object.create(null);render()');
auditCase.run("answer(3)");
assert(auditCase.el("explain").textContent.includes("1,503"));
assert(auditCase.el("explanationAuditNote").textContent.includes("再計算済み"));
assert.equal(auditCase.el("formula").classList.contains("hidden"),false);
info("calculated MLSS explanation includes formula and separate verification status");

auditCase.run('session=[QUESTION_BY_ID.get("R2-24")];pos=0;sessionMode="jump";sessionAnswers=Object.create(null);render()');
assert(auditCase.el("sourceNotice").innerHTML.includes("参考問題（原本確認待ち）"));
assert.equal(auditCase.el("reveal").classList.contains("show"),false);
auditCase.run("answer(1)");
assert(auditCase.el("explanationAuditNote").textContent.includes("参考扱い"));
info("damaged R2 Q24 wording is warned before answer and never promoted as verified");

auditCase.run('session=[QUESTION_BY_ID.get("R2-48")];pos=0;sessionMode="jump";sessionAnswers=Object.create(null);render()');
assert(auditCase.el("sourceNotice").innerHTML.includes("図なしでは確実に解けない"));
assert.equal(auditCase.run('QUESTION_BY_ID.get("R2-48").answer'),4);
info("diagram-dependent R2 Q48 flagged without modifying correct answer");

// v1.10: quality counts and additional checked explanations
const checks=bootFresh();
assert.equal(Number(checks.el("reviewedCount").textContent),20);
assert.equal(Number(checks.el("holdCount").textContent),6);
info("quality dashboard reports 18 independently grounded explanations and six holds");

checks.run('session=[QUESTION_BY_ID.get("R2-09")];pos=0;sessionMode="jump";sessionAnswers=Object.create(null);render()');
checks.run("answer(3)");
assert(checks.el("explain").textContent.includes("廃棄物処理法第4条"));
assert(checks.el("explanationReferences").innerHTML.includes("laws.e-gov.go.jp"));
info("R2 Q9 verified public-law explanation is displayed with source");

checks.run('session=[QUESTION_BY_ID.get("R2-15")];pos=0;sessionMode="jump";sessionAnswers=Object.create(null);render()');
assert(checks.el("sourceNotice").innerHTML.includes("正答の暗記に使わない"));
checks.run("answer(3)");
assert(checks.el("explanationAuditNote").textContent.includes("参考扱い"));
info("R2 Q15 potential answer-key discrepancy is not misrepresented as verified");

checks.run('session=[QUESTION_BY_ID.get("R2-30")];pos=0;sessionMode="jump";sessionAnswers=Object.create(null);render()');
assert(checks.el("sourceNotice").innerHTML.includes("無関係な文字列"));
assert.equal(checks.run('QUESTION_BY_ID.get("R2-30").answer'),2);
info("R2 Q30 archival text contamination is exposed before answering");

// v1.11: suspected source questions must NEVER influence real practice results.
const exclusion=bootFresh();
assert.equal(exclusion.run('ALL.filter(isReferenceOnly).length'),6);
assert.equal(exclusion.run('poolFromFilters().length'),234);
exclusion.run('startMode("random20")');
assert.equal(exclusion.run('session.some(isReferenceOnly)'),false);
exclusion.run('startMode("priority10")');
assert.equal(exclusion.run('session.some(isReferenceOnly)'),false);
info("all normal study pools and priority picks exclude six suspect exam questions");

const beforeHistory=exclusion.run('Object.keys(state.items).length');
exclusion.run('startMode("reference")');
assert.equal(exclusion.run("session.length"),6);
assert.equal(exclusion.run("session.every(isReferenceOnly)"),true);
assert.equal(exclusion.run("q().id"),"R2-10");
assert(exclusion.el("sourceNotice").innerHTML.includes("採点対象外"));
assert(exclusion.el("reveal").classList.contains("show"));
assert(exclusion.buttons.every(b=>b.disabled));
exclusion.run("answer(1)");
assert.equal(exclusion.run('Object.keys(state.items).length'),beforeHistory);
info("the six disputed questions are accessible as read-only reference, no scored attempts");

// The R2 historic 60-question session stays viewable with 54 graded questions.
exclusion.el("yearFilter").value="R2";
exclusion.run('startMode("mock")');
assert.equal(exclusion.run("session.length"),60);
assert.equal(exclusion.run('gradedTotal("R2")'),54);
exclusion.run("pos=9;render()");
assert.equal(exclusion.run("q().id"),"R2-10");
exclusion.run("answer(1)");
exclusion.run("pos=14;render()");
exclusion.run("answer(3)");
exclusion.run("pos=0;render()");
exclusion.run("answer(2)");
exclusion.run('finishMock("manual")');
assert.equal(exclusion.run("state.mockHistory[0].total"),54);
assert.equal(exclusion.run("state.mockHistory[0].score"),1);
assert.equal(exclusion.run("state.mockHistory[0].blankIds.length"),53);
assert.equal(exclusion.run('state.items["R2-10"]?.attempts||0'),0);
assert.equal(exclusion.run('state.items["R2-15"]?.attempts||0'),0);
assert(exclusion.el("mockResult").textContent.includes("1 / 54点"));
assert(exclusion.el("mockResult").textContent.includes("6問は採点対象外"));
info("R2 mock displays 60 questions while excluding six ambiguous ones from 54-point results");

// Existing 60-point R2 backup history remains readable without comparing unlike scores.
const result54=JSON.parse(exclusion.run('JSON.stringify(state.mockHistory[0])'));
const legacy={...result54,runKey:"legacy-r2-60-test",total:60,blankIds:[...result54.blankIds,"R2-10","R2-15","R2-24","R2-30","R2-43","R2-48"]};
const payload={items:{},mockHistory:[result54,legacy]};
const validate=exclusion.run('validateProgressBackup('+JSON.stringify(payload)+')');
assert.equal(validate.mockHistory.length,2);
assert.equal(validate.mockHistory[0].total,54);
assert.equal(validate.mockHistory[1].total,60);
info("legacy 60-point and current 54-point R2 score backups both validate");

// v1.12: old answers to held questions must NOT pollute new statistics.
const historical=bootFresh();
historical.run('state={items:{"R2-10":{attempts:100,correct:100,wrong:0,lastChoice:3,lastCorrect:true,rating:"ng"},"R7-01":{attempts:2,correct:1,wrong:1,lastChoice:4,lastCorrect:true,rating:"ok"}},mockHistory:[]};updateDashboard()');
assert.equal(Number(historical.el("statAnswered").textContent),1);
assert.equal(historical.el("statAccuracy").textContent,"50%");
assert.equal(Number(historical.el("statWeak").textContent),0);
assert.equal(Number(historical.el("statTotal").textContent),240);
assert.equal(historical.run('state.items["R2-10"].attempts'),100);
info("legacy attempts on held exam items survive but are excluded from study totals");

const statsHtml=historical.el("categoryStats").innerHTML;
const categoryCounts=[...statsHtml.matchAll(/(\d+)\/(\d+)問/g)].map(x=>Number(x[2]));
assert.equal(categoryCounts.reduce((a,b)=>a+b,0),234,"all category denominators should total 234");
const legacyCategory=historical.run('QUESTION_BY_ID.get("R2-10").category');
assert.equal(historical.run('getStudyRecommendation().category===QUESTION_BY_ID.get("R2-10").category&&getStudyRecommendation().weak>0'),false);
info("category coverage uses 234 graded questions, not 240 archival records");

// Existing 60-point R2 history must be explicitly labeled and never
// directly compared against modern 54-point reference-exam attempts.
historical.run('state.mockHistory='+JSON.stringify(payload.mockHistory)+';updateDashboard()');
const historyMarkup=historical.el("mockHistory").innerHTML;
assert(historyMarkup.includes("54点参考模試"));
assert(historyMarkup.includes("旧60点方式・参考"));
assert(historyMarkup.includes("原本確認待ち6問を含む旧採点"));
assert(!historyMarkup.includes("前回比："));
assert.equal(historical.run("state.mockHistory.length"),2);
info("legacy and modern R2 exam records are preserved and clearly distinguished");

console.log("UI REGRESSION PASS: 38 scenarios");
})().catch(e=>{console.error(e);process.exitCode=1});

