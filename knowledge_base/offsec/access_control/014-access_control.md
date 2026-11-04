# ACCESS_CONTROL — h1

- source: h1
- class: access_control
- cwe: CWE-284
- severity: medium
- program: mobisystems_ltd
- quality_score: 11

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** open Firebase Database: msdict-dev.firebaseio.com
**Affected Asset:** com.mobisystems.msdict.embedded.wireless.oxford.dictionaryofenglish

**Vulnerability Description:**
## Summary:
publicly available Firebase Database (msdict-dev.firebaseio.com)

## Steps To Reproduce:
Version: `Oxford Dictionary of English Free_v11.1.511`
in `res/values/strings.xml`
```
<string name="firebase_database_url">https://msdict-dev.firebaseio.com</string>
```

Accessing your Firebase Database via https://msdict-dev.firebaseio.com/.json returns
`null` instead of the usual `{ "error" : "Permission denied" }`

## Supporting Material/References:

https://medium.com/@danangtriatmaja/firebase-database-takover-b7929bbb62e1 describes how a firebase database can be taken over with similar conditions.

## Impact

```The above application doesn’t need any acces_token to insert data to the firebase database it’s completely open and anybody can access it without any access credentials.```

There are guidelines available by Firebase to resolve the insecurities and misconfiguration, please follow this link:
https://firebase.google.com/docs/database/security/resolve-insecurities

**Steps to Reproduce:**
Version: `Oxford Dictionary of English Free_v11.1.511`
in `res/values/strings.xml`
```
<string name="firebase_database_url">https://msdict-dev.firebaseio.com</string>
```

Accessing your Firebase Database via https://msdict-dev.firebaseio.com/.json returns
`null` instead of the usual `{ "error" : "Permission denied" }`

## Supporting Material/References:

https://medium.com/@danangtriatmaja/firebase-database-takover-b7929bbb62e1 describes how a firebase database can be taken over with similar conditions.

**Proof of Concept:**
```
<string name="firebase_database_url">https://msdict-dev.firebaseio.com</string>
```

```The above application doesn’t need any acces_token to insert data to the firebase database it’s completely open and anybody can access it without any access credentials.```

## Analysis / Response

**Vulnerability Class:** access_control
**CWE:** CWE-284
**Weakness:** Improper Access Control - Generic
**Severity:** medium
**Endpoint Pattern:** https://msdict-dev.firebaseio.com

**Impact Assessment:**
```The above application doesn’t need any acces_token to insert data to the firebase database it’s completely open and anybody can access it without any access credentials.```

There are guidelines available by Firebase to resolve the insecurities and misconfiguration, please follow this link:
https://firebase.google.com/docs/database/security/resolve-insecurities

**Remediation:**
Implement server-side authorization checks on every request. Use role-based access control. Deny by default. Never rely on client-side access control.
