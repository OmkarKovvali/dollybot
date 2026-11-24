// Transport only. The user's existing Kino agent makes the directing decisions.
export class SimulatorBridge {
  constructor({api,onStatus,onJob,onDisconnect}){
    this.api=api;this.onStatus=onStatus;this.onJob=onJob;this.onDisconnect=onDisconnect;
    this.clientId=crypto.randomUUID();this.token=null;this.base='';this.pending=null;this.activeJob=null;
    this.seen=new Set();this.stopEpoch=null;this.running=false;this.busy=false;this.instance=null;this.generation=0;this.interruptEpoch=0;
  }
  async request(route,data){
    const headers={};if(this.token)headers.Authorization=`Bearer ${this.token}`;
    if(data!==undefined)headers['Content-Type']='application/json';
    const response=await fetch(`${this.base}${route}`,{method:data===undefined?'GET':'POST',headers,body:data===undefined?undefined:JSON.stringify(data),signal:AbortSignal.timeout(2500),cache:'no-store'});
    const result=await response.json();if(!response.ok)throw new Error(result.error||`Bridge error ${response.status}`);return result;
  }
  async connect(base){
    if(this.running)return;
    const generation=++this.generation;
    this.base=base;this.onStatus('connecting','Connecting to the local simulator…');
    try{
      const session=await this.request('/api/bridge/session');
      if(generation!==this.generation)return;
      if(!session.simulation_only)throw new Error('This endpoint is not a simulator');
      this.token=session.token;this.instance=session.instance;this.stopEpoch=null;this.running=true;
      await this.poll();if(this.running)this.timer=setInterval(()=>this.poll(),300);
    }catch(e){this.running=false;this.token=null;this.onStatus('offline','Local bridge unavailable. Open the local simulator to connect Kino.');}
  }
  async disconnect(){
    this.generation++;
    clearInterval(this.timer);const wasRunning=this.running;this.running=false;
    this.api.stop();this.onDisconnect();
    if(wasRunning){try{await this.request('/api/bridge/viewer',{client_id:this.clientId,release:true});}catch{}}
    this.token=null;this.activeJob=null;this.pending=null;this.onStatus('offline','Kino bridge disconnected');
  }
  interrupt(reason='Stopped in the simulator'){
    this.interruptEpoch++;
    if(this.activeJob){this.pending={id:this.activeJob.id,status:'cancelled',reason};this.activeJob=null;}
  }
  async poll(){
    if(!this.running||this.busy)return;this.busy=true;
    const generation=this.generation,interruptEpoch=this.interruptEpoch;
    try{
      const state=this.api.getState();
      if(this.activeJob&&!this.pending){
        if(state.mode==='complete')this.pending={id:this.activeJob.id,status:'completed'};
        else if(state.mode!=='shot')this.pending={id:this.activeJob.id,status:'cancelled',reason:document.hidden?'Simulator tab was hidden':'Manual control or preview settings interrupted the shot'};
      }
      const sent=this.pending;
      const result=await this.request('/api/bridge/viewer',{client_id:this.clientId,ready:state.modelReady&&!document.hidden,telemetry:state,update:sent});
      if(!this.running||generation!==this.generation)return;
      if(this.pending===sent)this.pending=null;
      if(sent&&['completed','cancelled','failed'].includes(sent.status))this.activeJob=null;
      if(result.instance!==this.instance)throw new Error('Bridge restarted; reconnect to begin a new session');
      if(result.role==='observer'){this.onStatus('observer','Another simulator tab is connected. Disconnect it to use this one.');return;}
      this.onStatus('connected',state.modelReady?'Ask for a shot in Kino. Keep this preview visible.':'Loading the robot model…');
      if(this.stopEpoch!==null&&result.stop_epoch!==this.stopEpoch){this.api.stop();this.interrupt('Stop requested from Kino');}
      this.stopEpoch=result.stop_epoch;
      if(result.job?.status==='stopping'){this.api.stop();this.pending={id:result.job.id,status:'cancelled',reason:'Stop requested from Kino'};this.activeJob=null;}
      else if(result.job&&!this.seen.has(result.job.id)&&state.modelReady&&!document.hidden){
        const job=result.job;this.seen.add(job.id);
        if(interruptEpoch!==this.interruptEpoch||this.api.getState().mode==='manual'){this.pending={id:job.id,status:'cancelled',reason:'Manual input interrupted delivery'};this.onJob(job);return;}
        try{if(job.motion)this.api.executeMotion(job.motion,job.start_pose);else this.api.executeShot(job.shot);this.activeJob=job;this.pending={id:job.id,status:'running'};this.onJob(job);}
        catch(e){this.pending={id:job.id,status:'failed',reason:e.message};}
      }
      else if(result.job&&!this.activeJob&&!this.pending&&this.seen.has(result.job.id))this.pending={id:result.job.id,status:'cancelled',reason:'Interrupted before reconnection'};
      if(this.activeJob&&!result.job){this.api.stop();this.activeJob=null;}
      if(result.last_job)this.onJob(result.last_job);
    }catch(e){
      if(generation!==this.generation)return;
      clearInterval(this.timer);this.running=false;this.api.stop();this.onDisconnect();this.activeJob=null;this.token=null;
      this.onStatus('offline','Connection lost · Simulation stopped. Reconnect to continue.');
    }finally{this.busy=false;}
  }
}
