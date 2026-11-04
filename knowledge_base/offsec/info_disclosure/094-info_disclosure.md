# INFO_DISCLOSURE — h1

- source: h1
- class: info_disclosure
- cwe: CWE-200
- severity: medium
- program: security
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Possible PII Disclosure via Advanced Vetting Process - ██████
**Affected Asset:** hackerone.com

**Vulnerability Description:**
**Description:**
It might be possible to extract PII from Hackerone Users' via **HackerOne Advanced Vetting** process. As I tested this functionality from a sandboxed program, I'm not fully sure. An unauthozied user can download the **Advanced Vetting** term acceptance data from the ███ link. The csv file contains `Name of Finder,Username,Advanced Finder Vetting,Address (optional),Finder's Country,Date signed`. Also it has been observed that any logged-in user can download the terms_acceptance_data.
███████

### Steps To Reproduce
1.  Login to the H1 account.
2.  Go to ████ & ████ URLs. The csv file will be contains the Advanced Vetting acceptance details. Even though you don't have access to `███████` & `████████` programs. 

██████
█████████

### HTTP Request
```js
GET /█████/terms_acceptance_data.csv HTTP/2
Host: hackerone.com
Cookie: [REDACTED_COOKIE]
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36
```

## Impact

Possible PII Leakage.

**Steps to Reproduce:**
1.  Login to the H1 account.
2.  Go to ████ & ████ URLs. The csv file will be contains the Advanced Vetting acceptance details. Even though you don't have access to `███████` & `████████` programs. 

██████
█████████

### HTTP Request
```js
GET /█████/terms_acceptance_data.csv HTTP/2
Host: hackerone.com
Cookie: [REDACTED_COOKIE]
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36
```

**Proof of Concept:**
```js
GET /█████/terms_acceptance_data.csv HTTP/2
Host: hackerone.com
Cookie: [REDACTED_COOKIE]
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36
```

## Analysis / Response

**Vulnerability Class:** info_disclosure
**CWE:** CWE-200
**Weakness:** Information Disclosure
**Severity:** medium
**Endpoint Pattern:** GET /█████/terms_acceptance_data.csv

**Impact Assessment:**
Possible PII Leakage.

**Remediation:**
Remove sensitive data from error messages, headers, and responses. Implement proper access controls. Disable debug modes in production.
