# BUSINESS_LOGIC — portswigger_labs_sft

- source: portswigger_labs_sft
- class: business_logic
- cwe: CWE-840

## Scenario

How do I solve this PortSwigger Web Security Academy lab?

Title: Inconsistent handling of exceptional input
Difficulty: Practitioner
Category: Business logic vulnerabilities

This lab doesn't adequately validate user input. You can exploit a logic flaw in its account registration process to gain access to administrative functionality. To solve the lab, access the admin panel and delete the user `carlos`.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Business logic vulnerabilities: "Inconsistent handling of exceptional input".

## Solution steps

1. While proxying traffic through Burp, open the lab and go to the "Target" > "Site map" tab. Right-click on the lab domain and select "Engagement tools" > "Discover content" to open the content discovery tool.
2. Click "Session is not running" to start the content discovery. After a short while, look at the "Site map" tab in the dialog. Notice that it discovered the path `/admin`.
3. Try to browse to `/admin`. Although you don't have access, an error message indicates that `DontWannaCry` users do.
4. Go to the account registration page. Notice the message telling `DontWannaCry` employees to use their company email address.
5. From the button in the lab banner, open the email client. Make a note of the unique ID in the domain name for your email server (`@YOUR-EMAIL-ID.web-security-academy.net`).
6. Go back to the lab and register with an exceptionally long email address in the format: `very-long-string@YOUR-EMAIL-ID.web-security-academy.net` The `very-long-string` should be at least 200 characters long.
7. Go to the email client and notice that you have received a confirmation email. Click the link to complete the registration process.
8. Log in and go to the "My account" page. Notice that your email address has been truncated to 255 characters.
9. Log out and go back to the account registration page.
10. Register a new account with another long email address, but this time include `dontwannacry.com` as a subdomain in your email address as follows: `very-long-string@dontwannacry.com.YOUR-EMAIL-ID.web-security-academy.net` Make sure that the `very-long-string` is the right number of characters so that the "`m`" at the end of `@dontwannacry.com` is character 255 exactly.
11. Go to the email client and click the link in the confirmation email that you have received. Log in to your new account and notice that you now have access to the admin panel. The confirmation email was successfully sent to your email client, but the application server truncated the address associated with your account to 255 characters. As a result, you have been able to register with what appears to be a valid `@dontwannacry.com` address. You can confirm this from the "My account" page.
12. Go to the admin panel and delete `carlos` to solve the lab.

## Vulnerability note

Underlying issue: Business logic vulnerabilities (CWE-840). Validate workflow state server-side; never trust client-supplied prices, quantities, or step order.
