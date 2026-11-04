# BUSINESS_LOGIC — portswigger_labs_sft

- source: portswigger_labs_sft
- class: business_logic
- cwe: CWE-840

## Scenario

I'm stuck on the PortSwigger lab "Excessive trust in client-side controls" (Apprentice, Business logic vulnerabilities). Here's the scenario:

This lab doesn't adequately validate user input. You can exploit a logic flaw in its purchasing workflow to buy items for an unintended price. To solve the lab, buy a "Lightweight l33t leather jacket".

You can log in to your own account using the following credentials: `wiener:peter`

Please give me the step-by-step solution.

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers Business logic vulnerabilities: "Excessive trust in client-side controls".

## Solution steps

1. With Burp running, log in and attempt to buy the leather jacket. The order is rejected because you don't have enough store credit.
2. In Burp, go to "Proxy" > "HTTP history" and study the order process. Notice that when you add an item to your cart, the corresponding request contains a `price` parameter. Send the `POST /cart` request to Burp Repeater.
3. In Burp Repeater, change the price to an arbitrary integer and send the request. Refresh the cart and confirm that the price has changed based on your input.
4. Repeat this process to set the price to any amount less than your available store credit.
5. Complete the order to solve the lab.

## Vulnerability note

Underlying issue: Business logic vulnerabilities (CWE-840). Validate workflow state server-side; never trust client-supplied prices, quantities, or step order.
