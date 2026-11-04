# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-384

## Scenario

Walk me through Web Application Hacker's Handbook 2e — Chapter 7 n Attacking Session Management               217 with practical steps and examples from the source material.

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Chapter 7 n Attacking Session Management               217):

This second observation immediately alerts us to the role played by time
               in generating session tokens. Apparently, only ﬁve tokens have been issued
               between the two token-grabbing exercises. However, a period of approximately
               10 minutes has elapsed. The most likely explanation is that the second number
               is time-dependent and is probably a simple count of milliseconds.
                  Indeed, our hunch is correct. In a subsequent phase of our testing we perform
               a code review, which reveals the following token-generation algorithm:
                 String sessId = Integer.toString(s_SessionIndex++) +
                     “-” +
                     System.currentTimeMillis();

                  Given our analysis of how tokens are created, it is straightforward to con-
               struct a scripted attack to harvest the session tokens that the application issues
               to other users:
                  n   We continue polling the server to obtain new session tokens in quick
                      succession.
                  n   We monitor the increments in the ﬁrst number. When this increases by
                      more than 1, we know that a token has been issued to another user.
                  n   When a token has been issued to another user, we know the upper and
                      lower bounds of the second number that was issued to that person, because
                      we possess the tokens that were issued immediately before and after
                      his. Because we are obtaining new session tokens frequently, the range
                      between these bounds will typically consist of only a few hundred values.
                  n   Each time a token is issued to another user, we launch a brute-force attack
                      to iterate through each number in the range, appending this to the miss-
                      ing incremental number that we know was issued to the other user. We
                      attempt to access a protected page using each token we construct, until
                      the attempt succeeds and we have compromised the user’s session.
                  n   Running this scripted attack continuously will enable us to capture the
                      session token of every other application user. When an administrative
                      user logs in, we will fully compromise the entire application.

                 TRY IT!

                           http://mdsec.net/auth/339/
                           http://mdsec.net/auth/340/
                           http://mdsec.net/auth/347/
                           http://mdsec.net/auth/351/

c07.indd 217                                                                                        8/19/2011 12:07:40 PM

                                                                           Stuttard c07.indd V3 - 07/22/2011 Page 218

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.
