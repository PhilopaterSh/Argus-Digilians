# INFO_DISCLOSURE — h1

- source: h1
- class: info_disclosure
- cwe: CWE-359
- severity: medium
- program: brave
- quality_score: 10

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Persistent user tracking is possible using window.caches, by avoiding Brave Shields
**Affected Asset:** https://github.com/brave/brave-ios

**Vulnerability Description:**
## Summary:

The recent version of iOS 15 introduced `window.caches` in WKWebView. It provides a persistent cache for web pages, and is also potentially usable for user tracking.
The current [CookieControl.js](https://github.com/brave/brave-ios/blob/development/Client/Frontend/UserContent/UserScripts/CookieControl.js) disables cookie, localStorage and sessionStorage, but it doesn't disable `window.caches`, so it allows client-side user tracking by `window.caches` even when cookie brocker is enabled.

## Products affected: 

* Brave for iOS Version [REDACTED_PHONE])
* iPhone 8 with iOS 15.6

## Steps To Reproduce:

* Enable Brave Shields and block all cookies
* Visit https://csrf.jp/2022/caches.php
* Push "Set Tracking ID" button, then your tracking ID is set to window.caches
* Push "Get Tracking ID" button, then you can confirm your tracking ID that was set above
* Close your browser and visit the above page again
* Push "Get Tracking ID" button, then you can see your tracking ID again

## Supporting Material/References:

  * Attached is a movie file that demonstrate the above steps to reproduce.

## Impact

As witten in summary, client-side user tracking by `window.caches` is possible even when cookie brocker is enabled.

**Steps to Reproduce:**
* Enable Brave Shields and block all cookies
* Visit https://csrf.jp/2022/caches.php
* Push "Set Tracking ID" button, then your tracking ID is set to window.caches
* Push "Get Tracking ID" button, then you can confirm your tracking ID that was set above
* Close your browser and visit the above page again
* Push "Get Tracking ID" button, then you can see your tracking ID again

## Supporting Material/References:

  * Attached is a movie file that demonstrate the above steps to reproduce.

## Analysis / Response

**Vulnerability Class:** info_disclosure
**CWE:** CWE-359
**Weakness:** Privacy Violation
**Severity:** medium
**Endpoint Pattern:** https://github.com/brave/brave-ios/blob/development/Client/Frontend/UserContent/UserScripts/CookieControl.js)

**Impact Assessment:**
As witten in summary, client-side user tracking by `window.caches` is possible even when cookie brocker is enabled.

**Remediation:**
Remove sensitive data from error messages, headers, and responses. Implement proper access controls. Disable debug modes in production.
