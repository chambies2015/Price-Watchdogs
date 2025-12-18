# 🐾 Price & Subscription Change Monitor
*A boring, useful SaaS that quietly makes money*

---

## 0. Product Vision (Short & Sharp)
A lightweight web app that **monitors SaaS pricing pages, subscription terms, and plan structures**, detects meaningful changes, and **alerts users before they get surprised by higher bills**.

**Core value promise:**
> "Know when prices or plans change — before it costs you money."

This is **not** a general web monitor.
This is **price & plan intelligence**, tuned for clarity over noise.

---

## 1. Target Users (Laser-Focused)

### Primary
- Indie hackers
- Freelancers / contractors
- Small business owners
- Startup operators

### Secondary (later)
- Finance / ops teams
- Agencies managing many SaaS tools

**User pain:**
- Silent price increases
- Free tiers removed
- Plan limits changed
- Annual renewals forgotten

If they miss a change → **they lose money**.

---

## 2. Competitive Advantage (How We Win)

We **do less**, but do it **cleaner**:

- No uptime noise
- No "monitor everything" nonsense
- Diff only **pricing-relevant content**
- Human-readable change summaries

Positioning:
> "Not a website monitor. A price change watchdog."

---

## 3. MVP Feature Set (No Bloat)

### 3.1 Authentication
- Email + password
- Magic link (optional, v2)

---

### 3.2 Service Tracking
Users can add a monitored service:

**Required fields**
- Service name
- URL (pricing / plans page)
- Check frequency (daily default)

**Optional fields**
- Selector override (advanced users)
- Tags ("billing", "critical")

---

### 3.3 Change Detection
On each check:
- Fetch page
- Extract pricing-relevant content
- Normalize text
- Compare to last snapshot
- Classify change

Change types:
- Price increase
- Price decrease
- New plan added
- Plan removed
- Free tier removed
- Unknown / general change

---

### 3.4 Alerts
- Email notifications
- One alert per meaningful change

Alert includes:
- What changed
- Before vs after
- Timestamp
- Direct link to diff view

---

### 3.5 Change History
- Timeline per service
- Expandable diffs
- Visual highlights

---

### 3.6 Dashboard
- All tracked services
- Last check status
- Last change detected
- Alert toggle per service

---

## 4. Non-Goals (MVP Guardrails)
- ❌ No browser extension
- ❌ No SMS / Slack
- ❌ No team accounts
- ❌ No AI summaries (yet)
- ❌ No scraping login-protected pages

Keep it sharp. Keep it profitable.

---

## 5. Tech Stack (Solo-Dev Friendly)

### Backend
- Node.js (NestJS or Express)
- PostgreSQL
- Prisma or Drizzle ORM

### Frontend
- Next.js
- Server Components where possible
- Minimal Tailwind

### Infra
- Fly.io / Render
- Cron-based background workers
- Resend / Postmark for email

---

## 6. Data Model (Schema)

### User
```sql
id (uuid)
email (unique)
password_hash
created_at
```

---

### Service
```sql
id (uuid)
user_id (fk)
name
url
check_frequency (enum: daily, weekly)
last_checked_at
last_snapshot_id (fk)
is_active
created_at
```

---

### Snapshot
```sql
id (uuid)
service_id (fk)
raw_html_hash
normalized_content_hash
normalized_content (text)
created_at
```

---

### ChangeEvent
```sql
id (uuid)
service_id (fk)
old_snapshot_id
new_snapshot_id
change_type (enum)
summary (text)
confidence_score (float)
created_at
```

---

### Alert
```sql
id (uuid)
change_event_id (fk)
user_id (fk)
sent_at
channel (email)
```

---

## 7. Background Jobs (The Money Makers)

### 7.1 Page Fetch Job
**Runs:** every hour

Steps:
1. Select services due for check
2. Fetch page
3. Sanitize HTML
4. Extract pricing sections
5. Normalize text
6. Store snapshot

---

### 7.2 Diff & Classification Job
Triggered after snapshot insert:

1. Compare against previous snapshot
2. Detect meaningful deltas
3. Classify change type
4. Create ChangeEvent

Ignore:
- timestamps
- cookie banners
- marketing fluff

---

### 7.3 Alert Dispatch Job
Triggered by new ChangeEvent:

1. Verify confidence threshold
2. Check user alert settings
3. Send email
4. Log alert

---

### 7.4 Cleanup Job (Weekly)
- Prune old snapshots (keep diffs)
- Deduplicate unchanged content

---

## 8. Pricing Model (Simple & Honest)

### Free
- 3 services
- Daily checks

### Pro – $7/month
- Unlimited services
- Faster checks
- Priority alerts

### Annual
- 2 months free

Stripe only. No experiments.

---

## 9. MVP Launch Strategy (Low-Effort)

### Day 1
- Indie Hackers
- Hacker News "Show HN"

### Evergreen
- SEO landing pages:
  - "SaaS price increase monitor"
  - "track subscription price changes"

### Conversion hook
> "One missed price hike pays for this for a year."

---

## 10. Future Expansion (After Revenue)

- AI-generated summaries
- Slack / Discord alerts
- Shared dashboards
- Vendor profiles
- Public price history pages

---

## 11. Success Metrics

- Time to first alert < 24h
- < 1 false alert per user / month
- Break-even at 5–10 users

---

## 12. Build Order (Do Not Deviate)

1. Auth + DB
2. Service CRUD
3. Snapshot system
4. Diff engine
5. Email alerts
6. Dashboard polish
7. Billing

---

## Final Note
This app succeeds by being **quiet**, **accurate**, and **trustworthy**.
Not flashy. Not viral.

Just a good little money printer that behaves.

🐾 End of master file

