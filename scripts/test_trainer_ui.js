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
const storage={getItem:k=>stored.get(k)??null,setItem:(k,v)=>stored.set(k,String(v))};
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

console.log("UI REGRESSION PASS: 10 scenarios");
})().catch(e=>{console.error(e);process.exitCode=1});

