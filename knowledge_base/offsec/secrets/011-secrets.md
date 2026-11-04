# SECRETS — h1

- source: h1
- class: secrets
- cwe: CWE-200
- severity: critical
- program: h1-ctf
- quality_score: 10

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** [h1-415 2020] Multiple chained vulnerabilities lead to leaking secret document
**Affected Asset:** h1-415.h1ctf.com

**Vulnerability Description:**
A critical-severity vulnerability was found that could allow an attacker to exploit a secrets weakness. Specifically:

Hi!

# Summary
Multiple chained vulnerabilities lead to leaking secret documents.

Improper sanitization in registration allows an attacker to create a QR recover code for any email address. This leads to an account takeover.

Using that technique on jobert's account, attacker can access the support chat functionality. This endpoint, besides some meaningful conversation, is vulnerable to Blind XSS.

Blind XSS leaks an admin page that can change the name of any user, knowing the `user_id`. Abusing this vulnerability an attacker can change his name to a malicious payload and run it through the PDF converter. An attacker can then leak the secret documents processed by the converter.

The secret document contains the following highly classified flag: `h1ctf{y3s_1m_c0sm1c_n0w}`

# Story

My journey consists of two almost sleepless nights, skipping two days of gym, drinking hot chocolate late at night and praying for cosmic bugs.

## 0. Recon

I begin by proceeding to recon the application from all angles and noting everything in a document. I learned that from [ippsec's videos](https://ippsec.rocks/), small shout out.

Some interesting bits I observed are:

After you register, you get a beautiful QR Code, specially made for you, that you might want to save. It contains the email address (hex encoded) and a big token, which may be a hash of something (email, id, username, name, [random stuff](https://dilbert.com/strip/[REDACTED_PHONE])), may not be a hash of something.

There is a PDF convertor. Also it converts the image to a thumbnail. I'll go an limb here and say that the PDF is what we should focus on, based on: gut feeling, the fact that nahamsec has a pinned post about PDF generators, and the fact that he did say that, on discord.

{F688269}

You can find jobert's email on the first page if you're reading the source code. It is `[REDACTED_EMAIL]`. Does that mean we will find some cosmic bugs today? I hope so.

{F688270}

While logging out I noticed an `return_url` parameter for login. That's pretty cool, in my experience, it allows for open redirect. This one kinda does, but not really. It's a POST based open redirect and you need the CSRF Token. I tried XSS, SSTI and everything else in between but no luck.

I tested most inputs with the following polyglot I found on Twitter a while ago `App"/><s>'${7*6}[!--+*)(&`. I like it because most of the WAFs don't get triggered by it. Changing my name with this, I saw that `<>{}` are being removed. Basically `App"/><s>'${7*6}[!--+*)(&` got turned into `App"/s'$7*6[!--+*)(&`. Interesting fact.

On the user settings page, there was an `use

## Analysis / Response

**Vulnerability Class:** secrets
**CWE:** CWE-200
**Weakness:** None
**Severity:** critical
**Endpoint Pattern:** https://ippsec.rocks/),

**Impact Assessment:**
It's pretty bad.

#bountyplz
#bountyplz
#bountyplz

**Remediation:**
Remove hardcoded secrets from source code. Use environment variables or secret management services. Rotate exposed credentials immediately.
