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

console.log("UI REGRESSION PASS: 4 scenarios");
