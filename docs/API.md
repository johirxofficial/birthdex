# BirthDex API reference

Base URL when running locally: `http://localhost:5002`

All endpoints return JSON (`application/json`) except the captcha image.
Every JSON body starts with the same envelope:

```json
{ "status": true, "success": true, "code": 200, "message": "…" }
```

`status` and `success` are always identical booleans. `code` mirrors the HTTP
status. Additional keys depend on the endpoint and the step.

---

## 1. `GET /api/verify` — start a lookup

Opens a portal session and asks for a captcha.

### Query parameters

| Parameter | Required | Description |
|---|---|---|
| `type` | no | `birth` (default) or `death` |
| `number` | yes | 17-digit UBRN (birth) or UDRN (death). Spaces and dashes are ignored |
| `dob` | yes | Date as `YYYY-MM-DD`, `DD-MM-YYYY`, `DD/MM/YYYY`, `YYYY/MM/DD` or `DD.MM.YYYY` |

Aliases: `number` may also be sent as `num`, `ubrn` or `udrn`; `dob` as `date`,
`birth_date` or `death_date`. Parameter names are case-insensitive.

### Example

```bash
curl "http://localhost:5002/api/verify?type=birth&number=19901234567890123&dob=1990-01-01"
```

### `428 Captcha required`

```json
{
  "status": false,
  "success": false,
  "code": 428,
  "message": "Captcha required. Read the captcha image, then repeat the request with captcha_id and captcha.",
  "type": "birth",
  "number": "19901234567890123",
  "dob": "1990-01-01",
  "captcha": {
    "id": "xizdmM5OKWRZrNGPFdyorQ",
    "image_url": "http://localhost:5002/api/captcha/xizdmM5OKWRZrNGPFdyorQ.png",
    "expires_in": 600
  },
  "verify_with": "http://localhost:5002/api/verify?type=birth&number=19901234567890123&dob=1990-01-01&captcha_id=xizdmM5OKWRZrNGPFdyorQ&captcha=%3Cyour+answer%3E"
}
```

Show `captcha.image_url` to a human, collect the answer and continue with
step 2. A session is valid for `expires_in` seconds and can be used **once**.

---

## 2. `GET /api/verify` — submit the captcha

### Additional parameters

| Parameter | Required | Description |
|---|---|---|
| `captcha_id` | yes | `captcha.id` from step 1 (alias: `session_id`) |
| `captcha` | yes | What the human sees in the image (alias: `answer`) |

### Example

```bash
curl "http://localhost:5002/api/verify?type=birth&number=19901234567890123&dob=1990-01-01&captcha_id=xizdmM5OKWRZrNGPFdyorQ&captcha=38"
```

### `200 Record found`

```json
{
  "status": true,
  "success": true,
  "code": 200,
  "message": "Birth record found.",
  "type": "birth",
  "number": "19901234567890123",
  "dob": "1990-01-01",
  "data": {
    "registration_date": "2 January 2008",
    "registration_office": "Example Union Parishad",
    "issuance_date": "2 January 2008",
    "date_of_birth": "1 January 1990",
    "birth_registration_number": "19901234567890123",
    "sex": "MALE",
    "name_bn": "মোঃ রহিম উদ্দিন",
    "name_en": "MD RAHIM UDDIN",
    "birth_place_bn": "ঢাকা",
    "birth_place_en": "DHAKA",
    "mother_name_bn": "রহিমা বেগম",
    "mother_name_en": "RAHIMA BEGUM",
    "mother_nationality_bn": "বাংলাদেশী",
    "mother_nationality_en": "Bangladeshi",
    "father_name_bn": "মোঃ করিম মিয়া",
    "father_name_en": "MD KARIM MIA",
    "father_nationality_bn": "বাংলাদেশী",
    "father_nationality_en": "Bangladeshi"
  }
}
```

Fields that the portal does not publish are simply absent.

### `422 Wrong captcha` — with a fresh captcha

A rejected answer returns `422` **and a new captcha**, so you can retry
immediately:

```json
{
  "status": false,
  "success": false,
  "code": 422,
  "message": "That captcha answer was not accepted. A new captcha is ready.",
  "type": "birth",
  "number": "19901234567890123",
  "dob": "1990-01-01",
  "captcha": { "id": "newid…", "image_url": "http://…/api/captcha/newid….png", "expires_in": 600 },
  "verify_with": "http://…"
}
```

---

## 3. `POST /api/verify`

The same flow with a JSON body (or a form body). Useful for long numbers and
for clients that prefer POST.

```bash
curl -X POST "http://localhost:5002/api/verify" \
  -H "Content-Type: application/json" \
  -d '{"type":"birth","number":"19901234567890123","dob":"1990-01-01"}'
```

```json
{
  "type": "birth",
  "number": "19901234567890123",
  "dob": "1990-01-01",
  "captcha_id": "xizdmM5OKWRZrNGPFdyorQ",
  "captcha": "38"
}
```

---

## 4. `GET /api/captcha/<id>.png`

Serves the captcha image of a pending session.

- `200` with `Content-Type: image/gif` (or `image/png`).
- `410` if the session expired, was used, or never existed.
- `Cache-Control: no-store` is set, because a captcha is single-use.

```bash
curl -o captcha.gif "http://localhost:5002/api/captcha/xizdmM5OKWRZrNGPFdyorQ.png"
```

`captcha.image_url` from step 1 is exactly this URL.

---

## 5. `GET /health`

No authentication, no portal traffic.

```json
{
  "status": true,
  "success": true,
  "code": 200,
  "message": "OK",
  "service": "birthdex",
  "version": "1.0.0",
  "captcha": "manual",
  "sessions": { "active": 0, "capacity": 200, "ttl_seconds": 600 },
  "endpoints": ["/", "/health", "/api/verify", "/api/captcha/<id>.png"]
}
```

---

## Status codes

| Code | When | What to do |
|---|---|---|
| `200` | Record found | Read `data` |
| `400` | Missing/invalid parameters, bad JSON | Fix the request |
| `404` | The portal has no record for this number + date | Stop, report "not found" |
| `410` | Captcha session expired, already used, or unknown | Start again at step 1 |
| `422` | Invalid number/date, future date, or wrong captcha | Fix the input, or use the new captcha |
| `428` | Captcha required | Show `captcha.image_url`, then continue |
| `502` | Portal unreachable or unexpected page | Retry with backoff |
| `504` | Portal timed out | Retry with backoff |
| `500` | Bug in BirthDex | Open an issue with the request details |

---

## Client examples

### JavaScript (browser)

```js
const base = "/api/verify";
const params = new URLSearchParams({ type: "birth", number, dob });

let res = await fetch(`${base}?${params}`);
let body = await res.json();

if (res.status === 428) {
  showImage(body.captcha.image_url);          // human reads it
  // later, with the answer:
  params.set("captcha_id", body.captcha.id);
  params.set("captcha", answer);
  res = await fetch(`${base}?${params}`);
  body = await res.json();
  if (res.status === 200) console.log(body.data);
}
```

### Python

```python
import requests

BASE = "http://localhost:5002/api/verify"
params = {"type": "birth", "number": "19901234567890123", "dob": "1990-01-01"}

step1 = requests.get(BASE, params=params).json()
print("open:", step1["captcha"]["image_url"])

params |= {"captcha_id": step1["captcha"]["id"], "captcha": "38"}
step2 = requests.get(BASE, params=params).json()
print(step2.get("data") or step2["message"])
```

### PowerShell

```powershell
$p = @{ type='birth'; number='19901234567890123'; dob='1990-01-01' }
$r = Invoke-RestMethod -Uri 'http://localhost:5002/api/verify' -Body $p
Start-Process $r.captcha.image_url           # read the image
$p.captcha_id = $r.captcha.id
$p.captcha = Read-Host 'Captcha answer'
Invoke-RestMethod -Uri 'http://localhost:5002/api/verify' -Body $p | ConvertTo-Json -Depth 5
```

---

## Behaviour notes

- **One record per captcha.** After a successful or failed submit the session is
  gone; the next lookup needs a new captcha.
- **Type binding.** A birth captcha cannot be used for a death lookup (`410`).
- **No OCR.** There is deliberately no server-side captcha solving.
- **Be gentle.** A captcha image costs one portal request. Do not loop over
  hundreds of lookups; the upstream portal is a public service.
