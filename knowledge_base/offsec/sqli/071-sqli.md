# SQLI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: sqli
- cwe: CWE-89

## Scenario

From Chapter 17 (Web Applications), section 'Common Vulnerabilities': Break down Second Order Injection for an offensive security engineer doing authorized application assessment.

## Analysis / Response

From a software security assessment perspective (Chapter 17: Web Applications — Common Vulnerabilities), here is how auditors handle Second Order Injection.

Second order injection refers to SQL injection resulting from data in the database
itself; it occurs when database fields are used to generate a dynamic query. The root
of this problem is that a complex application might make determining the exact
source of data difficult. For instance, say you have a database that backs a
Web-based bulletin board. The following parameterized query would allow users to
update the list of bulletin board memberships:

UPDATE users SET boardlist = ? WHERE user = ?

Each board has a numeric ID, so the boardlist column contains strings such as the
following: 1, 15, 8, 23. On its own, this parameterized query is structured correctly
and safe from injection. However, there's no point in putting data in a database if you
don't use it. Here's a query you might use to access this data:

"SELECT board_id, board_name FROM boards, users
 WHERE user = ? AND board_id IN (" + boardList + ")"

The boardList variable is a string retrieved from an earlier database query. The
problem is that the string was originally supplied from user input and could contain
malicious characters. An attacker can exploit this by first updating the board_id field
and then triggering the unsafe query on this field.

These types of injection vulnerabilities are relatively common, particularly in stored
procedures. However, they are often hard to detect because the vulnerability results
from two or more seemingly unrelated code paths. This also makes automated
analysis and fuzzing techniques almost useless. The best approach is to identify all
dynamic queries. Then treat all database input fields as hostile until you can prove
otherwise. In some cases, you might not be able to determine that database input is
safe. The database tier might receive input from sources other than the application
you're reviewing, so you might have to consider it a vulnerability of unknown
potential risk.
