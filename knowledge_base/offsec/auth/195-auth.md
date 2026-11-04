# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Walk me through Web Security for Developers — Injection Attacks: Introduction with practical steps from the source material.

## Analysis / Response

Based on Web Security for Developers (Introduction):

Injection Attacks   51

                   statement, a hacker can craft input that bypasses the website’s authentica-
                   tion system.
                        An example of this is shown in Listing 6-3. In this example, the attacker
                   passes the user email parameter as billy@gmail.com'--, which terminates the
                   SQL statement early and causes the password-checking logic to not execute:

statement.executeQuery(
  "SELECT * FROM users WHERE email='billy@gmail.com'u--' AND encrypted_password='Z$DSA92H0'v");

Listing 6-3: Using SQL injection to bypass authentication

                        The database driver executes only the SQL statement u, and ignores
                   everything that comes after it v. In this type of SQL injection attack, the
                   single quote character (') closes the email argument early, and the SQL
                   comment syntax (--) tricks the database driver into ignoring the end of the
                   statement that does password checking. This SQL statement allows the attacker
                   to log in as any user without having to know their password! All the attacker
                   has to do is add the ' and -- characters to the user’s email address in the
                   login form.
                        This is a relatively simple example of a SQL injection attack. A more
                   advanced attack might cause the database driver to run additional com-
                   mands on the database. Listing 6-4 shows a SQL injection attack that runs
                   a DROP command to remove the users table entirely, in order to corrupt
                   the database.

                   statement.executeQuery("SELECT * FROM users WHERE email='billy@gmail.com';u
                   DROP TABLE users;v--' AND encrypted_password='Z$DSA92H0'");

                   Listing 6-4: A SQL injection attack in progress

                       In this scenario, the attacker passes the email parameter as billy@gmail​
                   .com'; DROP TABLE users;--. The semicolon character (;) terminates the first
                   SQL statement u, after which the attacker inserts an additional, destructive
                   statement v. The database driver will run both statements, leaving your
                   database in a corrupt state!
                        If your website is vulnerable to SQL injection, an attacker can often run
                   arbitrary SQL statements against your database, allowing them to bypass
                   authentication; read, download, and delete data at will; or even inject mali-
                   cious JavaScript into the pages rendered to your users. To scan websites for
                   SQL injection vulnerabilities, hacking tools like Metasploit can be used to
                   crawl websites and test HTTP parameters with potential exploits. If your site
                   is vulnerable to SQL injection attacks, you can be sure that somebody will
                   eventually take advantage of it.

                   Mitigation 1: Use Parameterized Statements
                   To protect against SQL injection attacks, your code needs to construct SQL
                   strings using bind parameters. Bind parameters are placeholder characters
                   that the database driver will safely replace with some supplied inputs—like

52   Chapter 6

  the email or password values shown in Listing 6-1. A SQL statement con-
  taining bind parameters is called a parameterized statement.
       SQL injection attacks use “control characters” that have special mean-
  ing in SQL statements to “ jump out” of the context and change the whole
  semantics of the SQL statement. When you use bind parameters, these con-
  trol characters are prefixed with “escape characters” that tell the database
  not to treat the following character as a control character. This escaping of
  control characters defuses potential injection attacks.

Use only on systems you are authorized to test; capture evidence and include remediation.
