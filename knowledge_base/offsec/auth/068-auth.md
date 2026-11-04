# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-384

## Scenario

What should a web pentester know about Web Application Hacker's Handbook 2e — 236   Chapter 7 n Attacking Session Management?

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (236   Chapter 7 n Attacking Session Management):

236   Chapter 7 n Attacking Session Management

                     service on the same server if one is running or to http://server:443/
                     otherwise), his token may be submitted. Means by which the attacker
                     may attempt this include sending the user a URL in an e-mail or instant
                     message, placing autoloading links into a website the attacker controls,
                     or using clickable banner ads. (See Chapters 12 and 13 for more details
                     about techniques of this kind for delivering attacks against other users.)

                  HACK STEPS

                   1. Walk through the application in the normal way from first access (the
                      “start” URL), through the login process, and then through all of the appli-
                      cation’s functionality. Keep a record of every URL visited, and note every
                      instance in which a new session token is received. Pay particular atten-
                      tion to login functions and transitions between HTTP and HTTPS com-
                      munications. This can be achieved manually using a network sniffer such
                      as Wireshark or partially automated using the logging functions of your
                      intercepting proxy, as shown in Figure 7-10.

                  Figure 7-10: Walking through an application to identify locations where new
                  session tokens are received.

                   2. If HTTP cookies are being used as the transmission mechanism for session
                      tokens, verify whether the secure flag is set, preventing them from ever
                      being transmitted over unencrypted connections.
                   3. Determine whether, in the normal use of the application, session tokens
                      are ever transmitted over an unencrypted connection. If so, they should be
                      regarded as vulnerable to interception.
                   4. Where the start page uses HTTP, and the application switches to HTTPS
                      for the login and authenticated areas of the site, verify whether a new
                      token is issued following login, or whether a token transmitted during the
                      HTTP stage is still being used to track the user’s authenticated session.

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.
