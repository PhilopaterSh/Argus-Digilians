# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Scenario: during a pentest I suspect end-to-end API testing methodology. How do I confirm and demonstrate it? Please emphasize regression of API fixes [Ch 11: API Testing Methodology]?

## Analysis / Response

## Overview
But in this bug, I was able to demonstrate that the DELETE method was missing a permission check of manage_pages scope, so any application with just the publish_pages scope (permission) was able to delete photos from a page. During authorized testing, but an application can delete only those photos which have been created by the application.

## Key points
An application cannot delete photos that are posted by the user or are posted by another application. Let's see how to delete a photo from a page using a user access token with publish_ pages permission but without manage_pages permission: Request Response "success":true Refer to Importantly, here, it is worth noting that the POST request method on the same endpoint enforced a manage_pages permission check, while only the DELETE method was missing the permission check. Note From these two bugs, you learned that you need to think in terms of an application and try to escalate privileges as an application and only Roles based testing We have already studied page roles applied to our targeted API (Graph API), using the information about roles implemented on a Facebook Page.

## Approach
1. An application cannot delete photos that are posted by the user or are posted by another application.
2. Importantly, let's see how to delete a photo from a page using a user access token with publish_ pages permission but without manage_pages permission: Request Response "success":true Refer to.
3. Importantly, here, it is worth noting that the POST request method on the same endpoint enforced a manage_pages permission check, while only the DELETE method was missing the permission check.
4. Typically, note From these two bugs, you learned that you need to think in terms of an application and try to escalate privileges as an application and only Roles based testing We have already studied page roles applied to our targeted API (Graph API), using the information about roles implemented on a Facebook Page.
5. Typically, you can study a few bugs that were exploited for real on Graph API.

## Example
```
    DELETE /{photo-id}
    {
    }
                 concentrate on scope (permissions) for that particular endpoint.
```

## Scope & safety
Confirm findings on your own test accounts whenever possible and prefer non-destructive proofs.
