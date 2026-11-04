# CSRF — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: csrf
- cwe: CWE-352

## Scenario

What controls mitigate cross-site request forgery (CSRF) effectively (angle: SameSite cookies)?

## Analysis / Response

## Overview
Here, you will go quickly over the techniques for protection. In practice, creating your own app ID and app secret – OAuth-styled Creating your own app ID and app secret is similar to what the major Internet companies are doing right now: we require developers to sign up for developing accounts and to attach an application ID and secret key for each of the apps.

## Key points
Have a look at the following screenshot: The same thing with Facebook; Facebook requires you to sign up, and it assigns app ID and app secret Checking the Origin header Simply put, you want to check where the request is coming from. This is a technique where you can check the Origin header. The Origin header, in layman's terms, refers to where the request is coming from. From a tester's perspective, if the website URL does not match with the one that is being registered, you can reject this request.

## Remediation ideas
1. Prefer fixing the root cause: During authorized testing, have a look at the following screenshot: The same thing with Facebook; Facebook requires you to sign up, and it assigns app ID and app secret Checking the Origin header Simply put, you want to check where the request is coming from.
2. Prefer fixing the root cause: This is a technique where you can check the Origin header.
3. Prefer fixing the root cause: The Origin header, in layman's terms, refers to where the request is coming from.
4. Prefer fixing the root cause: From a tester's perspective, if the website URL does not match with the one that is being registered, you can reject this request.

## Scope & safety
Only test systems you are explicitly authorized to assess, and stay within the agreed scope.
