# CMDI — h1

- source: h1
- class: cmdi
- cwe: CWE-22
- cve: ['CVE-2018-3758']
- severity: critical
- program: nodejs-ecosystem
- quality_score: 13

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Unrestricted file upload (RCE)
**Affected Asset:** express-cart

**Vulnerability Description:**
I would like to report an unrestricted file upload in express-cart.

It allows a user with administrative privileges to upload a file to any path.

# Module

**module name:** express-cart
**version:** 1.1.5
**npm page:** `https://www.npmjs.com/package/express-cart`

## Module Description

expressCart is a fully functional shopping cart built in Node.js (Express, MongoDB) with Stripe, PayPal and Authorize.net payments.

# Vulnerability

## Vulnerability Description

A privileged user can use the upload functionality to gain access to the server.

The application offers the possibility of uploading product images. However, there are many problems with the way it handles these uploads.

Firstly, it uses a path provided by the user. This path is not validated, therefore, it would allow the user to upload the file to any path on the hosting server.

Secondly, it does not restrict the type of the file being uploaded, therefore, it would allow the user to upload a malicious file to gain access to the server.

Finally, it does not restrict the size of the file. This would allow to easily exhaust the host resources and consequently produce a DoS.
  
## Steps To Reproduce:

There are many ways this vulnerability could be exploited. Supposing our goal would be to establish access to the host machine, we could replace the *app.js* file with a malicious JavaScript that would give us a web shell.

Once you have administrator privileges you can use a request similar to:

```
POST /admin/file/upload HTTP/1.1
Host: localhost:1111
Referer: http://localhost:1111/
Content-Type: multipart/form-data; boundary=---------------------------[REDACTED_PHONE]
Cookie: [REDACTED_COOKIE]

-----------------------------[REDACTED_PHONE]
Content-Disposition: form-data; name="upload_file"; filename="app.js"
Content-Type: image/png

[MALICIOUS_JAVASCRIPT]
-----------------------------[REDACTED_PHONE]
Content-Disposition: form-data; name="productId"

5ae2228d995e3e5d7c96474d
-----------------------------[REDACTED_PHONE]
Content-Disposition: form-data; name="directory"

../../
-----------------------------[REDACTED_PHONE]
Content-Disposition: form-data; name="saveButton"

-----------------------------[REDACTED_PHONE]--
```

# Wrap up

- I contacted the maintainer to let them know: [N] 
- I opened an issue in the related repository: [N]

## Impact

This vulnerability would allow a privileged user to gain access in the hosting machine.

**Steps to Reproduce:**
There are many ways this vulnerability could be exploited. Supposing our goal would be to establish access to the host machine, we could replace the *app.js* file with a malicious JavaScript that would give us a web shell.

Once you have administrator privileges you can use a request similar to:

```
POST /admin/file/upload HTTP/1.

## Analysis / Response

**Vulnerability Class:** cmdi
**CWE:** CWE-22
**Weakness:** Path Traversal
**Severity:** critical
**Endpoint Pattern:** POST /admin/file/upload

**Impact Assessment:**
This vulnerability would allow a privileged user to gain access in the hosting machine.

**Remediation:**
Avoid passing user input to system commands. Use language-native APIs instead of shell execution. If unavoidable, use strict allowlists for permitted values.
