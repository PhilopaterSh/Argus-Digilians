# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Explain Web Application Hacker's Handbook 2e — Approached in this way, code review can be an extremely useful complement with payloads/commands where the material provides them (authorized testing only).

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Approached in this way, code review can be an extremely useful complement):

Approached in this way, code review can be an extremely useful complement
                to the more familiar black-box testing. It can improve the effectiveness of that
                testing and reveal defects that may be extremely difﬁcult to discover when you
                are dealing with an application entirely from the outside.

                Questions
                Answers can be found at http://mdsec.net/wahh.
                  1. List three categories of common vulnerabilities that often have easily
                     recognizable signatures within source code.
                  2. Why can identifying all sources of user input sometimes be challenging
                     when reviewing a PHP application?
                  3. Consider the following two methods of performing a SQL query that
                     incorporates user-supplied input:
                      // method 1
                      String artist = request.getParameter(“artist”).replaceAll(“’”, “’’”);
                      String genre = request.getParameter(“genre”).replaceAll(“’”, “’’”);
                      String album = request.getParameter(“album”).replaceAll(“’”, “’’”);
                      Statement s = connection.createStatement();
                      s.executeQuery(“SELECT * FROM music WHERE artist = ‘” + artist +
                          ‘” AND genre = ‘” + genre + ‘” AND album = ‘” + album + “’”);

                      // method 2
                      String artist = request.getParameter(“artist”);
                      String genre = request.getParameter(“genre”);
                      String album = request.getParameter(“album”);
                      Statement s = connection.prepareStatement(
                          “SELECT * FROM music WHERE artist = ‘” + artist +
                          “’ AND genre = ? AND album = ?”);

c19.indd 744                                                                                            8/19/2011 12:18:39 PM

                                                           Stuttard c19.indd V2 - 08/11/2011 Page 745

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.
