# SATHRYX Christmas Computer Classes Portal

A Flask website and private admin console for the SATHRYX Christmas Holiday Special Computer Classes. Includes the supplied poster, certificate preview and full syllabus PDF.

## Included
- Responsive student-facing landing page, registration form and course details.
- Course poster and certificate preview; syllabus PDF download.
- English / Tamil / Hindi chatbot interface (OpenRouter preferred, Gemini fallback; basic course FAQ response if no AI key is configured).
- Supabase PostgreSQL integration for student registrations and detailed per-day learning records.
- Admin login, searchable student list, status management, attendance, daily progress, activities, attempts, learning interests, assessment scores, trainer remarks and next steps.
- Resend email notification to `sahayasathish60@gmail.com` for new registrations.

## 1. Create Supabase database
1. Create a Supabase project.
2. Open **SQL Editor** and run all of `sql/schema.sql`.
3. In Project Settings → API, copy the Project URL and **service_role** key. The service-role key is private and must only be stored on the Flask server.

## 2. Configure environment
1. Copy `.env.example` to `.env`.
2. Fill in `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.
3. Set a strong `FLASK_SECRET_KEY` (random long value).
4. Set the admin email to `sahayasathish60@gmail.com`.
5. Generate a fresh admin password hash:
   ```bash
   python make_admin_hash.py
   ```
   Put the printed value into `.env` as `ADMIN_PASSWORD_HASH`. A password was included in the project request; it is intentionally **not** embedded in source code or the ZIP. Choose a new private password instead.
6. For AI, add `OPENROUTER_API_KEY` or `GEMINI_API_KEY`. OpenRouter is attempted first. The chatbot will still answer basic course FAQs without a key.
7. For email, create a Resend account, verify a sending domain, then set `RESEND_API_KEY` and `EMAIL_FROM`. The app sends registration notifications to `sahayasathish60@gmail.com`. Resend's test sender may only deliver to verified recipients; production sending requires a verified domain.

## 3. Run locally
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000`. Admin: `http://127.0.0.1:5000/admin/login`.

## 4. Deploy (Render example)
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn --workers 2 --timeout 120 --bind 0.0.0.0:$PORT app:app`
- Add all `.env` values in Render → Environment. Do not upload `.env` to GitHub.
- Set `COOKIE_SECURE=true` when using HTTPS.
- Test `/health`, a registration, admin login, record creation, chatbot and email delivery after deployment.

## Security notes
- Do not share the Supabase service-role key, Resend key, Gemini/OpenRouter keys, Flask secret, or admin password.
- Do not put secrets in HTML or JavaScript. This app calls Supabase and AI providers from the Flask server.
- Supabase tables have Row Level Security enabled and no public policies. Only the server's service-role key can access them. Keep it private.
- The admin password is checked against a Werkzeug password hash; no plaintext password is stored in the source.
- Student records are personal information, especially because learners may be minors. Obtain parent/guardian consent, limit access, and publish a privacy/retention notice before public launch.
- Configure backups and restrict access to the hosting account and Supabase project.

## Course content
The uploaded syllabus booklet is copied to `static/docs/sathryx-course-syllabus.pdf`. Course modules and outcomes shown on the site follow that booklet. The uploaded certificate image is a visual preview only; the site does not automatically issue a personalized certificate.

## Important production boundary
This ZIP is a deployable starter implementation, not a live-connected service. Supabase, AI and email integrations become active only after you configure the corresponding private credentials and execute the SQL setup. Test with sample data before accepting real student information.
