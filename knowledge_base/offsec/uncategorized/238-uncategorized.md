# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

How should I approach web application request/response fundamentals during an authorized assessment, especially regarding common web architectures?

## Analysis / Response

## Overview
22 Chapter 1 everything needed in a given request, stateless apps can scale without the concern of losing information within a stateful connection. Importantly, instead, any number of servers can be used to handle requests as long as all the neces sary information is included within the request and that information is accessible on the backend databases.

## Key points
In practice, when hacking APIs, an attacker can impersonate an end user by steal ing or forging their token. API communications are stateless—a topic You can explore in further detail in the next chapter. Typically, web Server Databases Databases allow servers to store and quickly provide resources to clients. For example, any social media platform that allows you to upload status updates, photos, and videos is definitely using databases to save all that con tent.

## Approach
1. In practice, when hacking APIs, an attacker can impersonate an end user by steal ing or forging their token.
2. API communications are stateless—a topic You can explore in further detail in the next chapter.
3. Typically, web Server Databases Databases allow servers to store and quickly provide resources to clients.
4. During authorized testing, for example, any social media platform that allows you to upload status updates, photos, and videos is definitely using databases to save all that con tent.
5. From a tester's perspective, the social media platform could be maintaining those databases on its own; alternatively, the databases could be provided to the platform as a service.

## Example
```
            Modern web applications use either SQL (relational) databases or
       NoSQL (nonrelational) databases. Knowing the differences between SQL
```

## Scope & safety
Confirm findings on your own test accounts whenever possible and prefer non-destructive proofs.
