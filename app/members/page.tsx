'use client';
import { useCallback, useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';

type Member = { email: string; role: 'owner' | 'contributor'; added_at: string };

export default function Members() {
  const [me, setMe] = useState<string | null | undefined>(undefined);
  const [isOwner, setIsOwner] = useState(false);
  const [rows, setRows] = useState<Member[]>([]);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<'contributor' | 'owner'>('contributor');
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const load = useCallback(async () => {
    const { data } = await supabase().from('bunting_members').select('email,role,added_at').order('added_at');
    setRows((data as Member[]) || []);
  }, []);

  useEffect(() => {
    (async () => {
      const { data } = await supabase().auth.getSession();
      const em = data.session?.user.email?.toLowerCase() ?? null;
      setMe(em);
      if (!em) return;
      const { data: m } = await supabase().from('bunting_members').select('role').eq('email', em).maybeSingle();
      setIsOwner(m?.role === 'owner');
      if (m?.role === 'owner') load();
    })();
  }, [load]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    const em = email.trim().toLowerCase();
    const { error } = await supabase().from('bunting_members').upsert({ email: em, role });
    if (error) setMsg({ ok: false, text: error.message });
    else { setMsg({ ok: true, text: `${em} can now save changes in the demo. Send them the link to sign in.` }); setEmail(''); load(); }
  }
  async function remove(em: string) {
    const { error } = await supabase().from('bunting_members').delete().eq('email', em);
    if (error) setMsg({ ok: false, text: error.message }); else load();
  }

  if (me === undefined) return <main className="wrap" />;
  if (!me || !isOwner) {
    return (
      <main className="wrap">
        <h1 className="brand"><a href="/">Bunting</a></h1>
        <p className="sub">Only the demo owner can manage who has access.</p>
        <a href={me ? '/' : '/login'}>{me ? 'Back to the demo' : 'Sign in'}</a>
      </main>
    );
  }
  return (
    <main className="wrap wide">
      <h1 className="brand"><a href="/">Bunting</a></h1>
      <p className="sub">People who can save changes in the demo. Anyone else with the link can look around but can&apos;t change anything. Feedback and the admin view stay private to you.</p>
      <form className="card" onSubmit={add}>
        <div className="row">
          <label>Email<input type="email" required value={email} onChange={e => setEmail(e.target.value)} /></label>
          <label style={{ flex: '0 0 160px', minWidth: 0 }}>Access
            <select value={role} onChange={e => setRole(e.target.value as 'contributor' | 'owner')}>
              <option value="contributor">Contributor</option>
              <option value="owner">Owner</option>
            </select>
          </label>
          <button>Add</button>
        </div>
        {msg && <p className={'msg ' + (msg.ok ? 'good' : 'bad')}>{msg.text}</p>}
        <table>
          <thead><tr><th>Email</th><th>Access</th><th /></tr></thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.email}>
                <td>{r.email}</td>
                <td>{r.role === 'owner' ? 'Owner' : 'Contributor'}</td>
                <td style={{ textAlign: 'right' }}>{r.email !== me && <button className="ghost" onClick={() => remove(r.email)}>Remove</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </form>
    </main>
  );
}
