# Telegram sharing kit

Ready-made text for announcing BirthDex in a Telegram channel or group, plus a
short FAQ to pin.

Repository: <https://github.com/johirxofficial/birthdex> — adjust the links if
you publish a fork.

---

## Repository metadata

**Name:** `birthdex`

**Description (≤ 350 chars):**

> Self-hosted birth & death registration verification for Bangladesh (BDRIS).
> Manual captcha, clean JSON API, flat one-page UI, no OCR, no database.
> MIT licensed.

**Topics:**

```
bangladesh  bdris  birth-certificate  death-certificate  verification
flask  python  self-hosted  open-source  captcha  manual-captcha  api
```

**Release title:** `BirthDex v1.0.0 — manual captcha, zero OCR`

---

## Announcement (English)

> **BirthDex — verify Bangladesh birth & death registrations, self-hosted**
>
> I built a small open-source tool that verifies a birth (UBRN) or death (UDRN)
> registration on the BDRIS e-Verify portal and returns the record as clean
> JSON.
>
> The captcha is solved **by a human**, by design — no OCR, no captcha-solving
> services, no headless browser. The API shows you the image, you type the
> answer, you get the record.
>
> **What's inside**
> • One-page flat UI (no modals, no framework, under 20 KB of CSS/JS)
> • Two-endpoint JSON API: `/api/verify` + `/api/captcha/<id>.png`
> • The error response carries a fresh captcha, so retrying is one step
> • Single-use, 10-minute captcha sessions, in memory only
> • Windows / Linux / Docker, MIT licensed
> • 43 tests, entirely offline
>
> **Quick start**
> `pipx install birthdex` then `birthdex` → http://localhost:5002
> From source: `git clone https://github.com/johirxofficial/birthdex`
> `cd birthdex && ./run.sh` (Windows: `run.bat`)
>
> Repo: https://github.com/johirxofficial/birthdex
> Docs: API, deployment and contribution guidelines are in `/docs`.
>
> #bangladesh #opensource #flask #selfhosted #bdris

---

## Announcement (Bangla)

> **BirthDex — জন্ম ও মৃত্যু নিবন্ধন যাচাই, নিজের সার্ভারে**
>
> BDRIS e-Verify পোর্টাল থেকে জন্ম (UBRN) বা মৃত্যু (UDRN) নিবন্ধন যাচাই করে
> পরিষ্কার JSON ফেরত দেয় — ছোট, ওপেন সোর্স, সেলফ-হোস্টেড।
>
> captcha **মানুষ নিজে পড়বে** — কোনো OCR নেই, কোনো captcha-solving সার্ভিস নেই।
> API ছবি দেয়, আপনি উত্তর দেন, রেকর্ড চলে আসে।
>
> **যা আছে**
> • এক পাতার flat UI — কোনো popup/modal নেই, কোনো ফ্রেমওয়ার্ক নেই
> • দুটি endpoint: `/api/verify` ও `/api/captcha/<id>.png`
> • ভুল উত্তর হলে ৪২২-এর সাথে নতুন captcha — সাথে সাথে আবার চেষ্টা
> • captcha session একবারই ব্যবহারযোগ্য, ১০ মিনিট, শুধু মেমোরিতে
> • Windows / Linux / Docker, MIT লাইসেন্স
> • ৪৩টি টেস্ট, ইন্টারনেট ছাড়াই চলে
>
> **চালানো**
> `git clone https://github.com/johirxofficial/birthdex`
> `cd birthdex` → `run.bat` (Windows) বা `./run.sh`
> → http://localhost:5002
>
> রিপো: https://github.com/johirxofficial/birthdex
>
> #বাংলাদেশ #ওপেনসোর্স #জন্মনিবন্ধন #bdris

---

## One-liners

- "A captcha you can actually read — because a human reads it."
- "Two requests, one record, zero OCR."
- "Birth & death registration verification for Bangladesh, in under 20 KB of front-end."

---

## Suggested screenshots

1. The landing page with the search form (light theme, flat).
2. The captcha step with an image and the answer field.
3. The result table with English labels.
4. A terminal showing `curl` step 1 → `428` and step 2 → `200`.

Blur or replace any personal data before posting. Use a synthetic record.

---

## Pinned FAQ

**Is this an official BDRIS tool?**
No. It is an independent open-source project, not affiliated with BDRIS.

**Does it solve the captcha automatically?**
No, and it never will. A human reads the captcha; that is the point.

**Where is the data stored?**
Nowhere. Records are passed through to the caller; captcha sessions are kept in
memory for 10 minutes and then dropped.

**Can I run it on a phone?**
The UI is responsive, but the server is Python. Run it on a PC, a small VPS or
Docker, then open it from your phone on the same network.

**Is there an API key?**
No. Only the two endpoints described in `docs/API.md`.

**Can I use it commercially?**
The code is MIT licensed. Your use of the portal and of personal data must be
lawful and within BDRIS terms — that part is on you.

---

## Sharing checklist

- [ ] Create the repository and push `birthdex/`.
- [ ] Set the description and topics above.
- [ ] Confirm `LICENSE`, `README.md`, `CONTRIBUTING.md` are visible on the repo
      page.
- [ ] Update the repository links if you publish a fork.
- [ ] Tag `v1.0.0` and attach a screenshot or two.
- [ ] Post the English and Bangla versions in the right channels.
- [ ] Pin the FAQ message.
