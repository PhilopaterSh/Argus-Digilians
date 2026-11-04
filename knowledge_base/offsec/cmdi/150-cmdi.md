# CMDI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: cmdi
- cwe: CWE-78

## Scenario

From Chapter 8 (Strings and Metacharacters), section 'Common Metacharacter Formats': Summarize a practical audit checklist for Auditing Tip, including common vulnerable constructs and impact considerations.

## Analysis / Response

From a software security assessment perspective (Chapter 8: Strings and Metacharacters — Common Metacharacter Formats), here is how auditors handle Auditing Tip.

You might find a vulnerability in which you can duplicate a file descriptor. If you have
access to an environment similar to one in which the script is running, use lsof or a
similar tool to determine what file descriptors are open when the process runs. This
tool should help you see what you might have access to.

SQL Queries

SQL is a standard language for interacting with a relational database management
system (RDBMS). You most likely encounter SQL in the context of Web applications,
when examining server-side scripts or applications that process input from browsers
and issue queries to a back-end database. Incorrect handling of input to these queries
can result in severe vulnerabilities. This discussion focuses on dynamically
constructed queries in normal SQL syntax. Chapter 17, "Web Applications,"
expands this coverage to address parameterized queries and stored procedures.

The most common SQL-related vulnerability is SQL injection. It occurs when input is
taken from request data (post variables, forms, or cookies) and concatenated into a
query string issued against the database. Listing 8-20 is a simple example in PHP and
MySQL.

Listing 8-20. SQL Injection Vulnerability
$username = $HTTP_POST_VARS['username'];

$password = $HTTP_POST_VARS['passwd'];

$query = "SELECT * FROM logintable WHERE user = '"
 . $username . "' AND pass = '" . $password. "'";

...

$result = mysql_query($query);

if(!$result)
 die_bad_login();
...

This query is vulnerable to SQL injection because users can supply unfiltered input for
the passwd and username variables. Attackers could easily submit a string such as
"bob' OR pass <> 'bob" for both parameters, which results in the following query being
issued against the database:
