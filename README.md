# Us, Every Day 💗 — Couple attendance

This is a deployable, mobile-friendly couple attendance website. It uses Supabase for password-based authentication and shared online data.

## Attendance rules

- Both available: both are present.
- Only one available: the available person is present and the unavailable person is absent.
- Both unavailable: shared holiday; excluded from both attendance denominators.
- Percentage = present ÷ (present + absent) × 100. A day is counted only after both accounts have submitted a status.
- Attendance is recorded per calendar day. Each person can change their own status for that day.

## 1. Create the database

1. Create a free project at https://supabase.com/.
2. Open **SQL Editor** in the Supabase dashboard.
3. Paste and run all of `supabase-setup.sql`.
4. Open **Project Settings → API** and copy the Project URL and `anon` / publishable key.

## 2. Configure the website

Open `index.html` in a text editor. Replace:
- `PASTE_YOUR_SUPABASE_PROJECT_URL`
- `PASTE_YOUR_SUPABASE_ANON_KEY`

with the values from your Supabase project. The anon/publishable key is designed for browser use; never put a service-role or secret key in this file.

## 3. Publish online

1. Create a repository on GitHub and upload `index.html`.
2. Import that repository into https://vercel.com/ or https://www.netlify.com/.
3. Deploy it as a static site (no build command; publish/root directory is the repository root).
4. Open the deployed URL on both phones.

## 4. Create your two accounts

1. Person 1 opens the site and selects **Create account** with their own email and password.
2. Confirm the email if Supabase email confirmation is enabled, then log in.
3. The first account creates the couple space by running this once while logged in. In the browser console, run:
   `await sb.rpc('create_couple')`
   Then refresh the page. The dashboard will show the invite code.
4. Person 2 creates their own account, enters the invite code in **Couple code**, and selects **Join our space**.
5. Both can now log in from their own phones and mark their daily availability.

## Important first-run note

The first account's couple space must be initialized once. The SQL function `create_couple()` is included. After signing in as the first account, open the browser developer console and run `await sb.rpc('create_couple')`, then refresh. The dashboard displays the invite code.

## Privacy and safety

- Passwords are handled by Supabase Auth; this app never stores or reads passwords itself.
- Row-level security limits attendance and profile reads to members of the same couple.
- Keep the invite code private. Anyone who obtains it before the space is full could try to join.
- This project is not yet hosted; follow the deployment steps above to put it online.
