# CLICKJACKING — portswigger_labs_sft

- source: portswigger_labs_sft
- class: clickjacking
- cwe: CWE-1021

## Scenario

Help me complete the lab "Basic clickjacking with CSRF token protection" from PortSwigger Web Security Academy. Category: Clickjacking. Difficulty: Apprentice.

This lab contains login functionality and a delete account button that is protected by a CSRF token. A user will click on elements that display the word "click" on a decoy website.

To solve the lab, craft some HTML that frames the account page and fools the user into deleting their account. The lab is solved when the account is deleted.

You can log in to your own account using the following credentials: `wiener:peter`

Note

 The victim will be using Chrome so test your exploit on that browser.

Provide the ordered solution steps.

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers Clickjacking: "Basic clickjacking with CSRF token protection".

## Solution steps

1. Log in to your account on the target website.
2. Go to the exploit server and paste the following HTML template into the Body section: `<style> iframe { position:relative; width:$width_value; height: $height_value; opacity: $opacity; z-index: 2; } div { position:absolute; top:$top_value; left:$side_value; z-index: 1; } </style> <div>Test me</div> <iframe src="YOUR-LAB-ID.web-security-academy.net/my-account"></iframe>`
3. Make the following adjustments to the template: Replace `YOUR-LAB-ID` in the iframe `src` attribute with your unique lab ID. Substitute suitable pixel values for the `$height_value` and `$width_value` variables of the iframe (we suggest 700px and 500px respectively). Substitute suitable pixel values for the `$top_value` and `$side_value` variables of the decoy web content so that the "Delete account" button and the "Test me" decoy action align (we suggest 300px and 60px respectively). Set the opacity value `$opacity` to ensure that the target iframe is transparent. Initially, use an opacity of 0.1 so that you can align the iframe actions and adjust the position values as necessary. For the submitted attack a value of 0.0001 will work.
4. Click Store and then View exploit.
5. Hover over Test me and ensure the cursor changes to a hand indicating that the div element is positioned correctly. Do not actually click the "Delete account" button yourself. If you do, the lab will be broken and you will need to wait until it resets to try again (about 20 minutes). If the div does not line up properly, adjust the `top` and `left` properties of the style sheet.
6. Once you have the div element lined up correctly, change "Test me" to "Click me" and click Store.
7. Click on Deliver exploit to victim and the lab should be solved.

## Vulnerability note

Underlying issue: Clickjacking (CWE-1021). Prevent clickjacking with Content-Security-Policy frame-ancestors and X-Frame-Options.
