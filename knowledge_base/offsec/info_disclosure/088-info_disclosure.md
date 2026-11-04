# INFO_DISCLOSURE — portswigger_labs_sft

- source: portswigger_labs_sft
- class: info_disclosure
- cwe: CWE-200

## Scenario

Scenario framing — PortSwigger "Information disclosure on debug page" (Information disclosure, Apprentice):
This lab contains a debug page that discloses sensitive information about the application. To solve the lab, obtain and submit the `SECRET_KEY` environment variable.

What are the exact steps to solve this lab?

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers Information disclosure: "Information disclosure on debug page".

## Solution steps

1. With Burp running, browse to the home page.
2. Go to the "Target" > "Site Map" tab. Right-click on the top-level entry for the lab and select "Engagement tools" > "Find comments". Notice that the home page contains an HTML comment that contains a link called "Debug". This points to `/cgi-bin/phpinfo.php`.
3. In the site map, right-click on the entry for `/cgi-bin/phpinfo.php` and select "Send to Repeater".
4. In Burp Repeater, send the request to retrieve the file. Notice that it reveals various debugging information, including the `SECRET_KEY` environment variable.
5. Go back to the lab, click "Submit solution", and enter the `SECRET_KEY` to solve the lab.

## Vulnerability note

Underlying issue: Information disclosure (CWE-200). Remove verbose errors/debug pages in production; restrict backup and source files from web roots.
