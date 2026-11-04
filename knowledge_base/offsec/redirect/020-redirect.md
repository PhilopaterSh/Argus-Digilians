# REDIRECT — h1

- source: h1
- class: redirect
- cwe: CWE-601
- severity: medium
- program: brave
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Open redirect found on account.brave.com
**Affected Asset:** account.brave.com

**Vulnerability Description:**
While examining the application's URL redirection functionality, the following vulnerability was discovered:

## What is open redirect
A web application accepts a user-controlled input that specifies a link to an external site, and uses that link in a Redirect. This simplifies phishing attacks.
An http parameter may contain a URL value and could cause the web application to redirect the request to the specified URL. By modifying the URL value to a malicious site, an attacker may successfully launch a phishing scam and steal user credentials. Because the server name in the modified link is identical to the original site, phishing attempts have a more trustworthy appearance.

## Step to reproduce
visit https://account.brave.com//example.com/%2F.. you will redirect to example.com

## POC
{F1446362}

## Fix / prevention
You can prevent redirects to other domains by checking the URL being passed to the redirect function. Make sure all redirect URLs are relative paths – i.e. they start with a single / character. (Note that URLs starting with // will be interpreted by the browser as a protocol agnostic, absolute URL – so they should be rejected too.)

If you do need to perform external redirects, consider whitelisting the individual sites that you permit redirects to.

## Impact

One of the main uses for this vulnerability is to make phishing attacks more credible and effective. When an Open Redirect is used in a phishing attack, the victim receives an email that looks legitimate with a link that points to a correct and expected domain.

Let me know if you have any questions.

thanks & best regards

**Steps to Reproduce:**
visit https://account.brave.com//example.com/%2F.. you will redirect to example.com

**Proof of Concept:**
{F1446362}

## Fix / prevention
You can prevent redirects to other domains by checking the URL being passed to the redirect function. Make sure all redirect URLs are relative paths – i.e. they start with a single / character. (Note that URLs starting with // will be interpreted by the browser as a protocol agnostic, absolute URL – so they should be rejected too.)

If you do need to perform external redirects, consider whitelisting the individual sites that you permit redirects to.

## Analysis / Response

**Vulnerability Class:** redirect
**CWE:** CWE-601
**Weakness:** Open Redirect
**Severity:** medium
**Endpoint Pattern:** https://account.brave.com//example.com/%2F..

**Impact Assessment:**
One of the main uses for this vulnerability is to make phishing attacks more credible and effective. When an Open Redirect is used in a phishing attack, the victim receives an email that looks legitimate with a link that points to a correct and expected domain.

Let me know if you have any questions.

thanks & best regards

**Remediation:**
Validate redirect URLs against an allowlist of permitted domains. Use relative URLs for internal redirects. Never place user input directly in redirect targets.
