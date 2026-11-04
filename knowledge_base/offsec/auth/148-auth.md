# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Describe methodology and key techniques for From Day Zero to Zero Day — Automated Variant Analysis: To complete the root cause analysis, you must understand how to reach during an authorized assessment.

## Analysis / Response

Based on From Day Zero to Zero Day (web-relevant) (To complete the root cause analysis, you must understand how to reach):

To complete the root cause analysis, you must understand how to reach
                this vulnerable code path, or sink. Fortunately, the pull request comment
                also links to the corresponding issue, titled “[CVE-2021-46143] Crafted XML
                file can cause integer overflow on m_groupSize in function doProlog” (https://
                github.com/libexpat/libexpat/issues/532). The issue notes that an anonymous
                white hat researcher reported the vulnerability via the Zero Day Initiative
                (ZDI), which facilitates zero-day vulnerability disclosures and provides finan-
                cial rewards. Additionally, it states that “the issue is an integer overflow (in
                multiplication) near a call to realloc that takes a 2 GiB size craft XML file,
                and then will cause denial of service or more.” Finally, the issue comment
                includes a snippet of the vulnerability disclosure’s analysis section:
                     “This is an integer overflow vulnerability that exists in expat library. The
                vulnerable function is doProlog:

doProlog(XML_Parser parser, const ENCODING *enc, const char *s, const char *end,
         int tok, const char *next, const char **nextPtr, XML_Bool haveMore,
         XML_Bool allowClosingDoctype, enum XML_Account account) {

Use only on systems you are authorized to test; capture evidence and include remediation.
