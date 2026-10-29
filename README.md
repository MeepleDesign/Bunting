# Bunting

A party planning marketplace for Brighton & Hove. This repo is the **hosted demo**: the working prototype running on its own site, with real sign-in and a shared live database. No real payments happen.

## How it fits together

| Part | What it does |
| --- | --- |
| `prototype/bunting.html` | The prototype, exactly as built in Claude. Every screen and flow lives here. |
| `src/runtime/index.ts` | Gives the prototype the small API it expects (`db`, `user`, `downloads`), backed by Supabase. |
| `scripts/build-demo.mjs` | Bundles the runtime and wraps the prototype into `public/bunting.html`, served at `/`. |
| `app/login` | Email sign-in link (no passwords). |
| `app/members` | Owner-only page to choose who can save changes. |
| `supabase/migrations` | Tables and access rules. |
| `tests/smoke.mjs` | Runs the demo against an in-browser fake of Supabase and checks the access rules. |

**Hosting:** Next.js on Vercel. **Data:** Supabase (tables prefixed `bunting_` in the MeepleDesign project).

## Who can do what

- **Anyone with the link** can look around, read-only.
- **Members** (added on `/members`) can save changes: bookings, suppliers, messages and so on.
- **The owner** also sees the admin dashboard and feedback, and can change admin settings.
- **Feedback** is only visible to the person who wrote it and the owner. This is enforced by the database, not just hidden in the page.

## Updating the prototype

1. Replace `prototype/bunting.html` with the latest version from the Claude artifact.
2. Run `npm test`.
3. Commit and push. Vercel deploys automatically.

## Running locally

```bash
npm install
npm run dev        # http://localhost:3000
npm test           # smoke test (needs Playwright)
```

Copy `.env.example` to `.env.local` to point at a different Supabase project. Without it, the app uses the MeepleDesign project.

## One-off Supabase setup

In the Supabase dashboard, go to **Authentication → URL Configuration** and add the site address to **Redirect URLs**, for example `https://bunting-demo.vercel.app/**`. Without this, sign-in links go to the project's default site instead.

The built-in Supabase email service only sends a few sign-in emails an hour. Before sharing widely, add your own SMTP under **Authentication → Emails** (Resend's free tier works well).

## Next steps towards the MVP

The prototype stores each area of the app as documents. The MVP (spec, phase 2) will gradually replace this with proper tables: suppliers, packages, events, bookings and payments. That way the pricing engine and permissions run on the server, not in the browser.
