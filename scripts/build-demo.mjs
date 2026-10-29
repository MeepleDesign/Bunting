// Builds the static demo: bundles the runtime and wraps the prototype in a full HTML page.
// Input:  prototype/bunting.html (the prototype exactly as published as a Claude artifact)
// Output: public/runtime.js and public/bunting.html
import { build } from 'esbuild';
import { readFileSync, writeFileSync } from 'node:fs';

const env = k => JSON.stringify(process.env[k] || '');
await build({
  entryPoints: ['src/runtime/index.ts'],
  bundle: true, minify: true, format: 'iife', target: 'es2020',
  outfile: 'public/runtime.js',
  define: {
    'process.env.NEXT_PUBLIC_SUPABASE_URL': env('NEXT_PUBLIC_SUPABASE_URL'),
    'process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY': env('NEXT_PUBLIC_SUPABASE_ANON_KEY'),
  },
  logLevel: 'warning',
  // Smoke tests swap in an in-browser fake of Supabase (see tests/fake-supabase.ts).
  alias: process.env.BUNTING_FAKE ? { '@supabase/supabase-js': './tests/fake-supabase.ts' } : {},
});

let html = readFileSync('prototype/bunting.html', 'utf8');

// Wording that only made sense inside Claude.
const swaps = [
  ['Uses your Claude account.', 'Uses your Bunting sign-in.'],
  ['Ask the owner for Contributor access to try it for real.', 'Sign in with an invited email to try it for real.'],
  ["Ask the owner for Contributor access.", 'Sign in with an invited email to save changes.'],
  ['open the Share menu on this page and give them <b>Contributor</b> access. Viewers can look around but can\'t save anything.',
   'add their email on the <a href="/members">Members</a> page. Anyone else can look around but can\'t save anything.'],
  ["Downloads aren't available here. Open the page in Claude to download", "Downloads aren't available in this browser"],
];
for (const [from, to] of swaps) {
  if (!html.includes(from)) { console.warn('build-demo: wording not found, skipped:', from.slice(0, 60)); continue; }
  html = html.split(from).join(to);
}

// The artifact is a fragment (the host adds the document shell), so add one here.
const head = `<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Plan a party in Brighton & Hove: instant prices from venues, caterers, DJs and more.">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<script src="/runtime.js"></script>
`;
// Browsers place the title, meta and style tags in the head and start the body at the first page element.
const hasShell = /<html[\s>]/i.test(html);
const out = hasShell ? html.replace(/<head>/i, m => m + '\n<script src="/runtime.js"></script>') : head + html + '\n';
writeFileSync('public/bunting.html', out);
console.log('build-demo: wrote public/bunting.html (' + Math.round(out.length / 1024) + ' KB) and public/runtime.js');
