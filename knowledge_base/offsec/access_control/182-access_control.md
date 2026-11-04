# ACCESS_CONTROL — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: access_control
- cwe: CWE-284

## Scenario

What should a web pentester know about Web Application Hacker's Handbook 2e — But in Oracle, if you want to return something, you must select from?

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (But in Oracle, if you want to return something, you must select from):

But in Oracle, if you want to return something, you must select from
                                 a table. The DUAL table will do ﬁne:

                                 SELECT 1 from DUAL

                  Oracle:        ORA-00936: missing expression
                  MS-SQL:        Msg 156, Level 15, State 1, Line 1Incorrect syntax
                                 near the keyword ‘from’.
                  MySQL:         You have an error in your SQL syntax. Check the
                                 manual that corresponds to your MySQL server version
                                 for the right syntax to use near ‘ XXX , YYY from
                                 SOME_TABLE’ at line 1
                  Translation:   You commonly see this error message when your injection point
                                 occurs before the FROM keyword (for example, you have injected
                                 into the columns to be returned) and/or you have used the com-
                                 ment character to remove required SQL keywords. Try completing the
                                 SQL statement yourself while using your comment character. MySQL
                                 should helpfully reveal the column names XXX, YYY when this condi-
                                 tion is encountered.

c09.indd 336                                                                                              8/19/2011 12:09:33 PM

                                                                  Stuttard c09.indd V3 - 07/28/2011 Page 337

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.
