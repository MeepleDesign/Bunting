'use client';
import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';

export default function Login() {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [state, setState] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');
  const [error, setError] = useState('');
  const [signedIn, setSignedIn] = useState<string | null>(null);

  useEffect(() => {
    supabase().auth.getSession().then(({ data }) => setSignedIn(data.session?.user.email ?? null));
  }, []);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    setState('sending'); setError('');
    const { error } = await supabase().auth.signInWithOtp({
      email: email.trim().toLowerCase(),
      options: { emailRedirectTo: window.location.origin + '/', data: name.trim() ? { name: name.trim() } : undefined },
    });
    if (error) { setState('error'); setError(error.message); } else setState('sent');
  }

  return (
    <main className="wrap">
      <h1 className="brand"><a href="/">Bunting</a></h1>
      <p className="sub">Sign in to try the demo. We&apos;ll email you a link, so there&apos;s no password.</p>
      {signedIn ? (
        <div className="card">
          <p className="msg">You&apos;re signed in as <b>{signedIn}</b>.</p>
          <div className="row">
            <button onClick={() => { window.location.href = '/'; }}>Open the demo</button>
            <button className="ghost" onClick={async () => { await supabase().auth.signOut(); setSignedIn(null); }}>Sign out</button>
          </div>
        </div>
      ) : state === 'sent' ? (
        <div className="card">
          <p className="msg good">Check your email. We&apos;ve sent a sign-in link to <b>{email}</b>.</p>
          <p className="msg">Open it in this browser. It can take a minute to arrive, so check your spam folder too.</p>
          <button className="ghost" onClick={() => setState('idle')}>Use a different email</button>
        </div>
      ) : (
        <form className="card" onSubmit={send}>
          <label>Email<input type="email" required autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} /></label>
          <label>Your name (shown to other people using the demo)<input autoComplete="name" value={name} onChange={e => setName(e.target.value)} /></label>
          <button disabled={state === 'sending'}>{state === 'sending' ? 'Sending…' : 'Email me a sign-in link'}</button>
          {state === 'error' && <p className="msg bad">{error}</p>}
          <p className="msg">Anyone can look around. To save changes, Tony needs to add your email.</p>
        </form>
      )}
    </main>
  );
}
