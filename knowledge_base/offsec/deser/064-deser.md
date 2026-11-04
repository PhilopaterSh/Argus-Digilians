# DESER — portswigger_labs_sft

- source: portswigger_labs_sft
- class: deser
- cwe: CWE-502

## Scenario

How do I solve this PortSwigger Web Security Academy lab?

Title: Using application functionality to exploit insecure deserialization
Difficulty: Practitioner
Category: Insecure deserialization

This lab uses a serialization-based session mechanism. A certain feature invokes a dangerous method on data provided in a serialized object. To solve the lab, edit the serialized object in the session cookie and use it to delete the `morale.txt` file from Carlos's home directory.

You can log in to your own account using the following credentials: `wiener:peter`

You also have access to a backup account: `gregg:rosebud`

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Insecure deserialization: "Using application functionality to exploit insecure deserialization".

## Solution steps

1. Log in to your own account. On the "My account" page, notice the option to delete your account by sending a `POST` request to `/my-account/delete`.
2. Send a request containing a session cookie to Burp Repeater.
3. In Burp Repeater, study the session cookie using the Inspector panel. Notice that the serialized object has an `avatar_link` attribute, which contains the file path to your avatar.
4. Edit the serialized data so that the `avatar_link` points to `/home/carlos/morale.txt`. Remember to update the length indicator. The modified attribute should look like this: `s:11:"avatar_link";s:23:"/home/carlos/morale.txt"`
5. Click "Apply changes". The modified object will automatically be re-encoded and updated in the request.
6. Change the request line to `POST /my-account/delete` and send the request. Your account will be deleted, along with Carlos's `morale.txt` file.

## Vulnerability note

Underlying issue: Insecure deserialization (CWE-502). Avoid deserializing untrusted data; use allowlists, signing, and safer formats like JSON with schema validation.
