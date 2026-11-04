# RESOURCE — h1

- source: h1
- class: resource
- cwe: CWE-400
- severity: informational
- program: nextcloud
- quality_score: 10

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Uploading large avatar images cause excessive CPU usage
**Affected Asset:** nextcloud/3rdparty

**Vulnerability Description:**
How to reproduce:
- Create an account on any server running Nextcloud 13 or 14.
- Open the personal settings.
- Upload a large image as avatar (tested with a 4032x3024 PNG image of about 14.5 MB).
- Keep the selected area in the popup and save the avatar.
- Notice that the avatar area shows the spinner and doesn't show the avatar.
- One of your php-fpm processes on the server runs with 100% CPU.
- Reload the browser and the avatar is visible - the php-fpm process is still at 100% CPU.
- Repeat uploading the image as avatar until all php-fpm processes are at 100% CPU or the server is completely overloaded.
- This doesn't resolve itself even after a couple of minutes.

This applies to Nextcloud 13 and 14. The issue is fixed in Nextcloud 15 and the fix should be backported to all supported versions of Nextcloud.

The cause for the issue is the 3rdparty VCard code that splits the property values at 75 characters, the fix for Nextcloud 15 is here:
https://github.com/nextcloud/3rdparty/commit/085494c2ad5c3757f9f1c11945f786d63fb2d40f#diff-0d23de9452f6235135a046b1011b5c30

## Impact

An attacker could completely overload a server, cause it to stop responding to any more requests.

**Steps to Reproduce:**
- Create an account on any server running Nextcloud 13 or 14.
- Open the personal settings.
- Upload a large image as avatar (tested with a 4032x3024 PNG image of about 14.5 MB).
- Keep the selected area in the popup and save the avatar.
- Notice that the avatar area shows the spinner and doesn't show the avatar.
- One of your php-fpm processes on the server runs with 100% CPU.
- Reload the browser and the avatar is visible - the php-fpm process is still at 100% CPU.
- Repeat uploading the image as avatar until all php-fpm processes are at 100% CPU or the server is completely overloaded.
- This doesn't resolve itself even after a couple of minutes.

This applies to Nextcloud 13 and 14. The issue is fixed in Nextcloud 15 and the fix should be backported to all supported versions of Nextcloud.

The cause for the issue is the 3rdparty VCard code that splits the property values at 75 characters, the fix for Nextcloud 15 is here:
https://github.com/nextcloud/3rdparty/commit/085494c2ad5c3757f9f1c11945f786d63fb2d40f#diff-0d23de9452f6235135a046b1011b5c30

## Analysis / Response

**Vulnerability Class:** resource
**CWE:** CWE-400
**Weakness:** Uncontrolled Resource Consumption
**Severity:** informational
**Endpoint Pattern:** https://github.com/nextcloud/3rdparty/commit/085494c2ad5c3757f9f1c11945f786d63fb2d40f#diff-0d23de9452f6235135a046b1011b5c30

**Impact Assessment:**
An attacker could completely overload a server, cause it to stop responding to any more requests.

**Remediation:**
Implement rate limiting and request size limits. Set timeouts on all operations. Use circuit breakers for downstream services. Validate input complexity.
