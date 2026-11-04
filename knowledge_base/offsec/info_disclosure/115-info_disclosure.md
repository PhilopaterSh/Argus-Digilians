# INFO_DISCLOSURE — portswigger_labs_sft

- source: portswigger_labs_sft
- class: info_disclosure
- cwe: CWE-200

## Scenario

Help me complete the lab "Source code disclosure via backup files" from PortSwigger Web Security Academy. Category: Information disclosure. Difficulty: Apprentice.

This lab leaks its source code via backup files in a hidden directory. To solve the lab, identify and submit the database password, which is hard-coded in the leaked source code.

Provide the ordered solution steps.

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers Information disclosure: "Source code disclosure via backup files".

## Solution steps

1. Browse to `/robots.txt` and notice that it reveals the existence of a `/backup` directory. Browse to `/backup` to find the file `ProductTemplate.java.bak`. Alternatively, right-click on the lab in the site map and go to "Engagement tools" > "Discover content". Then, launch a content discovery session to discover the `/backup` directory and its contents.
2. Browse to `/backup/ProductTemplate.java.bak` to access the source code.
3. In the source code, notice that the connection builder contains the hard-coded password for a Postgres database.
4. Go back to the lab, click "Submit solution", and enter the database password to solve the lab.

## Vulnerability note

Underlying issue: Information disclosure (CWE-200). Remove verbose errors/debug pages in production; restrict backup and source files from web roots.
