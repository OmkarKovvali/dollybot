// Caster-rate equations adapted from I2RT's MIT-licensed SimBase example.
// This is an ideal kinematic preview, not a contact/dynamics simulation.
export const MODEL_COMMIT = '8c1b3ab6b6f31ae11e8b5f1e46c037d154199938';
export const LIMITS = Object.freeze({linear: 0.5, angular: 0.8, acceleration: 0.5, angularAcceleration: 1.2});
export const CASTERS = Object.freeze([[-0.2, 0.2], [0.2, 0.2], [0.2, -0.2], [-0.2, -0.2]]);
export const WHEEL_RADIUS = 0.05;
export const TRAIL = -0.02;
export const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
export const wrap = a => Math.atan2(Math.sin(a), Math.cos(a));
export const smooth = t => t * t * t * (10 + t * (-15 + 6 * t));
export const approach = (a, b, amount) => a + clamp(b - a, -amount, amount);

export function integratePose(p, v, dt) {
  const [vx, vy, w] = v, a = w * dt;
  const sinc = Math.abs(a) < 1e-7 ? 1 - a * a / 6 : Math.sin(a) / a;
  const cosc = Math.abs(a) < 1e-7 ? a / 2 : (1 - Math.cos(a)) / a;
  const dx = dt * (sinc * vx - cosc * vy), dy = dt * (cosc * vx + sinc * vy);
  return {x: p.x + Math.cos(p.yaw) * dx - Math.sin(p.yaw) * dy,
    y: p.y + Math.sin(p.yaw) * dx + Math.cos(p.yaw) * dy, yaw: p.yaw + a};
}

export function advanceCasters(steer, drive, velocity, dt) {
  const steps = Math.max(1, Math.ceil(dt / 0.005)), h = dt / steps;
  const [vx, vy, w] = velocity;
  for (let n = 0; n < steps; n++) {
    for (let i = 0; i < 4; i++) {
      const s = Math.sin(steer[i]), c = Math.cos(steer[i]), [hx, hy] = CASTERS[i];
      steer[i] += h * ((s * vx - c * vy - (hx * c + hy * s) * w) / TRAIL - w);
      drive[i] += h * (c * vx + s * vy + (hx * s - hy * c) * w) / WHEEL_RADIUS;
    }
  }
}

export function isClear(p) {
  // Conservative footprint radius 0.40 m, subject radius 0.30 m, extra clearance 0.10 m.
  return Number.isFinite(p.x + p.y + p.yaw) && Math.hypot(p.x, p.y) >= 0.8 && Math.abs(p.x) <= 4.5 && Math.abs(p.y) <= 4.5;
}

export function makePlan(input) {
  const p = {kind: 'orbit', radius: 2.5, sweepDeg: 90, distance: 1.2, duration: 16, faceSubject: true, ...input};
  if (!['orbit', 'dolly', 'slide'].includes(p.kind)) throw new Error('Unknown shot type');
  for (const key of ['radius', 'sweepDeg', 'distance', 'duration']) {
    if (!Number.isFinite(p[key])) throw new Error(`Invalid ${key}`);
  }
  if (p.unconstrained !== undefined && typeof p.unconstrained !== 'boolean') throw new Error('unconstrained must be boolean');
  if (p.duration <= 0 || p.radius < 0) throw new Error('Use a positive duration and nonnegative radius');
  if (!p.unconstrained && (p.radius < 0.8 || p.radius > 4 || p.duration < 1 || p.duration > 120 || p.distance < 0 || p.distance > 6 || Math.abs(p.sweepDeg) > 360)) throw new Error('Shot parameters out of range');
  const sample = seconds => {
    const u = smooth(clamp(seconds / p.duration, 0, 1));
    let x, y, yaw;
    if (p.kind === 'orbit') {
      const angle = Math.PI + p.sweepDeg * Math.PI / 180 * u;
      x = p.radius * Math.cos(angle); y = p.radius * Math.sin(angle);
      yaw = p.faceSubject ? angle - Math.PI : 0;
    } else if (p.kind === 'dolly') {
      x = -p.radius + p.distance * u; y = 0; yaw = 0;
    } else {
      x = -p.radius; y = p.distance * (u - 0.5);
      yaw = p.faceSubject ? Math.atan2(-y, -x) : 0;
    }
    return {x, y, yaw};
  };
  const velocityAt = seconds => {
    const a = Math.max(0, seconds - 0.001), b = Math.min(p.duration, seconds + 0.001);
    const pa = sample(a), pb = sample(b), pc = sample(seconds), h = b - a;
    const wx = (pb.x - pa.x) / h, wy = (pb.y - pa.y) / h;
    return [Math.cos(pc.yaw) * wx + Math.sin(pc.yaw) * wy, -Math.sin(pc.yaw) * wx + Math.cos(pc.yaw) * wy, (pb.yaw - pa.yaw) / h];
  };
  let maxSpeed = 0, maxAngular = 0, maxAcceleration = 0, maxAngularAcceleration = 0, length = 0, clear = true;
  let prev = sample(0), prevWorldV = [0, 0, 0];
  const step = p.duration / 600;
  for (let i = 0; i <= 600; i++) {
    const pos = sample(i * step), v = velocityAt(i * step);
    if (![pos.x,pos.y,pos.yaw,...v].every(Number.isFinite)) throw new Error('Shot exceeds numeric precision');
    const worldV = [Math.cos(pos.yaw) * v[0] - Math.sin(pos.yaw) * v[1], Math.sin(pos.yaw) * v[0] + Math.cos(pos.yaw) * v[1], v[2]];
    if (i) {
      maxAcceleration = Math.max(maxAcceleration, Math.hypot(worldV[0] - prevWorldV[0], worldV[1] - prevWorldV[1]) / step);
      maxAngularAcceleration = Math.max(maxAngularAcceleration, Math.abs(worldV[2] - prevWorldV[2]) / step);
    }
    length += Math.hypot(pos.x - prev.x, pos.y - prev.y);
    maxSpeed = Math.max(maxSpeed, Math.hypot(v[0], v[1])); maxAngular = Math.max(maxAngular, Math.abs(v[2]));
    clear &&= isClear(pos); prev = pos; prevWorldV = worldV;
  }
  const factor = Math.max(maxSpeed / LIMITS.linear, maxAngular / LIMITS.angular, Math.sqrt(maxAcceleration / LIMITS.acceleration), Math.sqrt(maxAngularAcceleration / LIMITS.angularAcceleration));
  const minDuration = Math.ceil(p.duration * factor);
  const reason = p.unconstrained ? '' : !clear ? 'Path enters the subject clearance zone or leaves the stage.' : factor > 1.005 ? `Use at least ${minDuration} seconds to stay within preview motion limits.` : '';
  return {params: p, sample, velocityAt, length, maxSpeed, maxAngular, maxAcceleration, minDuration, valid: !reason, reason};
}

export class Simulator {
  constructor() { this.steer = [0,0,0,0]; this.drive = [0,0,0,0]; this.unconstrained=false; this.reset(); }
  reset(pose = {x:-2.5,y:0,yaw:0}) { this.pose = {...pose}; this.velocity = [0,0,0]; this.target = [0,0,0]; this.elapsed = 0; this.mode = 'idle'; this.plan = null; this.blocked = false; this.steer.fill(0); this.drive.fill(0); }
  stop() { this.velocity = [0,0,0]; this.target = [0,0,0]; this.mode = 'idle'; }
  manual(command) {
    if (command.length !== 3 || !command.every(Number.isFinite)) throw new Error('Invalid velocity');
    const scale = this.unconstrained ? 1 : Math.max(1, Math.hypot(command[0],command[1]) / LIMITS.linear);
    this.target = [command[0]/scale,command[1]/scale,this.unconstrained?command[2]:clamp(command[2],-LIMITS.angular,LIMITS.angular)];
    this.mode = 'manual'; this.plan = null; this.blocked = false;
  }
  play(plan) {
    if (!plan.valid) throw new Error(plan.reason);
    this.reset(plan.sample(0)); this.plan = plan; this.mode = 'shot';
  }
  seek(plan, t) { this.stop(); this.plan = plan; this.elapsed = clamp(t,0,plan.params.duration); this.pose = plan.sample(this.elapsed); this.mode = 'paused'; }
  tick(dt) {
    if (!Number.isFinite(dt) || dt <= 0) return;
    dt = Math.min(dt, 0.1);
    if (this.mode === 'shot') {
      this.elapsed = Math.min(this.plan.params.duration, this.elapsed + dt);
      this.velocity = this.plan.velocityAt(this.elapsed);
      this.pose = this.plan.sample(this.elapsed);
      advanceCasters(this.steer,this.drive,this.velocity,dt);
      if (this.elapsed >= this.plan.params.duration) { this.stop(); this.mode = 'complete'; }
    } else if (this.mode === 'manual') {
      const dx = this.target[0]-this.velocity[0], dy = this.target[1]-this.velocity[1], mag=Math.hypot(dx,dy);
      const scale = Math.min(1, LIMITS.acceleration * dt / (mag || 1));
      this.velocity[0] += dx * scale; this.velocity[1] += dy * scale;
      this.velocity[2] = approach(this.velocity[2],this.target[2],LIMITS.angularAcceleration*dt);
      if(this.unconstrained)this.velocity=[...this.target];
      const next = integratePose(this.pose,this.velocity,dt);
      if (!this.unconstrained && !isClear(next)) { this.stop(); this.blocked=true; return; }
      this.pose = next; advanceCasters(this.steer,this.drive,this.velocity,dt);
    }
  }
}

export function exportPlan(plan) {
  const samples=[];
  const step=Math.max(.1,plan.params.duration/5000);
  for(let i=0;i<5000&&i*step<plan.params.duration;i++){const t=i*step;samples.push({t_s:+t.toFixed(3),...plan.sample(t),body_velocity:plan.velocityAt(t)});}
  samples.push({t_s:plan.params.duration,...plan.sample(plan.params.duration),body_velocity:[0,0,0]});
  return {schema_version:1,kind:'kino.shot_preview',simulation_only:true,model_commit:MODEL_COMMIT,frame:'world',units:{position:'m',yaw:'rad',time:'s'},subject:{x:0,y:0},motion:plan.params,validation:{valid:plan.valid,reason:plan.reason,constraints_enforced:!plan.params.unconstrained,limits:plan.params.unconstrained?null:LIMITS},samples};
}
