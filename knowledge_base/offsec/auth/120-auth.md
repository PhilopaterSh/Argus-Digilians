# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Describe the methodology and key techniques for Web Application Hacker's Handbook 2e — SQL Error Messages during an authorized assessment.

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (SQL Error Messages):

SQL Error Messages

                  Oracle:        ORA-01756: quoted string not properly terminated

                                 ORA-00933: SQL command not properly ended
                  MS-SQL:        Msg 170, Level 15, State 1, Line 1

                                 Line 1: Incorrect syntax near ‘foo’

                                 Msg 105, Level 15, State 1, Line 1

                                 Unclosed quotation mark before the character string
                                 ‘foo’

c09.indd 334                                                                                            8/19/2011 12:09:33 PM

                                                                    Stuttard c09.indd V3 - 07/28/2011 Page 335

                                                            Chapter 9 n Attacking Data Stores            335

               MySQL:         You have an error in your SQL syntax. Check the man-
                              ual that corresponds to your MySQL server version
                              for the right syntax to use near ‘’foo’ at line X
               Translation:   For Oracle and MS-SQL, SQL injection is present, and it is almost
                              certainly exploitable! If you entered a single quote and it altered
                              the syntax of the database query, this is the error you’d expect. For

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.
