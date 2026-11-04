# RESOURCE — h1

- source: h1
- class: resource
- cwe: CWE-400
- severity: medium
- program: gitlab
- quality_score: 11

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** DoS on the Issue page by exploiting Mermaid.
**Affected Asset:** gitlab.com

**Vulnerability Description:**
**Summary:**
An attacker could exploit Mermaid available in Markdown and cause DoS.

**Description:**
Markdown supported by GitLab can generate diagrams and flowcharts from text using Mermaid. An  Attacker can exploit this function to prevent users from successfully accessing some functions. For example, you can use Markdown in Issue's comment. Therefore, DoS can be caused by all users who can comment on that Issue.

## Steps To Reproduce:
[Preparation]
1. Create a new public Project.
2. Create an Issue in the Project created in step 1.
3. Add some comments to the Project created in step 2.

[Attack Flow]
1. Go to the Issue page created in preparation step 2. 
2. Copy the payload. (payload is attached file.)
3. Paste the payload on the comment input form.
4. Submit the comment.

Result: Since the screen freezes, the user can not access details of the Issue. In addition, the user can not take any additional action on that Issue.

NOTE: Similar attacks are effective for all functions that can use Markdown.

## Supporting Material/References:
- payload.txt
- poc.mp4

## Impact

- All users will not be able to access Issue details.
- All users can not take additional actions for the Issue.

**Steps to Reproduce:**
[Preparation]
1. Create a new public Project.
2. Create an Issue in the Project created in step 1.
3. Add some comments to the Project created in step 2.

[Attack Flow]
1. Go to the Issue page created in preparation step 2. 
2. Copy the payload. (payload is attached file.)
3. Paste the payload on the comment input form.
4. Submit the comment.

Result: Since the screen freezes, the user can not access details of the Issue. In addition, the user can not take any additional action on that Issue.

NOTE: Similar attacks are effective for all functions that can use Markdown.

## Supporting Material/References:
- payload.txt
- poc.mp4

## Analysis / Response

**Vulnerability Class:** resource
**CWE:** CWE-400
**Weakness:** Uncontrolled Resource Consumption
**Severity:** medium

**Impact Assessment:**
- All users will not be able to access Issue details.
- All users can not take additional actions for the Issue.

**Remediation:**
Implement rate limiting and request size limits. Set timeouts on all operations. Use circuit breakers for downstream services. Validate input complexity.
