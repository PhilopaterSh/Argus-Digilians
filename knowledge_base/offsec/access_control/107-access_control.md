# ACCESS_CONTROL — h1

- source: h1
- class: access_control
- cwe: CWE-16
- severity: medium
- program: openmage
- quality_score: 11

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** No error thrown when IDOR attempted while editing address
**Affected Asset:** demo.openmage.org

**Vulnerability Description:**
## Summary:
demo.openmage.org application having features to add, edit and delete addresses. When a user tries to edit the address of another user, the server adds a new address with a new id on the attacker's account. By sending it to an intruder, an attacker may cause Dos.

## Steps To Reproduce:

  1. Create two user accounts demo.openmage.org with different emails
  2. Add addresses on both accounts
  3. Edit the address on account 1 and capture the request on burp and send it to the repeater
  4. Replace the ID of the address on both GET request and referee header with the ID of the address of the account 2
  5. Submit the request, Now you can see a new address is added on account 1 with a new ID.
(here, when an attacker try to edit the address of another user, the server should not create new address)
  6. Now Send the same request to intruder with the id of the address of the victim, and set payload as null byte
  7. Start attack with min 60 threads
  8. Now you can see many addresses is added on user account 1. and soon you will see 503 Error code

## Supporting Material/References:


  * {F1169693}

## Impact

* It may cause  Dos

**Steps to Reproduce:**
1. Create two user accounts demo.openmage.org with different emails
  2. Add addresses on both accounts
  3. Edit the address on account 1 and capture the request on burp and send it to the repeater
  4. Replace the ID of the address on both GET request and referee header with the ID of the address of the account 2
  5. Submit the request, Now you can see a new address is added on account 1 with a new ID.
(here, when an attacker try to edit the address of another user, the server should not create new address)
  6. Now Send the same request to intruder with the id of the address of the victim, and set payload as null byte
  7. Start attack with min 60 threads
  8. Now you can see many addresses is added on user account 1. and soon you will see 503 Error code

## Supporting Material/References:


  * {F1169693}

## Analysis / Response

**Vulnerability Class:** access_control
**CWE:** CWE-16
**Weakness:** Misconfiguration
**Severity:** medium

**Impact Assessment:**
* It may cause  Dos

**Remediation:**
Implement server-side authorization checks on every request. Use role-based access control. Deny by default. Never rely on client-side access control.
