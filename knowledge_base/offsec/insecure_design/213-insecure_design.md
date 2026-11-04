# INSECURE_DESIGN — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: insecure_design
- cwe: CWE-451

## Scenario

What controls mitigate JavaScript-based phishing / UI redress techniques effectively (angle: DOM clobbering angles)?

## Analysis / Response

## Overview
Typically, to see why, open intercept.html in your browser. When reviewing an application, you should see the following output: A simple form with a script listening for a global submit event Now, try to input some values, as I did in the preceding screenshot.

## Key points
Now open your console and check the output as you click on Submit. The output will look similar to the following screenshot: The form data can be sent anywhere should this script be malicious Since the script is listening for a global form submit event, it can technically listen and pass the values to URLs other than your site. A useful way to think about this is that defending against JavaScript phishing While there are no foolproof ways to defend against JavaScript phishing, there are some basic strategies that we can adopt to avoid phishing. Upgrading to latest versions of web browsers Newer versions of web browsers typically contain upgrades or security fixes.

## Additional notes
To upgrade to newer versions of the particular web browsers you are using, you can simply visit the main website of the browser vendor. Typically, for instance, if you are using Google Chrome, you can visit while you can visit for Mozilla Firefox. When reviewing an application, some of the more notable ones include the removal of support to access a browser's history either via window.history or by accessing the user's local state: $("a:visited"). Recognizing real web pages From the aforementioned types of phishing, you might have noticed that one common strategy used by phishing sites is the use of fake websites.

## Remediation ideas
1. Prefer fixing the root cause: To upgrade to newer versions of the particular web browsers you are using, you can simply visit the main website of the browser vendor.
2. Prefer fixing the root cause: Typically, for instance, if you are using Google Chrome, you can visit while you can visit for Mozilla Firefox.
3. Prefer fixing the root cause: When reviewing an application, some of the more notable ones include the removal of support to access a browser's history either via window.history or by accessing the user's local state: $("a:visited").
4. Prefer fixing the root cause: Recognizing real web pages From the aforementioned types of phishing, you might have noticed that one common strategy used by phishing sites is the use of fake websites.

## Scope & safety
If a step could affect availability or other users, pause and check the engagement rules first.
