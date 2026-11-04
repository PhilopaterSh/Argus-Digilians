# SQLI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: sqli
- cwe: CWE-89

## Scenario

What is a second-order SQL injection and how does it differ from a first-order one?

## Analysis / Response

## First vs second order
Most SQL injections are **first-order**: they happen when an application uses user-submitted input directly in a SQL query, so the payload fires immediately. A **second-order** SQL injection happens when user input is first stored in the database, then later retrieved and used unsafely in a SQL query. Even if the application handles input properly *at submission time*, the bug occurs if it mistakenly treats that stored data as safe when it reads it back out.

## Why it is easy to miss
The vulnerability splits across two requests and often two features. Input that looked harmless (or was even sanitized) on the way in becomes dangerous on the way out, so testing only the submission point will miss it. There is frequently a **time delay** between the malicious input going in and the SQL query that executes it later — which is also why blind/second-order cases can be hard to observe directly.

## Mindset for testing
Treat any value you can store (usernames, profile fields, comments) as a candidate payload carrier, then exercise *other* features that might read that value back into a query. Track where stored data resurfaces.

## Detection aid
Because second-order injections involve a delay, techniques that make the database record the result somewhere (e.g., MySQL's `SELECT ... INTO OUTFILE` writing to a web-accessible path) can help you confirm the injection fired even when you can't see an immediate response difference — only on systems you are authorized to test.
