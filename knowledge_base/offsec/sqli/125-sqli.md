# SQLI — portswigger_labs_sft

- source: portswigger_labs_sft
- class: sqli
- cwe: CWE-943

## Scenario

Teach me the official solution for this PortSwigger Academy lab.

Lab: Bypassing GraphQL brute force protections
Topic: GraphQL API vulnerabilities
Level: Practitioner

Scenario:
The user login mechanism for this lab is powered by a GraphQL API. The API endpoint has a rate limiter that returns an error if it receives too many requests from the same origin in a short space of time.

To solve the lab, brute force the login mechanism to sign in as `carlos`. Use the list of authentication lab passwords as your password source.

Learn more about Working with GraphQL in Burp Suite.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers GraphQL API vulnerabilities: "Bypassing GraphQL brute force protections".

## Solution steps

1. In Burp's browser, access the lab and select My account.
2. Attempt to log in to the site using incorrect credentials.
3. In Burp, go to Proxy > HTTP history. Note that login requests are sent as a GraphQL mutation.
4. Right-click the login request and select Send to Repeater.
5. In Repeater, attempt some further login requests with incorrect credentials. Note that after a short period of time the API starts to return a rate limit error.
6. In the GraphQL tab, craft a request that uses aliases to send multiple login mutations in one message. See the tip in this lab for a method that makes this process less time-consuming. Bear the following in mind when constructing your request: The list of aliases should be contained within a `mutation {}` type. Each aliased mutation should have the username `carlos` and a different password from the authentication list. If you are modifying the request that you sent to Repeater, delete the variable dictionary and `operationName` field from the request before sending. You can do this from Repeater's Pretty tab. Ensure that each alias requests the `success` field, as shown in the simplified example below: ` mutation { bruteforce0:login(input:{password: "123456", username: "carlos"}) { token success } bruteforce1:login(input:{password: "password", username: "carlos"}) { token success } ... bruteforce99:login(input:{password: "12345678", username: "carlos"}) { token success } } `
7. Click Send.
8. Notice that the response lists each login attempt and whether its login attempt was successful.
9. Use the search bar below the response to search for the string `true`. This indicates which of the aliased mutations was able to successfully log in as `carlos`.
10. Check the request for the password that was used by the successful alias.
11. Log in to the site using the `carlos` credentials to solve the lab.

## Vulnerability note

Underlying issue: GraphQL API vulnerabilities (CWE-943). Enforce authz per field/resolver, limit query depth/complexity, and disable introspection in production if appropriate.
