# DESER — portswigger_labs_sft

- source: portswigger_labs_sft
- class: deser
- cwe: CWE-502

## Scenario

How do I solve this PortSwigger Web Security Academy lab?

Title: Developing a custom gadget chain for PHP deserialization
Difficulty: Expert
Category: Insecure deserialization

This lab uses a serialization-based session mechanism. By deploying a custom gadget chain, you can exploit its insecure deserialization to achieve remote code execution. To solve the lab, delete the `morale.txt` file from Carlos's home directory.

You can log in to your own account using the following credentials: `wiener:peter`

## Analysis / Response

This PortSwigger Web Security Academy lab (Expert) covers Insecure deserialization: "Developing a custom gadget chain for PHP deserialization".

## Solution steps

1. Log in to your own account and notice that the session cookie contains a serialized PHP object. Notice that the website references the file `/cgi-bin/libs/CustomTemplate.php`. Obtain the source code by submitting a request using the `.php~` backup file extension.
2. In the source code, notice that the `__wakeup()` magic method for a `CustomTemplate` will create a new `Product` by referencing the `default_desc_type` and `desc` from the `CustomTemplate`.
3. Also notice that the `DefaultMap` class has the `__get()` magic method, which will be invoked if you try to read an attribute that doesn't exist for this object. This magic method invokes `call_user_func()`, which will execute any function that is passed into it via the `DefaultMap->callback` attribute. The function will be executed on the `$name`, which is the non-existent attribute that was requested.
4. You can exploit this gadget chain to invoke `exec(rm /home/carlos/morale.txt)` by passing in a `CustomTemplate` object where: `CustomTemplate->default_desc_type = "rm /home/carlos/morale.txt"; CustomTemplate->desc = DefaultMap; DefaultMap->callback = "exec"` If you follow the data flow in the source code, you will notice that this causes the `Product` constructor to try and fetch the `default_desc_type` from the `DefaultMap` object. As it doesn't have this attribute, the `__get()` method will invoke the callback `exec()` method on the `default_desc_type`, which is set to our shell command.
5. To solve the lab, Base64 and URL-encode the following serialized object, and pass it into the website via your session cookie: `O:14:"CustomTemplate":2:{s:17:"default_desc_type";s:26:"rm /home/carlos/morale.txt";s:4:"desc";O:10:"DefaultMap":1:{s:8:"callback";s:4:"exec";}}`

## Vulnerability note

Underlying issue: Insecure deserialization (CWE-502). Avoid deserializing untrusted data; use allowlists, signing, and safer formats like JSON with schema validation.
