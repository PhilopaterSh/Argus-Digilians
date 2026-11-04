# ACCESS_CONTROL — h1

- source: h1
- class: access_control
- cwe: CWE-284
- severity: low
- program: kubernetes
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Broken Link Hijacking on kubernetes.io Documentation
**Affected Asset:** kubernetes.io

**Vulnerability Description:**
Report Submission Form

## Summary:
Kubernetes docs has Spanish translation available. One of the page of spanish doc has an external reference to a confluence page.
The confluence account was not registered on Atlassian.
So I was able to takeover the page and host the PoC

## Kubernetes Version:
NA

## Component Version:
NA

## Steps To Reproduce:

  1. Go to https://kubernetes.io/es/docs/concepts/workloads/controllers/daemonset/
  2. Search for `Sysdig Agent`
  3. Click on the atlassian link next to that text
  4. You will be redirected to `https://sysdigdocs.atlassian.net/wiki/spaces/Platform),/overview`
  5. Now try opening the confluence account with this url https://sysdigdocs.atlassian.net/wiki/spaces/TAKEOVER/overview
  6. You will see the takeover message

## Supporting Material/References:

- https://sysdigdocs.atlassian.net/wiki/spaces/TAKEOVER/overview

{F1438785}

## Impact

As an attacker, I can host malicious content on the confluence page to misguide the user.
I can also, host details about installing malicious sdk or softwares, which user will think is part of the deployment docs as its referreded in kubernetes.io, this can lead to RCE for users who are referring to this doc

**Steps to Reproduce:**
1. Go to https://kubernetes.io/es/docs/concepts/workloads/controllers/daemonset/
  2. Search for `Sysdig Agent`
  3. Click on the atlassian link next to that text
  4. You will be redirected to `https://sysdigdocs.atlassian.net/wiki/spaces/Platform),/overview`
  5. Now try opening the confluence account with this url https://sysdigdocs.atlassian.net/wiki/spaces/TAKEOVER/overview
  6. You will see the takeover message

## Supporting Material/References:

- https://sysdigdocs.atlassian.net/wiki/spaces/TAKEOVER/overview

{F1438785}

## Analysis / Response

**Vulnerability Class:** access_control
**CWE:** CWE-284
**Weakness:** Improper Access Control - Generic
**Severity:** low
**Endpoint Pattern:** https://kubernetes.io/es/docs/concepts/workloads/controllers/daemonset/

**Impact Assessment:**
As an attacker, I can host malicious content on the confluence page to misguide the user.
I can also, host details about installing malicious sdk or softwares, which user will think is part of the deployment docs as its referreded in kubernetes.io, this can lead to RCE for users who are referring to this doc

**Remediation:**
Implement server-side authorization checks on every request. Use role-based access control. Deny by default. Never rely on client-side access control.
