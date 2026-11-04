# RACE — portswigger_labs_sft

- source: portswigger_labs_sft
- class: race
- cwe: CWE-362

## Scenario

How do I solve this PortSwigger Web Security Academy lab?

Title: Multi-endpoint race conditions
Difficulty: Practitioner
Category: Race conditions

This lab's purchasing flow contains a race condition that enables you to purchase items for an unintended price.

To solve the lab, successfully purchase a Lightweight L33t Leather Jacket.

You can log into your account with the following credentials: `wiener:peter`.

Note

 Solving this lab requires Burp Suite 2023.9 or higher.

Tip

 When experimenting, we recommend purchasing the gift card as you can later redeem this to avoid running out of store credit.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Race conditions: "Multi-endpoint race conditions".

## Solution steps

1. Log in and purchase a gift card so you can study the purchasing flow.
2. Consider that the shopping cart mechanism and, in particular, the restrictions that determine what you are allowed to order, are worth trying to bypass.
3. From the proxy history, identify all endpoints that enable you to interact with the cart. For example, a `POST /cart` request adds items to the cart and a `POST /cart/checkout` request submits your order.
4. Add another gift card to your cart, then send the `GET /cart` request to Burp Repeater.
5. In Repeater, try sending the `GET /cart` request both with and without your session cookie. Confirm that without the session cookie, you can only access an empty cart. From this, you can infer that: The state of the cart is stored server-side in your session. Any operations on the cart are keyed on your session ID or the associated user ID. This indicates that there is potential for a collision.
6. Notice that submitting and receiving confirmation of a successful order takes place over a single request/response cycle.
7. Consider that there may be a race window between when your order is validated and when it is confirmed. This could enable you to add more items to the order after the server checks whether you have enough store credit.

## Vulnerability note

Underlying issue: Race conditions (CWE-362). Use atomic operations, proper locking/transactions, and idempotency keys for sensitive state changes.
