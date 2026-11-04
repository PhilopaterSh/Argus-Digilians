# SSTI — gapfill_synthetic

- source: gapfill_synthetic
- class: ssti

## Scenario

A templating endpoint reflects `name`. Input `{{7*7}}` renders `49`; `${7*7}` renders literally. Which engine and how far does it go?

## Analysis / Response

<think>
`{{7*7}}`→49 but `${7*7}` literal narrows it to a curly-brace engine (Jinja2/Twig), not Freemarker/JSP-EL (dollar). To split Jinja2 vs Twig I probe object internals: `{{''.__class__}}` works in Jinja2 (Python). If a Python type reflects, it's Jinja2 and I can walk the object graph to os.system → RCE. Critical if server-side; must confirm it's SSTI not client-side template injection (different, XSS-ish impact). `49` alone is only 'confirmed injection', not yet RCE.
</think>

**Server-Side Template Injection — Jinja2 (Python).**

**Fingerprint:** `{{7*7}}`→49, `${7*7}` literal (rules out EL/Freemarker); `{{''.__class__.__mro__[1].__subclasses__()}}` returns Python classes → Jinja2.

**PoC → RCE:**
```
{{ cycler.__init__.__globals__.os.popen('id').read() }}
```
returns `uid=33(www-data)`.

**Root cause:** user input concatenated into template *source* and rendered (`Template("Hi "+name).render()`), so template syntax is evaluated.

**Impact:** arbitrary code execution on the app server.

**Severity:** Critical — AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H = 9.8.

**Fix:** never build templates from input — render a static template with user data as a context variable: `render_template("hi.html", name=name)`. SandboxedEnvironment has known escapes; avoid dynamic templates entirely.
**Edge case:** if `__class__` is sandbox-blocked, the finding may cap at info-disclosure — verify before rating critical.
