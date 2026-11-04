# ACCESS_CONTROL — h1

- source: h1
- class: access_control
- cwe: CWE-284
- severity: medium
- program: lovable-vdp
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Users can change project visibility which requires high subscription by just changing request body
**Affected Asset:** lovable.dev

**Vulnerability Description:**
## Summary:
A Broken Access Control vulnerability allows users to change project visibility — a feature restricted to higher subscription tiers — by simply modifying the request body of visibility to Personal or Workspace. This bypasses subscription checks, enabling unauthorized access to premium functionality

## Steps To Reproduce:
1. On the burp, enable intercept
2. On Lovabl, write anything to build a project
3. Click create and go to burp to endpoint `https://lovable-api.com/workspaces/{YOUR-WORKSPACE-ID}/projects`
4. On the body of the request change the visibility to Personal or Workspace which requires paid subscription
```
{"description":"landing view","visibility":"Personal","initial_message":{"id":"umsg_01k6qkw83ze07t9f7m9p3jabs9","message":"landing view","files":[],"optimisticImageUrls":[],"chat_only":false,"agent_mode_enabled":false,"ai_message_id":"aimsg_01k6qkw841e07t9f7ytpghd6bs"}}
```
5. Send the request, 201 Created response and the project is now personal or workspace without any restrictions

{F4856401}

## POC Video
{F4856412}

## Impact

- Users can access resources, features, or content they did not pay for
- Direct revenue loss to the company since attackers can use premium features without subscription/payment.

**Steps to Reproduce:**
1. On the burp, enable intercept
2. On Lovabl, write anything to build a project
3. Click create and go to burp to endpoint `https://lovable-api.com/workspaces/{YOUR-WORKSPACE-ID}/projects`
4. On the body of the request change the visibility to Personal or Workspace which requires paid subscription
```
{"description":"landing view","visibility":"Personal","initial_message":{"id":"umsg_01k6qkw83ze07t9f7m9p3jabs9","message":"landing view","files":[],"optimisticImageUrls":[],"chat_only":false,"agent_mode_enabled":false,"ai_message_id":"aimsg_01k6qkw841e07t9f7ytpghd6bs"}}
```
5. Send the request, 201 Created response and the project is now personal or workspace without any restrictions

{F4856401}

## POC Video
{F4856412}

**Proof of Concept:**
```
{"description":"landing view","visibility":"Personal","initial_message":{"id":"umsg_01k6qkw83ze07t9f7m9p3jabs9","message":"landing view","files":[],"optimisticImageUrls":[],"chat_only":false,"agent_mode_enabled":false,"ai_message_id":"aimsg_01k6qkw841e07t9f7ytpghd6bs"}}
```

## Analysis / Response

**Vulnerability Class:** access_control
**CWE:** CWE-284
**Weakness:** Improper Access Control - Generic
**Severity:** medium
**Endpoint Pattern:** https://lovable-api.com/workspaces/{YOUR-WORKSPACE-ID}/projects

**Impact Assessment:**
- Users can access resources, features, or content they did not pay for
- Direct revenue loss to the company since attackers can use premium features without subscription/payment.

**Remediation:**
Implement server-side authorization checks on every request. Use role-based access control. Deny by default. Never rely on client-side access control.
