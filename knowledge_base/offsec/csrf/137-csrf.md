# CSRF — h1

- source: h1
- class: csrf
- cwe: CWE-352
- severity: medium
- program: unikrn
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** CSRF logs the victim into attacker's account
**Affected Asset:** unikrn.com

**Vulnerability Description:**
Description: There is no session validation while logging in which leads to csrf.

Steps To Reproduce:

  1. Create a CSRF login POC using the following code.
<html>
  <body>
    <form action="https://unikrn.com/apiv1/login" method="POST">
	  <input type="hidden" name="usr" value="[email]">
	  <input type="hidden" name="pwd" value="[password]">
      <input type="submit" value="Submit request" />
    </form>
  </body>
</html>
  
  2. Replace the email and password with the valid credentials.
  3. Send the script to the victim to make them click.

References:

1. You've rewarded a guy for login csrf here: https://hackerone.com/reports/293016
2. Impact of login csrf on a company: https://support.detectify.com/customer/portal/articles/1969819-login-csrf

## Impact

1. Log any victim into the attacker account, the attacker can create a similar account profile as the victim - with some information missing, and then social-engineering (e.g. email) user to provide personal information or current password and can also monitor the victim activities. 
2. Also the victim may add his paymet info in the attackers account unknowingly using your wallet feature.

The hacker selected the **Cross-Site Request Forgery (CSRF)** weakness. This vulnerability type requires contextual information from the hacker. They provided the following answers:

**URL**
https://unikrn.com/apiv1/login

**Verified**
Yes

**Can a victim be forced to perform a sensitive state-change operation unknowningly?**
Yes

**What state-change operation can be performed?**
Any user details.

This issue falls under Cross-Site Request Forgery (CSRF) and carries a medium severity rating based on its exploitability and potential impact.

**Steps to Reproduce:**
1. Create a CSRF login POC using the following code.
<html>
  <body>
    <form action="https://unikrn.com/apiv1/login" method="POST">
	  <input type="hidden" name="usr" value="[email]">
	  <input type="hidden" name="pwd" value="[password]">
      <input type="submit" value="Submit request" />
    </form>
  </body>
</html>
  
  2. Replace the email and password with the valid credentials.
  3. Send the script to the victim to make them click.

References:

1. You've rewarded a guy for login csrf here: https://hackerone.com/reports/293016
2. Impact of login csrf on a company: https://support.detectify.com/customer/portal/articles/1969819-login-csrf

## Analysis / Response

**Vulnerability Class:** csrf
**CWE:** CWE-352
**Weakness:** Cross-Site Request Forgery (CSRF)
**Severity:** medium
**Endpoint Pattern:** https://unikrn.com/apiv1/login

**Impact Assessment:**
1. Log any victim into the attacker account, the attacker can create a similar account profile as the victim - with some information missing, and then social-engineering (e.g. email) user to provide personal information or current password and can also monitor the victim activities. 
2. Also the victim may add his paymet info in the attackers account unknowingly using your wallet feature.

The hacker selected the **Cross-Site Request Forgery (CSRF)** weakness. This vulnerability type requires contextual information from the hacker. They provided the following answers:

**URL**
https://unikrn.com/apiv1/login

**Verified**
Yes

**Can a victim be forced to perform a sensitive state-change operation unknowningly?**
Yes

**What state-change operation can be performed?**
Any user details.

**Remediation:**
Implement anti-CSRF tokens on all state-changing operations. Use the SameSite cookie attribute. Verify Origin and Referer headers.
