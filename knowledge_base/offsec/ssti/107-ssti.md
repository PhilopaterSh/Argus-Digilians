# SSTI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: ssti
- cwe: CWE-1336

## Scenario

Describe the methodology and key techniques for Bug Hunter's Methodology v2: ★ Engine identification during an authorized assessment.

## Analysis / Response

Based on Bug Hunter's Methodology v2 (★ Engine identification):

★ Engine identification
   ○ WAPPalyzer + BuiltWith + Vulners scanner
   ○ Test fuzzing
   ○ Tooling
   ○ TPLmap + tplmap Burp Extension
   ○ Backslash powered scanner?
★ Resources

SSTI

  1: https://acme.com/errorpage{{2*3}}

  2:

  https://acme.com/errorpage{{''.__class__.__mro__[2].__subclasses__
  ()[40]('/etc/passwd').read() }}

SSTI Tooling

SSTI           Original Whitepaper - James
               Kettle
                                             http://blog.portswigger.net/2015/08/server-side-template-injection.html

Resources
               OWASP SSTI Workshop -         https://speakerdeck.com/owaspmontreal/workshop-server-side-template-i
               Gérôme Dieu                   njection-ssti

               Exploring SSTI in             https://www.lanmaster53.com/2016/03/exploring-ssti-flask-jinja2/
               Flask/Jinja2 - Tim Tomes
                                             https://nvisium.com/blog/2016/03/11/exploring-ssti-in-flask-jinja2-part-ii/

               Injecting Flask - Ryan Reid   https://nvisium.com/blog/2015/12/07/injecting-flask/

    Hi Pete!
               Rails Dynamic Render to       https://nvisium.com/blog/2016/01/26/rails-dynamic-render-to-rce-cve-201
               RCE (CVE-2016-0752) -         6-0752/
               John Poulin

               uber.com may RCE by Flask     https://hackerone.com/reports/125980

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report. Always stay within authorized scope, document evidence carefully, and prefer non-destructive verification (harmless canaries, OOB callbacks you control, and clear remediation guidance for the asset owner).
