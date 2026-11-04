# SQLI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: sqli
- cwe: CWE-943

## Scenario

What is NoSQL injection and how is it different from classic SQL injection?

## Analysis / Response

## Overview
Databases do not always use SQL. NoSQL ("Not Only SQL") databases do not use the SQL language and store data in structures other than tables — such as key-value pairs and graphs. Their query syntax is database-specific and queries are often written in the application's own programming language. Modern NoSQL databases such as **MongoDB**, **Apache CouchDB**, and **Apache Cassandra** are still vulnerable to injection, and these bugs are becoming more common as NoSQL grows in popularity.

## How it differs
Classic SQLi injects into a SQL string. NoSQL injection abuses database-specific operators and the fact that queries are frequently built in the app's language, so payloads often take the form of structured objects/operators rather than SQL keywords.

## MongoDB example
In MongoDB, `Users.find()` returns users matching criteria:

    Users.find({username: 'vickie', password: 'password123'});

If the app builds the query directly from user input:

    Users.find({username: $username, password: $password});

an attacker can submit the password `{$ne: ""}`. With username `admin`, the query becomes:

    Users.find({username: 'admin', password: {$ne: ""}});

`$ne` selects objects whose value is *not equal* to the specified value, so this returns the admin user as long as their password is not an empty string — bypassing authentication and logging the attacker in as admin.

## Why it matters
Because NoSQL operators can change query logic (and in some cases run server-side code), unvalidated input flowing into NoSQL queries can bypass auth, leak data, or worse.
