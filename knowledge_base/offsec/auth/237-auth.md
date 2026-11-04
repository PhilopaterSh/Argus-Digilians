# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

How do I apply 'Web Security for Developers — Compromising Authentication: Requiring Complex Passwords' when testing an in-scope web application?

## Analysis / Response

Based on Web Security for Developers (Requiring Complex Passwords):

Requiring Complex Passwords
Complex passwords are generally harder to guess, so you should require
users to meet certain password complexity standards when they choose a
password, for their own protection. Complex passwords include numbers
and symbols as well as letters, have a mix of uppercase and lowercase char-
acters, and are long rather than short. At the very least, you should enforce
a minimum length of eight characters for passwords, but the longer the bet-
ter. (Studies have shown that password length is more important than mix-
ing in unusual characters.)

                                                             Compromising Authentication   87

                      However, users often have trouble remembering complex passwords,
                 so if you enforce overly strict password complexity requirements, a user will
                 usually reuse a password they previously entered on another website. Some
                 secure sites prevent a user from reusing a password they previously used
                 to force them to choose a new, unique password each time, pushing them
                 away from lazy habits. Unfortunately, most users will simply cycle passwords
                 by adding a number at the end of a password they commonly use, which
                 doesn’t make for a significantly less guessable password.
                      Ultimately, each user is responsible for their own security online, so it’s
                 generally better to nudge your users toward strong password choices rather
                 than forcing them to jump through hoops. Some JavaScript libraries, like
                 the password-strength-calculator library, can be used to rate a user’s pass-
                 word’s complexity as they type it and to call out commonly used passwords,
                 which you can use on sign-up and password-reset screens to push users
                 toward a more secure password.

Use only on systems you are authorized to test; capture evidence and include remediation.
