const crypto=require('node:crypto');
const page=require('../lib/page.cjs');
const {validateBrief,direct}=require('../lib/director.cjs');
const attempts=new Map();
const hash=value=>crypto.createHash('sha256').update(value).digest();
const equal=(a,b)=>crypto.timingSafeEqual(hash(a),hash(b));
function secret(){return process.env.LBP_SESSION_SECRET||'';}
function ready(){return (process.env.LBP_PASSWORD||'').length>=16&&secret().length>=32;}
function sign(payload){return crypto.createHmac('sha256',secret()+process.env.LBP_PASSWORD).update(payload).digest('base64url');}
function token(){const p=Buffer.from(JSON.stringify({exp:Date.now()+8*3600000,id:crypto.randomUUID()})).toString('base64url');return p+'.'+sign(p);}
function authorized(req){if(!ready())return false;try{const t=(req.headers.cookie||'').split(';').map(x=>x.trim()).find(x=>x.startsWith('lbp_session='))?.slice(12)||'';const [p,s]=t.split('.');return !!p&&!!s&&equal(sign(p),s)&&JSON.parse(Buffer.from(p,'base64url')).exp>Date.now();}catch{return false;}}
function allowed(key,limit,period){const now=Date.now();if(attempts.size>10000){for(const [k,v]of attempts)if(v.reset<now)attempts.delete(k);if(attempts.size>10000)return false;}let v=attempts.get(key);if(!v||v.reset<now){v={count:0,reset:now+period};attempts.set(key,v);}return ++v.count<=limit;}
function json(res,status,data){res.statusCode=status;res.setHeader('Content-Type','application/json');res.end(JSON.stringify(data));}
module.exports=async function handler(req,res){
  res.setHeader('Cache-Control','no-store');res.setHeader('X-Robots-Tag','noindex, nofollow, noarchive');res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','same-origin');res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'");
  if(req.method==='GET'){res.setHeader('Content-Type','text/html; charset=utf-8');res.end(authorized(req)?page.studio():page.login());return;}
  if(req.method!=='POST'){res.setHeader('Allow','GET, POST');return json(res,405,{error:'Method not allowed.'});}
  let origin;try{origin=new URL(req.headers.origin).host;}catch{return json(res,403,{error:'Please open the studio directly.'});}
  if(origin!==req.headers.host)return json(res,403,{error:'Request origin did not match the studio.'});
  if(!String(req.headers['content-type']||'').startsWith('application/json'))return json(res,415,{error:'JSON required.'});
  if(!ready())return json(res,503,{error:'Studio setup is pending. Add LBP_PASSWORD (16+ characters) and LBP_SESSION_SECRET (32+ characters) to Vercel, then redeploy.'});
  let body;try{body=typeof req.body==='string'?JSON.parse(req.body):req.body;if(!body||Buffer.byteLength(JSON.stringify(body))>40000)throw Error();}catch{return json(res,400,{error:'The request is too large or invalid.'});}
  const ip=String(req.headers['x-forwarded-for']||req.socket?.remoteAddress||'unknown').split(',')[0];
  if(body.action==='login'){
    if(!allowed('login:'+ip,8,15*60000))return json(res,429,{error:'Too many sign-in attempts. Try again in 15 minutes.'});
    if(typeof body.password!=='string'||!equal(body.password,process.env.LBP_PASSWORD))return json(res,401,{error:'That password did not match.'});
    res.setHeader('Set-Cookie','lbp_session='+token()+'; Path=/; HttpOnly; SameSite=Strict; Max-Age=28800'+(process.env.VERCEL?'; Secure':''));return json(res,200,{ok:true});
  }
  if(!authorized(req))return json(res,401,{error:'Your session expired. Sign in again; your draft stays in this tab.'});
  if(body.action==='logout'){res.setHeader('Set-Cookie','lbp_session=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0'+(process.env.VERCEL?'; Secure':''));return json(res,200,{ok:true});}
  if(!process.env.OPENAI_API_KEY)return json(res,503,{error:'GPT-6 is not connected yet. Add OPENAI_API_KEY to this Vercel project and redeploy. Your scene has not been sent to OpenAI.'});
  let brief;try{brief=validateBrief(body);}catch(e){return json(res,400,{error:e.message});}
  if(!allowed('generation:'+ip,12,60000))return json(res,429,{error:'Please wait a minute before asking for more direction.'});
  try{return json(res,200,await direct(brief));}catch(e){return json(res,502,{error:e.name==='TimeoutError'?'The director took too long. Your draft is safe in this tab; try again.':e.message});}
};
module.exports._test={authorized,token,ready,allowed};
