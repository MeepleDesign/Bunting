// In-browser stand-in for @supabase/supabase-js, used only by the smoke tests.
// It covers the calls the runtime and pages make, keeps data in localStorage so two tabs
// share it, and applies the same access rules as supabase/migrations/0001_bunting_init.sql.
type Row = Record<string, any>;
type Tables = Record<string, Row[]>;
const KEY = 'fake.supabase';
const load = (): Tables => { try { return JSON.parse(localStorage.getItem(KEY) || '') } catch { return { bunting_docs: [], bunting_members: [], bunting_profiles: [] } } };
const save = (t: Tables) => { localStorage.setItem(KEY, JSON.stringify(t)); };
const session = () => { try { return JSON.parse(sessionStorage.getItem('fake.session') || 'null') } catch { return null } };
const role = () => { const s = session(); if (!s) return null; return (load().bunting_members.find(m => m.email === s.user.email) || {}).role || null; };
const uid = () => session()?.user.id;

function allowedRead(table: string, r: Row) {
  if (table === 'bunting_docs') return r.coll !== 'feedback' || role() === 'owner' || r.data?.uid === uid();
  if (table === 'bunting_members') return r.email === session()?.user.email || role() === 'owner';
  return true;
}
function allowedWrite(table: string, r: Row, op: string) {
  if (!session()) return false;
  if (table === 'bunting_docs') {
    if (r.coll === 'admin') return role() === 'owner';
    if (r.coll === 'feedback') return op === 'delete' ? role() === 'owner' : (r.data?.uid === uid() || role() === 'owner');
    return role() !== null;
  }
  if (table === 'bunting_members') return role() === 'owner';
  if (table === 'bunting_profiles') return r.id === uid();
  return false;
}
const denied = { error: { code: '42501', message: 'new row violates row-level security policy' }, data: null };
const pk: Record<string, string> = { bunting_docs: 'path', bunting_members: 'email', bunting_profiles: 'id' };
const listeners: { coll: string; cb: (p: any) => void }[] = [];
function emit(eventType: string, row: Row, old?: Row) {
  const ev = { eventType, new: eventType === 'DELETE' ? {} : row, old: eventType === 'DELETE' ? row : (old || {}) };
  localStorage.setItem('fake.event', JSON.stringify({ ev, n: Math.random() }));
  deliver(ev);
}
function deliver(ev: any) { const r = ev.eventType === 'DELETE' ? ev.old : ev.new; listeners.forEach(l => { if (r.coll === l.coll && allowedRead('bunting_docs', r)) setTimeout(() => l.cb(ev), 5); }); }
window.addEventListener('storage', e => { if (e.key === 'fake.event' && e.newValue) deliver(JSON.parse(e.newValue).ev); });

class Query {
  private filters: ((r: Row) => boolean)[] = [];
  private op = 'select'; private payload: Row | null = null; private one = false; private rng: [number, number] | null = null; private ord: string | null = null;
  constructor(private table: string) {}
  select() { return this; }
  eq(k: string, v: any) { this.filters.push(r => r[k] === v); return this; }
  in(k: string, v: any[]) { this.filters.push(r => v.includes(r[k])); return this; }
  order(k: string) { this.ord = k; return this; }
  range(a: number, b: number) { this.rng = [a, b]; return this; }
  maybeSingle() { this.one = true; return this; }
  upsert(p: Row) { this.op = 'upsert'; this.payload = p; return this; }
  delete() { this.op = 'delete'; return this; }
  then(res: (v: any) => void, rej?: (e: any) => void) { return Promise.resolve().then(() => this.run()).then(res, rej); }
  private run(): any {
    const t = load(); const rows = t[this.table] || (t[this.table] = []);
    if (this.op === 'upsert') {
      const p = Object.assign({}, this.payload);
      if (this.table === 'bunting_docs' && JSON.stringify(p.data).length > 262144) return { error: { code: '23514', message: 'violates check constraint "bunting_docs_size"' } };
      if (!allowedWrite(this.table, p, 'upsert')) return denied;
      const i = rows.findIndex(r => r[pk[this.table]] === p[pk[this.table]]);
      const old = i >= 0 ? rows[i] : undefined;
      if (old && !allowedWrite(this.table, old, 'upsert')) return denied;
      if (i >= 0) rows[i] = Object.assign({}, rows[i], p); else rows.push(p);
      save(t); if (this.table === 'bunting_docs') emit(i >= 0 ? 'UPDATE' : 'INSERT', p, old);
      return { error: null, data: null };
    }
    let out = rows.filter(r => allowedRead(this.table, r) && this.filters.every(f => f(r)));
    if (this.op === 'delete') {
      if (out.some(r => !allowedWrite(this.table, r, 'delete'))) return denied;
      t[this.table] = rows.filter(r => !out.includes(r)); save(t);
      if (this.table === 'bunting_docs') out.forEach(r => emit('DELETE', r));
      return { error: null, data: null };
    }
    if (this.ord) { const k = this.ord; out = out.slice().sort((a, b) => String(a[k]).localeCompare(String(b[k]))); }
    if (this.rng) out = out.slice(this.rng[0], this.rng[1] + 1);
    out = JSON.parse(JSON.stringify(out));
    return { error: null, data: this.one ? (out[0] || null) : out };
  }
}

export function createClient() {
  return {
    from: (t: string) => new Query(t),
    auth: {
      getSession: async () => ({ data: { session: session() } }),
      onAuthStateChange: () => ({ data: { subscription: { unsubscribe() {} } } }),
      signOut: async () => { sessionStorage.removeItem('fake.session'); return { error: null }; },
      signInWithOtp: async () => ({ error: null }),
    },
    channel() {
      const ch: any = { coll: '' };
      ch.on = (_t: string, f: any, cb: any) => { ch.coll = String(f.filter).replace('coll=eq.', ''); ch.cb = cb; return ch; };
      ch.subscribe = (s: any) => { ch.l = { coll: ch.coll, cb: ch.cb }; listeners.push(ch.l); setTimeout(() => s && s('SUBSCRIBED'), 5); return ch; };
      return ch;
    },
    removeChannel(ch: any) { const i = listeners.indexOf(ch.l); if (i >= 0) listeners.splice(i, 1); },
  };
}
