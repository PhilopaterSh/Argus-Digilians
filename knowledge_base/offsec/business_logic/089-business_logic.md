# BUSINESS_LOGIC — portswigger_labs_sft

- source: portswigger_labs_sft
- class: business_logic
- cwe: CWE-840

## Scenario

PortSwigger lab: "Low-level logic flaw". This lab doesn't adequately validate user input. You can exploit a logic flaw in its purchasing workflow to buy items for an unintended price. To solve the lab, buy a "Lightweight l33t leather jacket".

You can log in to your own account using the following credentials: `wiener:peter`

Walk me through how to solve it.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Business logic vulnerabilities: "Low-level logic flaw".

## Solution steps

1. With Burp running, log in and attempt to buy the leather jacket. The order is rejected because you don't have enough store credit. In the proxy history, study the order process. Send the `POST /cart` request to Burp Repeater.
2. In Burp Repeater, notice that you can only add a 2-digit quantity with each request. Send the request to Burp Intruder.
3. Go to Intruder and set the `quantity` parameter to `99`.
4. In the Payloads side panel, select the payload type Null payloads. Under Payload configuration, select Continue indefinitely. Start the attack.
5. While the attack is running, go to your cart. Keep refreshing the page every so often and monitor the total price. Eventually, notice that the price suddenly switches to a large negative integer and starts counting up towards 0. The price has exceeded the maximum value permitted for an integer in the back-end programming language (2,147,483,647). As a result, the value has looped back around to the minimum possible value (-2,147,483,648).
6. Clear your cart. In the next few steps, we'll try to add enough units so that the price loops back around and settles between $0 and the $100 of your remaining store credit. This is not mathematically possible using only the leather jacket. Note that the price of the jacket is stored in cents (133700).
7. Create the same Intruder attack again, but this time under Payload configuration, choose to generate exactly `323` payloads.
8. Click Resource pool to open the Resource pool tab. Add the attack to a resource pool with the Maximum concurrent requests set to `1`. Start the attack.
9. When the Intruder attack finishes, go to the `POST /cart` request in Burp Repeater and send a single request for `47` jackets. The total price of the order should now be `-$1221.96`.
10. Use Burp Repeater to add a suitable quantity of another item to your cart so that the total falls between $0 and $100.
11. Place the order to solve the lab.

## Vulnerability note

Underlying issue: Business logic vulnerabilities (CWE-840). Validate workflow state server-side; never trust client-supplied prices, quantities, or step order.
