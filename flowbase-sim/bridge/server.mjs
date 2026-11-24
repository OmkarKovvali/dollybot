import http from 'node:http';
import {randomBytes,timingSafeEqual} from 'node:crypto';
import {readFile,writeFile,mkdir,stat,unlink} from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {BridgeState,BridgeError} from './state.mjs';

export async function startBridge({port=8766,root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),runtime=true}={}){
  const state=new BridgeState(),token=randomBytes(32).toString('hex'),dist=path.join(root,'dist');
  const origins=new Set(['https://kino-flowbase-sim.vishnu670472.chatgpt.site']);
  const localHosts=new Set();
  const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript','.mjs':'text/javascript','.css':'text/css','.json':'application/json','.stl':'model/stl','.urdf':'application/xml','.txt':'text/plain','.zip':'application/zip','.jpg':'image/jpeg','.png':'image/png'};
  const send=(res,status,data)=>{res.writeHead(status,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(data));};
  const body=async req=>{let data='';for await(const chunk of req){data+=chunk;if(data.length>131072)throw new BridgeError(413,'Request too large (128 KB maximum)');}try{return JSON.parse(data);}catch{throw new BridgeError(400,'Expected JSON');}};
  const server=http.createServer(async(req,res)=>{
    res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','no-referrer');
    try{
      if(!localHosts.has(req.headers.host))throw new BridgeError(403,'Invalid loopback host');
      const origin=req.headers.origin;
      if(origin&&!origins.has(origin))throw new BridgeError(403,'Origin not allowed');
      if(origin){res.setHeader('Access-Control-Allow-Origin',origin);res.setHeader('Vary','Origin');res.setHeader('Access-Control-Allow-Private-Network','true');}
      if(req.method==='OPTIONS'){res.writeHead(204,{'Access-Control-Allow-Methods':'GET, POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type, Authorization','Access-Control-Max-Age':'600'});res.end();return;}
      const url=new URL(req.url,'http://localhost');
      if(url.pathname==='/api/bridge/health'&&req.method==='GET'){send(res,200,{service:'kino-flowbase-simulator',simulation_only:true,instance:state.instance});return;}
      if(url.pathname==='/api/bridge/session'&&req.method==='GET'){
        if(req.headers['sec-fetch-site']==='cross-site'&&!origin)throw new BridgeError(403,'Origin required');
        send(res,200,{token,instance:state.instance,simulation_only:true});return;
      }
      if(url.pathname.startsWith('/api/')){
        const provided=Buffer.from(req.headers.authorization||''),expected=Buffer.from(`Bearer ${token}`);
        if(provided.length!==expected.length||!timingSafeEqual(provided,expected))throw new BridgeError(401,'Bridge authentication required; reconnect the simulator');
        if(req.method==='POST'&&!req.headers['content-type']?.startsWith('application/json'))throw new BridgeError(415,'Use application/json');
        if(url.pathname==='/api/bridge/viewer'&&req.method==='POST'){send(res,200,state.viewerTick(await body(req)));return;}
        if(url.pathname==='/api/shots'&&req.method==='POST'){send(res,202,state.publicJob(state.submit(await body(req))));return;}
        if(url.pathname==='/api/motions'&&req.method==='POST'){send(res,202,state.publicJob(state.submitMotion(await body(req))));return;}
        if(url.pathname==='/api/capabilities'&&req.method==='GET'){send(res,200,{simulation_only:true,version:2,degrees_of_freedom:['x','y','yaw'],motions:['drive','move','pose','path','sequence'],frames:['body','world'],units:{position:'meters',yaw:'radians',time:'seconds',velocity:'meters/second',omega:'radians/second'},motion_limits:null,clearance_enforced:false,max_request_bytes:131072,max_commands_or_waypoints:1024,shots:['orbit','dolly','slide']});return;}
        if(url.pathname==='/api/stop'&&req.method==='POST'){send(res,200,state.stop());return;}
        if(url.pathname==='/api/state'&&req.method==='GET'){send(res,200,state.status());return;}
        if(url.pathname.startsWith('/api/jobs/')&&req.method==='GET'){send(res,200,state.status(decodeURIComponent(url.pathname.slice(10))));return;}
        throw new BridgeError(404,'Unknown API route');
      }
      if(!['GET','HEAD'].includes(req.method))throw new BridgeError(405,'Method not allowed');
      let pathname;try{pathname=decodeURIComponent(url.pathname);}catch{throw new BridgeError(400,'Invalid path');}
      const filename=path.resolve(dist,`.${pathname==='/'?'/index.html':pathname}`);
      if(!filename.startsWith(dist+path.sep))throw new BridgeError(403,'Invalid path');
      let info;try{info=await stat(filename);}catch{throw new BridgeError(404,'Not found');}if(!info.isFile())throw new BridgeError(404,'Not found');
      res.writeHead(200,{'Content-Type':mime[path.extname(filename)]||'application/octet-stream','Content-Length':info.size,'Cache-Control':'no-cache'});
      if(req.method==='HEAD')res.end();else createReadStream(filename).pipe(res);
    }catch(e){if(!res.headersSent)send(res,e.status||500,{error:e.status?e.message:'Bridge request failed',simulation_only:true});else res.end();}
  });
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(port,'127.0.0.1',resolve);});
  const actual=server.address().port;
  for(const host of [`127.0.0.1:${actual}`,`localhost:${actual}`]){localHosts.add(host);origins.add(`http://${host}`);}
  const configPath=path.join(root,'.runtime','bridge.json');
  if(runtime){await mkdir(path.dirname(configPath),{recursive:true,mode:0o700});await writeFile(configPath,JSON.stringify({url:`http://127.0.0.1:${actual}`,token,pid:process.pid,instance:state.instance}),{mode:0o600});}
  const timer=setInterval(()=>state.sweep(),500);timer.unref();
  const close=async()=>{clearInterval(timer);state.stop();await new Promise(resolve=>server.close(resolve));if(runtime){try{const data=JSON.parse(await readFile(configPath,'utf8'));if(data.instance===state.instance)await unlink(configPath);}catch{}}};
  return {server,state,url:`http://127.0.0.1:${actual}`,token,close};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  try{
    const bridge=await startBridge();console.log(`Kino simulator bridge: ${bridge.url}\nSimulation only. Keep this process running while directing shots in Kino.`);
    let stopping=false;for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>{if(!stopping){stopping=true;bridge.close().then(()=>process.exit(0));}});
  }catch(e){console.error(e.code==='EADDRINUSE'?'Port 8766 is already in use. Keep the existing bridge, or stop it before restarting.':e.message);process.exitCode=1;}
}
