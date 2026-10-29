// Bunting demo runtime.
// The prototype was built against a small runtime API (window.claude.use('db' | 'user' | 'downloads')).
// This file provides the same API backed by Supabase, so the prototype runs unchanged on its own site.
import type { RealtimeChannel, Session } from '@supabase/supabase-js';
import { supabase } from '../../lib/supabase';

type Data = Record<string, unknown>;
type Snap = { id: string; exists: boolean; data: () => Data | undefined; metadata: { fromCache: boolean; hasPendingWrites: boolean } };
type Change = { type: 'added' | 'modified' | 'removed'; doc: Snap; oldIndex: number; newIndex: number };
type QuerySnap = { docs: Snap[]; size: number; empty: boolean; docChanges: () => Change[]; metadata: Data };
type RuntimeError = { code: string; message: string };

const MAX_BYTES = 256 * 1024;
const sb = supabase();
const clone = <T,>(o: T): T => JSON.parse(JSON.stringify(o));
const fail = (code: string, message: string): RuntimeError => ({ code, message });

// ---------- session and role
let session: Session | null = null;
let role: 'owner' | 'contributor' | null = null;
const ready: Promise<void> = (async () => {
  try {
    const { data } = await sb.auth.getSession();
    session = data.session;
    // PKCE magic links land on /?code=...; tidy the address bar once the session is in.
    const u = new URL(location.href);
    if (u.searchParams.has('code')) { u.searchParams.delete('code'); history.replaceState(null, '', u.pathname + u.search + u.hash); }
    if (session) {
      const { data: m } = await sb.from('bunting_members').select('role').eq('email', (session.user.email || '').toLowerCase()).maybeSingle();
      role = (m?.role as typeof role) ?? null;
    }
  } catch { /* stay signed out */ }
})();
sb.auth.onAuthStateChange((evt, s) => {
  // A sign-in or sign-out in another tab changes who the page is acting as, so reload.
  if ((evt === 'SIGNED_IN' && !session && s) || (evt === 'SIGNED_OUT' && session)) location.reload();
  session = s;
});

function displayName(s: Session): string {
  const meta = (s.user.user_metadata || {}) as Data;
  return String(meta.full_name || meta.name || (s.user.email || '').split('@')[0] || '');
}

// ---------- user
const NAMES: Record<string, string> = {};
const user = {
  async me() {
    await ready;
    if (!session) return { id: null, name: '', email: null, avatarUrl: '', color: '#888', isOwner: false, canEdit: false };
    const id = session.user.id;
    let name = NAMES[id];
    if (!name) {
      const { data } = await sb.from('bunting_profiles').select('name').eq('id', id).maybeSingle();
      name = data?.name || displayName(session);
      NAMES[id] = name;
      if (!data) sb.from('bunting_profiles').upsert({ id, name }).then(() => {}, () => {});
    }
    return { id, name, email: session.user.email ?? null, avatarUrl: '', color: '#888', isOwner: role === 'owner', canEdit: role === 'owner' };
  },
  async id() { await ready; return session?.user.id ?? null; },
  async isOwner() { await ready; return role === 'owner'; },
  async canEdit() { await ready; return role === 'owner'; },
  async can(what: string) { await ready; return what === 'data.write' ? role !== null : role === 'owner'; },
  async profiles(ids: string | string[]) {
    const list = (Array.isArray(ids) ? ids : [ids]).filter(Boolean);
    const out: Record<string, Data> = {};
    if (!list.length) return out;
    const { data } = await sb.from('bunting_profiles').select('id,name').in('id', list);
    (data || []).forEach(p => { NAMES[p.id] = p.name; });
    list.forEach(id => { out[id] = { id, name: NAMES[id] || '', avatarUrl: '', color: '#888', email: null, isMe: id === session?.user.id, guest: false }; });
    return out;
  },
  async search() { return []; },
};

// ---------- db
const split = (path: string) => { const i = path.indexOf('/'); return { coll: path.slice(0, i), id: path.slice(i + 1) }; };
const snap = (id: string, d: Data | undefined): Snap => ({ id, exists: d !== undefined, data: () => (d === undefined ? undefined : clone(d)), metadata: { fromCache: false, hasPendingWrites: false } });

function mapError(e: { code?: string; message?: string } | null, writing: boolean): RuntimeError {
  const msg = e?.message || 'Request failed';
  if (!e) return fail('unavailable', msg);
  if (e.code === '42501' || /row-level security|permission/i.test(msg)) {
    // Not allowed to write. Signed-out viewers and non-members switch the demo to read-only;
    // a contributor touching owner-only data just gets a quiet refusal.
    return writing && role === null ? fail('invalid_argument', 'not allowed') : fail('permission_denied', msg);
  }
  if (e.code === '23514' && /size/.test(msg)) return fail('invalid_argument', 'document over 256 KiB');
  if (/fetch|network|timeout/i.test(msg)) return fail('unavailable', msg);
  return fail('internal', msg);
}

async function fetchColl(coll: string): Promise<Map<string, Data>> {
  const out = new Map<string, Data>();
  const page = 500;
  for (let from = 0; ; from += page) {
    const { data, error } = await sb.from('bunting_docs').select('doc_id,data').eq('coll', coll).order('doc_id').range(from, from + page - 1);
    if (error) throw mapError(error, false);
    (data || []).forEach(r => out.set(r.doc_id, r.data as Data));
    if (!data || data.length < page) break;
  }
  return out;
}
function querySnap(map: Map<string, Data>, changes: Change[]): QuerySnap {
  const docs = [...map.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([id, d]) => snap(id, d));
  return { docs, size: docs.length, empty: !docs.length, docChanges: () => changes, metadata: { fromCache: false, hasPendingWrites: false } };
}

function docRef(path: string) {
  const { coll, id } = split(path);
  return {
    id, path,
    async get(): Promise<Snap> {
      await ready;
      const { data, error } = await sb.from('bunting_docs').select('data').eq('path', path).maybeSingle();
      if (error) throw mapError(error, false);
      return snap(id, data ? (data.data as Data) : undefined);
    },
    async set(d: Data) {
      await ready;
      const json = JSON.stringify(d);
      if (new Blob([json]).size > MAX_BYTES) throw fail('invalid_argument', 'document over 256 KiB');
      if (!session) throw fail('invalid_argument', 'not allowed');
      const { error } = await sb.from('bunting_docs').upsert({ path, coll, doc_id: id, data: JSON.parse(json), updated_at: new Date().toISOString() });
      if (error) throw mapError(error, true);
    },
    async update(d: Data) {
      const cur = await this.get();
      if (!cur.exists) throw fail('invalid_argument', 'missing');
      await this.set(Object.assign(cur.data() || {}, clone(d)));
    },
    async delete() {
      await ready;
      const { error } = await sb.from('bunting_docs').delete().eq('path', path);
      if (error) throw mapError(error, true);
    },
    onSnapshot(next: (s: Snap) => void, err?: (e: RuntimeError) => void) {
      const stop = collRef(coll).onSnapshot(qs => { const d = qs.docs.find(x => x.id === id); next(d || snap(id, undefined)); }, err);
      return stop;
    },
    collection(sub: string) { return collRef(path + '/' + sub); },
  };
}

function collRef(coll: string) {
  return {
    path: coll,
    doc: (id?: string) => docRef(coll + '/' + (id || Math.random().toString(36).slice(2))),
    async get(): Promise<QuerySnap> {
      await ready;
      const map = await fetchColl(coll);
      return querySnap(map, [...map.entries()].map(([id, d], i) => ({ type: 'added', doc: snap(id, d), oldIndex: -1, newIndex: i })));
    },
    onSnapshot(next: (qs: QuerySnap) => void, err?: (e: RuntimeError) => void) {
      let dead = false, channel: RealtimeChannel | null = null, poll: ReturnType<typeof setInterval> | null = null;
      const local = new Map<string, Data>();
      // Compare a fresh copy of the collection with what we last delivered.
      const resync = async (first = false) => {
        if (dead) return;
        try {
          const fresh = await fetchColl(coll);
          const changes: Change[] = [];
          fresh.forEach((d, id) => {
            const old = local.get(id);
            if (old === undefined) changes.push({ type: 'added', doc: snap(id, d), oldIndex: -1, newIndex: 0 });
            else if (JSON.stringify(old) !== JSON.stringify(d)) changes.push({ type: 'modified', doc: snap(id, d), oldIndex: 0, newIndex: 0 });
          });
          local.forEach((d, id) => { if (!fresh.has(id)) changes.push({ type: 'removed', doc: snap(id, d), oldIndex: 0, newIndex: -1 }); });
          local.clear(); fresh.forEach((d, id) => local.set(id, d));
          if (changes.length || first) next(querySnap(local, changes));
        } catch (e) { err?.(e as RuntimeError); }
      };
      ready.then(async () => {
        await resync(true);
        if (dead) return;
        channel = sb.channel('docs:' + coll + ':' + Math.random().toString(36).slice(2))
          .on('postgres_changes', { event: '*', schema: 'public', table: 'bunting_docs', filter: 'coll=eq.' + coll }, payload => {
            if (dead) return;
            const row = (payload.eventType === 'DELETE' ? payload.old : payload.new) as { doc_id?: string; data?: Data; path?: string };
            const id = row.doc_id || (row.path ? split(row.path).id : '');
            if (!id) { resync(); return; }
            if (payload.eventType === 'DELETE') {
              const old = local.get(id); if (old === undefined) return;
              local.delete(id); next(querySnap(local, [{ type: 'removed', doc: snap(id, old), oldIndex: 0, newIndex: -1 }]));
            } else if (row.data) {
              const had = local.has(id); local.set(id, row.data);
              next(querySnap(local, [{ type: had ? 'modified' : 'added', doc: snap(id, row.data), oldIndex: had ? 0 : -1, newIndex: 0 }]));
            } else resync(); // large rows can arrive without their data
          })
          .subscribe(status => { if (status === 'SUBSCRIBED') resync(); });
        // Safety net: catch anything missed while the tab slept or the socket dropped.
        poll = setInterval(() => { if (document.visibilityState === 'visible') resync(); }, 20000);
      });
      const onVis = () => { if (document.visibilityState === 'visible') resync(); };
      document.addEventListener('visibilitychange', onVis);
      return () => { dead = true; if (channel) sb.removeChannel(channel); if (poll) clearInterval(poll); document.removeEventListener('visibilitychange', onVis); };
    },
    where() { return this; }, orderBy() { return this; }, limit() { return this; },
  };
}
const db = { doc: docRef, collection: collRef };

// ---------- downloads
const downloads = {
  async save({ filename, data, mimeType }: { filename: string; data: string | Blob | ArrayBuffer; mimeType?: string }) {
    const type = mimeType || (/\.csv$/i.test(filename) ? 'text/csv' : /\.ics$/i.test(filename) ? 'text/calendar' : /\.json$/i.test(filename) ? 'application/json' : 'application/octet-stream');
    const blob = data instanceof Blob ? data : new Blob([data], { type });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = filename; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 10000);
    return { status: 'saved' };
  },
};

// ---------- account bar (sign in / out)
function accountBar() {
  const el = document.createElement('div');
  el.id = 'bunting-account';
  el.setAttribute('role', 'status');
  const css = document.createElement('style');
  css.textContent = `#bunting-account{position:fixed;left:50%;transform:translateX(-50%);bottom:12px;z-index:40;display:flex;gap:10px;align-items:center;
    padding:7px 8px 7px 14px;border-radius:999px;background:var(--surface,#fff);color:var(--ink,#16203A);border:1px solid var(--line,#E4E6EE);
    box-shadow:var(--shadow,0 4px 16px rgba(0,0,0,.08));font:500 13px/1.2 var(--body,system-ui,sans-serif);max-width:calc(100vw - 32px)}
    #bunting-account a,#bunting-account button{font:inherit;font-weight:600;border:0;border-radius:999px;padding:6px 12px;cursor:pointer;text-decoration:none;
    background:var(--accent,#D6336C);color:var(--accent-ink,#fff)}#bunting-account .x{background:transparent;color:var(--muted,#5E667A);padding:4px 8px}
    #bunting-account span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    body.hasmodal #bunting-account,body.touring #bunting-account{display:none}`;
  const render = () => {
    let text = '', action = '';
    if (!session) { text = 'You can look around. Sign in to try it.'; action = '<a href="/login">Sign in</a>'; }
    else if (role === null) { text = `Signed in as ${esc(session.user.email || '')}. Ask Tony to add you to save changes.`; action = '<button data-out>Sign out</button>'; }
    else { text = `Signed in as ${esc(session.user.email || '')}${role === 'owner' ? ' · <a href="/members" style="background:none;color:inherit;padding:0;text-decoration:underline">Members</a>' : ''}`; action = '<button data-out>Sign out</button>'; }
    el.innerHTML = `<span>${text}</span>${action}<button class="x" aria-label="Hide" data-hide>×</button>`;
  };
  el.addEventListener('click', async e => {
    const t = e.target as HTMLElement;
    if (t.closest('[data-out]')) { await sb.auth.signOut(); location.reload(); }
    if (t.closest('[data-hide]')) { el.remove(); try { sessionStorage.setItem('bunting.bar.hidden', '1'); } catch { /* ignore */ } }
  });
  ready.then(() => {
    try { if (sessionStorage.getItem('bunting.bar.hidden') && session) return; } catch { /* ignore */ }
    render(); document.head.appendChild(css); document.body.appendChild(el);
  });
}
const esc = (s: string) => s.replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c] as string));

// ---------- expose
const caps: Record<string, unknown> = { db, user, downloads };
(window as unknown as { claude: unknown }).claude = {
  use: async (name: string) => { await ready; if (name in caps) return caps[name]; throw fail('unsupported', `${name} isn't available on this site`); },
};
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', accountBar); else accountBar();
