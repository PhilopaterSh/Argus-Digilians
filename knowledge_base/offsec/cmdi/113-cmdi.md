# CMDI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: cmdi
- cwe: CWE-20

## Scenario

What's a solid methodology for finding issues related to API fuzzing and parameter mutation? Please emphasize parameter mutation.

## Analysis / Response

## Overview
As discussed in Chapter 3, you can find improper assets management vulnerabilities by paying close attention to outdated API documentation. If an organization’s API documentation has not been updated along with the organization’s API endpoints, it could contain references to portions 214 Chapter 9 of the API that are no longer supported.

## Key points
In practice, also, check any sort of changelog or GitHub repository. A useful way to think about this is that a changelog that says something along the lines of “resolved broken object level authorization vulnerability in v3” will make finding an endpoint still using v1 or v2 all the sweeter. Other than using documentation, you can discover improper assets vulnerabilities through the use of fuzzing. One of the best ways to do this is to watch for patterns in the business logic and test your assumptions.

## Approach
1. In practice, also, check any sort of changelog or GitHub repository.
2. A useful way to think about this is that a changelog that says something along the lines of “resolved broken object level authorization vulnerability in v3” will make finding an endpoint still using v1 or v2 all the sweeter.
3. Other than using documentation, you can discover improper assets vulnerabilities through the use of fuzzing.
4. During authorized testing, one of the best ways to do this is to watch for patterns in the business logic and test your assumptions.
5. During authorized testing, for example, in , you can see that the baseURL variable used within all requests for this collection is.

## Scope & safety
If a step could affect availability or other users, pause and check the engagement rules first.
