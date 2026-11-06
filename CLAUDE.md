# Bunting – notes for Claude

Bunting is Tony Webb's side project: a marketplace and planning tool for private parties (milestone birthdays, engagements, anniversaries) in Brighton & Hove. Planners get instant, comparable prices from venues, caterers, DJs and so on, book with a deposit, and run the whole event (budget, guests, RSVPs, messages, payments) in one place. Suppliers get free business tools and pay commission only on bookings Bunting sends them.

Tony is an indirect tax professional (VAT, compliance), not a developer. Explain technical choices in plain English, use UK spelling, and keep user-facing wording plain and friendly. He is self-funding, so prefer free or low-cost options and say when something costs money.

## Where things are

| What | Where |
| --- | --- |
| The prototype (every screen and flow) | `prototype/bunting.html`: one self-contained file, about 560 KB |
| Hosted demo | https://bunting-demo.vercel.app (Vercel project `bunting-demo`, team "Meeple Design's projects"). Every push to `main` deploys. |
| Claude artifact version of the demo | https://claude.ai/artifact/1SzdR6NfkdnhCu4ybZeRgB (version 44 = this repo as of 6 Nov 2026). It runs the same file inside Claude. It is no longer the source of truth: edit this repo, and republish the artifact only if Tony asks. |
| Database | Supabase project `iwqdohdcfszylvwihmrs` ("MeepleDesign's Project", shared with another app, so every Bunting table is prefixed `bunting_`). Schema and access rules: `supabase/migrations/0001_bunting_init.sql`. |
| Documents | Google Drive folder `1amGtHPRVwzS3w4OqRQ2Hoxi_qiDkkzfg`. **Standing rule from Tony: all documentation for Bunting is saved in this folder.** |

### Documents in the Drive folder

- **Product Specification** (`1oPN7kaU99wspAz2ZSrPhQDND3-KkKR5lVmLei79wzeU`), version 1.6. Keep it in step with the prototype: bump the version line and edit the relevant sections when features change.
- **Product Decisions** (`1EQ5I9mrNiGLLbCfsEvykJ0XftmO8ZIz9LEnmp43CEF0`)
- **Supplier Testing Playbook** (`103QISrHtW5BY_WVV2By6t0urbJOT_ipA-xnki6aDjH0`)
- **Compliance Review: VAT and Platform Reporting** (`1CEsLfmAdWbnbAWNGSvYyzsQX7fCProH4XdMCYQDGh18`)
- **Demo Testing Script** (`1ZLEs_HdUzIy01RNy4fYU8V0OfKKqbrCdBV7kPQlFUbU`): testers get a copy each. Update it when features change.
- **Fees: Free and Pro** spreadsheet (`1sBDVlu3Iq9wlC7tXb32X_qHBHqoH38u3acY83oQFeLI`)
- **Next Steps and Income Potential** (Claude Doc): https://claude.ai/artifact/9yQog64c7XEGyYVHoKQRnB

## How the hosted demo works

- `prototype/bunting.html` was written against a small runtime API: `window.claude.use('db' | 'user' | 'downloads')`.
- `src/runtime/index.ts` provides that API using Supabase:
  - `db` is a Firestore-like document store on the `bunting_docs` table, with realtime updates and a 20-second resync.
  - `user` uses Supabase email-link sign-in and the `bunting_members` roles.
  - `downloads` saves files through the browser.
- `scripts/build-demo.mjs` does two things:
  - It bundles the runtime with esbuild and wraps the prototype in an HTML page, writing `public/bunting.html` (served at `/`) and `public/runtime.js`.
  - It swaps a few phrases that only made sense inside Claude. If a phrase isn't found, it warns rather than failing.
- Access rules are enforced in the database by row level security, not in the page:
  - Anyone can read the demo data.
  - Members can write it.
  - Only the owner can write the `admin/*` docs.
  - `feedback/*` is readable only by its author and the owner.
- Next.js pages: `/login` (email link) and `/members` (the owner adds testers).
- **Still to do in Supabase.** These are dashboard settings that can't be changed from code:
  - Add `https://bunting-demo.vercel.app/**` to Authentication → URL Configuration → Redirect URLs.
  - Set up custom SMTP (Resend free tier). The built-in email only sends a few emails an hour.

## How the prototype is built

- **Structure:** a single file holding the CSS, the HTML and one large JavaScript IIFE. State lives in `S`. `render()` draws the page and `renderModal()` draws pop-ups. `setView(v)` changes screen.
- **Debugging:** `window.__dbg` exposes `S`, `setView`, `loadAccount`, `SUP`, `ACC`, `LIVE`, `SUPDATA` and `NAV`. Tests use it, so keep it.
- **Demo accounts:** `loadAccount('tony')` is the planner, with events `e1` (Sam's 40th) and `e2` (Mum's 60th). `loadAccount('supplier')` is Sophie at Pier & Plate (`pierplate`). `S.supplierAs` can be any supplier id.
- **Shared data:**
  - `worldDocs()` and `applyDoc()` serialise supplier data (`SUPDATA[sid]`: others, ownClients, requests, sthreads, disputes, viewings, referrals) and the accounts.
  - `SETTINGS` is saved to `admin/settings`.
  - Anything new that must be shared has to live in those structures.
- **Event hooks:**
  - `featClick(t)` handles clicks: return true when handled. It calls `newClick` and `areaClick` first.
  - `newChange` handles change events.
  - `renderModal` dispatches on `S.modal.type` via a chain of `m.type==='x'?mX():` ternaries.
  - New features have usually been added as blocks inserted before `function tourLS(`.
- **Back button (`NAV`, near the end of the file):** each screen, supplier tab, pop-up and (on phones) open conversation gets a history entry. `render` and `renderModal` are wrapped to call `navSync()`. History starts on the first tap.
- **Layout:** phone layouts switch at 780px. Colours are CSS tokens on `:root`, with a dark mode.
- **Appointments (viewings, tastings and chats):**
  - `vset(s)` returns a supplier's settings (on, mins, where, addr, link, fee, feePer, credit, slots).
  - Each appointment is stored in `SUPDATA[sid].viewings`.
  - Statuses are `requested` (the planner asked), `offered` (the supplier offered times), `booked`, `cancelled` and `declined`.
  - `followup` marks an appointment made after booking. Follow-ups are always free.
  - Paid fees appear in `platformPayments()`. `tastingCredit()` takes a fee off a booking, and that fee is counted only once.
  - Planners' private notes live in `ACC[acc].vnotes`.

### Editing safely

- The file is large. Use targeted find-and-replace that checks each match is unique. Never retype big sections.
- Check the JavaScript still parses after every change. Pull the largest `<script>` block out into a temporary file and run `node --check` on it.
- Watch for apostrophes inside single-quoted JavaScript strings, and for `${}` inside template literals. Both have broken the build before.
- If you replace a whole function, make sure you don't also swallow any `const` declarations that sit between it and the next function.

## Testing

- **Smoke test for the hosted demo:**
  - Run `npm test`.
  - It builds with an in-browser fake of Supabase (`tests/fake-supabase.ts`), serves `public/`, and checks sign-in roles, writes, private feedback, live updates between tabs, downloads and the 256 KB size limit.
  - It needs Node packages and `playwright` for Node.
- **Prototype regression suite:**
  - Run `bash tests/prototype/run_all.sh` for all 21 scripts, or name some, for example `bash tests/prototype/run_all.sh tvw tvw2 tback`.
  - It needs Python Playwright: `pip install playwright && playwright install chromium`.
  - Each script tests at 1280px and 390px wide. A script fails if it prints FAIL, a traceback or page errors.
  - `ta2` and `t21` are flaky two-page live tests: rerun them alone before investigating.
- **When adding a feature:**
  - Add a test script in `tests/prototype/` and include it in the default list in `run_all.sh`.
  - Run the whole suite before pushing.

## Decisions so far (details in the Decisions doc and the spec)

- **Fees:** reduced 6 November to help suppliers adopt Bunting and come to rely on it early.
  - Commission: 5% working figure (was 8%), set after testing.
  - Founding suppliers: 0% on their first 3 bookings, then 3% for 12 months (was 5%).
  - Pro: free for suppliers' first 6 months after real launch, then £9 a month or £90 a year (was £19/£190). Still free for everyone while Bunting is in testing.
  - Pro grouping (which features are free vs Pro-only) and the 0.5% Bunting margin on Pro suppliers' own-client card payments: approved as proposed 27 October.
  - No booking fee for planners. An optional planner premium comes later.
  - Featured placement comes later, as a separate add-on.
- **Payments:** Stripe Connect direct charges. The supplier is the merchant of record and Bunting acts as a disclosed commercial agent. Bunting never holds money.
  - For the live build, choose a Connect setup where suppliers, not Bunting, carry chargebacks and refunds.
  - Process refunds manually at first.
  - Reconcile against Stripe daily.
- **Supplier checks:**
  - Insurance is required to list for venues, caterers, bars and activities (admin can change these categories).
  - There's no alcohol licence check. Bars declare their licensing instead.
  - The food hygiene (FSA) rating is checked automatically on a schedule.
- **Appointments:**
  - Any supplier can offer viewings, tastings or chats: in person, at the customer's, by video or by phone. They can be free or charged, per appointment or per person, with the fee optionally taken off the booking.
  - Cancelling is free up to 48 hours before.
  - Planners can ask any supplier for a time.
  - Suppliers can offer times from requests and bookings.
- **Expansion:** stage 1 grows through supplier invites. Stage 2 is sign up anywhere, with an area opening once it has 2 checked suppliers per core category (Areas view in admin).

## Where things stand (6 November 2026)

- The demo is hosted and ready for testers. The testing script exists.
- **Waiting on Tony:**
  - Supabase redirect URL and SMTP.
  - Commission on appointment fees.
  - Checking his KAYAK employment contract (IP and outside work) before announcing anything.
- **Next big piece, the live MVP (spec section 15):**
  - Rebuild on proper tables (suppliers, packages, events, bookings, payments), with prices and bookings worked out on the server and per-user access rules.
  - Keep the tested screens.
  - Go live in two steps: first without payments (real accounts, listings, booking requests, messages, guests), then Stripe Connect after test-mode coverage of every money flow and an independent review.
  - Bunting should get its own Supabase project before real customers arrive. The free plan allows 2 projects and Tony has used both, so this means pausing one or paying for Pro, about $25 a month.
  - Vercel Pro (about $20 a month) is needed once real bookings are taken, because the free plan doesn't allow commercial use.

## Git

- Commit as Tony (`Tony Webb <boardgames@meepledesign.com>`). Push to `main` only when Tony asks, or when the work he asked for is finished and tested; `main` deploys live.
- The remote is `https://github.com/MeepleDesign/Bunting`.
