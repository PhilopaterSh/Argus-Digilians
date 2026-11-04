# INFO_DISCLOSURE — portswigger_labs_sft

- source: portswigger_labs_sft
- class: info_disclosure
- cwe: CWE-200

## Scenario

Teach me the official solution for this PortSwigger Academy lab.

Lab: Information disclosure in error messages
Topic: Information disclosure
Level: Apprentice

Scenario:
This lab's verbose error messages reveal that it is using a vulnerable version of a third-party framework. To solve the lab, obtain and submit the version number of this framework.

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers Information disclosure: "Information disclosure in error messages".

## Solution steps

1. With Burp running, open one of the product pages.
2. In Burp, go to "Proxy" > "HTTP history" and notice that the `GET` request for product pages contains a `productID` parameter. Send the `GET /product?productId=1` request to Burp Repeater. Note that your `productId` might be different depending on which product page you loaded.
3. In Burp Repeater, change the value of the `productId` parameter to a non-integer data type, such as a string. Send the request: `GET /product?productId="example"`
4. The unexpected data type causes an exception, and a full stack trace is displayed in the response. This reveals that the lab is using Apache Struts 2 2.3.31.
5. Go back to the lab, click "Submit solution", and enter 2 2.3.31 to solve the lab.

## Vulnerability note

Underlying issue: Information disclosure (CWE-200). Remove verbose errors/debug pages in production; restrict backup and source files from web roots.
