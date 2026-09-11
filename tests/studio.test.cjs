const test=require('node:test');
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const handler=require('../api/boutique');
const {validateBrief,direct}=require('../lib/director.cjs');
process.env.LBP_PASSWORD='local-test-password-only';
process.env.LBP_SESSION_SECRET=crypto.randomBytes(32).toString('hex');
const brief={action:'review',film:'Uno',style:'Stylized animation',scene:'A young turtle hesitates before returning a lost shell.',dialogue:'',references:'',continuity:'',revision:'',duration:30,aspect:'16:9',surface:'Seedance 2.5',coverage:'Recommend for me',answers:[]};
async function call(body,headers={},method='POST'){
 const res={statusCode:200,headers:{},setHeader(k,v){this.headers[k]=v;},end(v){this.body=v;}};
 await handler({method,headers:{host:'studio.test',origin:'https://studio.test','content-type':'application/json',...headers},body},res);return res;
}
test('password gate, tamper rejection, logout, and password rotation',async()=>{
 const publicPage=await call(null,{},'GET');assert.match(publicPage.body,/id="login"/);assert.match(publicPage.headers['X-Robots-Tag'],/noindex/);
 assert.equal((await call({action:'login',password:'wrong'})).statusCode,401);
 const login=await call({action:'login',password:process.env.LBP_PASSWORD});assert.equal(login.statusCode,200);assert.match(login.headers['Set-Cookie'],/HttpOnly; SameSite=Strict/);
 const cookie=login.headers['Set-Cookie'].split(';')[0];assert.match((await call(null,{cookie},'GET')).body,/id="brief"/);
 assert.equal(handler._test.authorized({headers:{cookie:cookie+'tampered'}}),false);
 assert.match((await call({action:'logout'},{cookie})).headers['Set-Cookie'],/Max-Age=0/);
 const original=process.env.LBP_PASSWORD;process.env.LBP_PASSWORD+='changed';assert.equal(handler._test.authorized({headers:{cookie}}),false);process.env.LBP_PASSWORD=original;
});
test('reject cross-origin and unauthenticated paid requests',async()=>{
 assert.equal((await call(brief,{origin:'https://other.test'})).statusCode,403);
 assert.equal((await call(brief)).statusCode,401);
 assert.throws(()=>validateBrief({...brief,scene:''}));assert.throws(()=>validateBrief({...brief,duration:999}));
 assert.equal(validateBrief(brief).duration,30);
});
test('rate limiter rejects excess requests',()=>{assert.equal(handler._test.allowed('test-limit',1,1000),true);assert.equal(handler._test.allowed('test-limit',1,1000),false);});
test('Responses request preserves answers and uses structured server-side output',async()=>{
 const output={feedback:'Clarify the emotional change.',questions:[{id:'emotion',title:'What changes?',why:'Guide the performance.',options:['Fear to trust','Pride to remorse'],recommendedIndex:0}],settings:'',referenceMap:'',clips:[],risks:[]};
 const result=await direct(brief,async(url,options)=>{assert.equal(url,'https://api.openai.com/v1/responses');const b=JSON.parse(options.body);assert.equal(b.store,false);assert.equal(b.reasoning.effort,'low');assert.equal(b.max_output_tokens,3000);assert.ok(b.instructions.length<10000);assert.equal(b.text.format.strict,true);assert.deepEqual(JSON.parse(b.input),brief);return{ok:true,json:async()=>({output:[{content:[{type:'output_text',text:JSON.stringify(output)}]}]})};});assert.equal(result.questions.length,1);
});
test('handles quota errors and incomplete model responses without fake prompts',async()=>{
 await assert.rejects(direct(brief,async()=>({ok:false,status:429})),/billing/);
 await assert.rejects(direct(brief,async()=>({ok:true,json:async()=>({status:'incomplete'})})),/response space/);
 await assert.rejects(direct(brief,async()=>({ok:true,json:async()=>({output:[]})})),/incomplete response/);
});
