# CRYPTO_WEAK — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: crypto_weak
- cwe: CWE-327

## Scenario

How should I approach common web security protocols (TLS, encoding, crypto basics) during an authorized assessment, especially regarding encoding vs encryption?

## Analysis / Response

## Overview
Typically, in a typical simple CORS request, the following sequence happens: Request: – Origin A Response: – Origin B 1. When reviewing an application, origin A attempts to access the home page of a CDN running at origin B, 2.

## Key points
When reviewing an application, origin A sends a GET request to the Origin B web server. Typically, the Origin B server responds with Access-Control-Allow-Origin. URL encoding – percent encoding In this section, I'll explain percent encoding, which is a commonly used encoding technique to encode URLs. URL encoding is a way in which certain characters are encoded or substituted by % followed by the hexadecimal equivalent of the character.

## Approach
1. When reviewing an application, origin A sends a GET request to the Origin B web server.
2. Typically, the Origin B server responds with Access-Control-Allow-Origin.
3. Typically, uRL encoding – percent encoding In this section, I'll explain percent encoding, which is a commonly used encoding technique to encode URLs.
4. URL encoding is a way in which certain characters are encoded or substituted by % followed by the hexadecimal equivalent of the character.
5. Typically, developers often use encoding because there are certain cases when an intended character or representation is sent to the server but when received, the character changes or gets misinterpreted because of transport issues.

## Example
```
    Content-Type: text/html; charset=utf-8
       http://cdn.prakharprasad.com, using CORS.
```

## Scope & safety
If a step could affect availability or other users, pause and check the engagement rules first.
