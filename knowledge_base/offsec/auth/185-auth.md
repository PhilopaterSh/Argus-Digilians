# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Describe the methodology and key techniques for Enumerating Esoteric Attack Surfaces (Jann Moon): To start off this frenzied JavaScript methodology, my first step would be during an authorized assessment.

## Analysis / Response

Based on Enumerating Esoteric Attack Surfaces (Jann Moon) (To start off this frenzied JavaScript methodology, my first step would be):

To start off this frenzied JavaScript methodology, my first step would be
to gather all of the endpoints from the past steps in this section - the
ones pulled from various third-party services and then spidered to find
as many relevant endpoints as possible. At this time, you could use

something like httpx or fff to weed out all of the bad endpoints (cat
urls-gathered.txt | httpx -mc 200,302), though I think katana
should’ve done all of that if you feed the third-party lists to it as your
input. Once you have this list, you can pull all the JS files from it with
the following command.

cat urls.txt | grep -E -v “\.json|\.jsp” | grep “.js” | tee js-urls.txt

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.
