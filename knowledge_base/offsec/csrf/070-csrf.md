# CSRF — h1

- source: h1
- class: csrf
- cwe: CWE-352
- severity: medium
- program: lab45
- quality_score: 11

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** CSRF on https://apps.topcoder.com/wiki/users/editmyprofile.action
**Affected Asset:** apps.topcoder.com

**Vulnerability Description:**
## Summary:
Hi :) There is a CSRF on changing user details.

## Steps To Reproduce:
There is no CSRF token or anything like that on https://apps.topcoder.com/wiki/users/editmyprofile.action . I added the poc html file below. When someone opens this html file, or we can add it into our website, victim's name and information will change.

Note: This only works to signed-in users. Because unauthorized users cannot upload attachments. There is a mistake on https://apps.topcoder.com/wiki/login.action now. If you encounter an error, you can login on main site (https://accounts.topcoder.com/member) then try.

## Impact

An attacker can force other users to change their name and  informations without their knowledge.

**Steps to Reproduce:**
There is no CSRF token or anything like that on https://apps.topcoder.com/wiki/users/editmyprofile.action . I added the poc html file below. When someone opens this html file, or we can add it into our website, victim's name and information will change.

Note: This only works to signed-in users. Because unauthorized users cannot upload attachments. There is a mistake on https://apps.topcoder.com/wiki/login.action now. If you encounter an error, you can login on main site (https://accounts.topcoder.com/member) then try.

## Analysis / Response

**Vulnerability Class:** csrf
**CWE:** CWE-352
**Weakness:** Cross-Site Request Forgery (CSRF)
**Severity:** medium
**Endpoint Pattern:** https://apps.topcoder.com/wiki/users/editmyprofile.action

**Impact Assessment:**
An attacker can force other users to change their name and  informations without their knowledge.

**Remediation:**
Implement anti-CSRF tokens on all state-changing operations. Use the SameSite cookie attribute. Verify Origin and Referer headers.
