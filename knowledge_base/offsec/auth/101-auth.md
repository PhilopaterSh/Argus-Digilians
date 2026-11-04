# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Scenario: during a pentest I suspect OAuth 2.0 security issues. How do I confirm and demonstrate it? Please emphasize token leakage [Ch 10: OAuth 2.0 Security]?

## Analysis / Response

## Overview
Typically, hijacking the OAuth flow – fiddling with redirect URI By now, some of you may be aware of the inherent risks involved in using redirect_uri in a grant situation where it can be made to redirect to a different location than the one allowed, thereby hijacking the access tokens. From a tester's perspective, the beauty of OAuth is that once an application is granted access, the authorization server will never display the prompt again, in case of reattempts by the client application (unless the scope varies from the ones which already exist).

## Key points
A useful way to think about this is that this opens a wide door: by hijacking the redirect_uri we can simply get the access tokens for that client. If the client is a popular client and has lots of permissions (scopes) already granted, we can use different tricks to fool the authorization server into believing that the redirect_uri provided in the grant request link is a valid one as in application configuration. Let's assume there is an OAuth application with lots of scopes already granted, and we are interested in hijacking redirect_uri for profit. Typically, the application is set to allow only redirect_uri =

## Approach
1. A useful way to think about this is that this opens a wide door: by hijacking the redirect_uri we can simply get the access tokens for that client.
2. From a tester's perspective, if the client is a popular client and has lots of permissions (scopes) already granted, we can use different tricks to fool the authorization server into believing that the redirect_uri provided in the grant request link is a valid one as in application configuration.
3. Let's assume there is an OAuth application with lots of scopes already granted, and we are interested in hijacking redirect_uri for profit.
4. Typically, the application is set to allow only redirect_uri =.
5. Then we can use tricks like these to circumvent the checks and hijack the tokens to our (hijacker's) domain or file.

## Scope & safety
If a step could affect availability or other users, pause and check the engagement rules first.
