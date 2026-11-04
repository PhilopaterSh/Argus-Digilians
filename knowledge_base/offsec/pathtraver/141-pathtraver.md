# PATHTRAVER — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: pathtraver
- cwe: CWE-98

## Scenario

What should a web pentester know about Enumerating Esoteric Attack Surfaces (Jann Moon): Another tool fulfilling the role of insane bastard resolver, is?

## Analysis / Response

Based on Enumerating Esoteric Attack Surfaces (Jann Moon) (Another tool fulfilling the role of insane bastard resolver, is):

Another tool fulfilling the role of insane bastard resolver, is
projectdiscovery’s dnsx.

You can install it through go.

go install -v
github.com/projectdiscovery/dnsx/cmd/dnsx@latest

Or grab the compiled release.

https://github.com/projectdiscovery/dnsx/releases/

I usually set it to record any response it receives like so.

   cat badboy-com-subdomains.txt |            ripgen      | dnsx -t 1000
                    -silent -o ripgen-results.txt

If your output is popping regardless of the nonsense that is entered as a
    subdomain, you’ll want to have dnsx use its very bleeding-edge
  wildcard filter. Apparently, it does multi-level DNS-based wildcards,
which I am not afraid to admit is a term that I’m unfamiliar with. Add it
    by tossing in the “-wd [domain.com]” into dnsx’s arguments.

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report. Always stay within authorized scope, document evidence carefully, and prefer non-destructive verification (harmless canaries, OOB callbacks you control, and clear remediation guidance for the asset owner).
