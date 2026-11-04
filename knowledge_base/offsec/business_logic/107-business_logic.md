# BUSINESS_LOGIC — portswigger_labs_sft

- source: portswigger_labs_sft
- class: business_logic
- cwe: CWE-840

## Scenario

Teach me the official solution for this PortSwigger Academy lab.

Lab: High-level logic vulnerability
Topic: Business logic vulnerabilities
Level: Apprentice

Scenario:
This lab doesn't adequately validate user input. You can exploit a logic flaw in its purchasing workflow to buy items for an unintended price. To solve the lab, buy a "Lightweight l33t leather jacket".

You can log in to your own account using the following credentials: `wiener:peter`

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers Business logic vulnerabilities: "High-level logic vulnerability".

## Solution steps

1. With Burp running, log in and add a cheap item to your cart.
2. In Burp, go to "Proxy" > "HTTP history" and study the corresponding HTTP messages. Notice that the quantity is determined by a parameter in the `POST /cart` request.
3. Go to the "Intercept" tab and turn on interception. Add another item to your cart and go to the intercepted `POST /cart` request in Burp.
4. Change the `quantity` parameter to an arbitrary integer, then forward any remaining requests. Observe that the quantity in the cart was successfully updated based on your input.
5. Repeat this process, but request a negative quantity this time. Check that this is successfully deducted from the cart quantity.
6. Request a suitable negative quantity to remove more units from the cart than it currently contains. Confirm that you have successfully forced the cart to contain a negative quantity of the product. Go to your cart and notice that the total price is now also a negative amount.
7. Add the leather jacket to your cart as normal. Add a suitable negative quantity of the another item to reduce the total price to less than your remaining store credit.
8. Place the order to solve the lab.

## Vulnerability note

Underlying issue: Business logic vulnerabilities (CWE-840). Validate workflow state server-side; never trust client-supplied prices, quantities, or step order.
