# DESER — portswigger_labs_sft

- source: portswigger_labs_sft
- class: deser
- cwe: CWE-502

## Scenario

PortSwigger lab: "Developing a custom gadget chain for Java deserialization". This lab uses a serialization-based session mechanism. If you can construct a suitable gadget chain, you can exploit this lab's insecure deserialization to obtain the administrator's password.

To solve the lab, gain access to the source code and use it to construct a gadget chain to obtain the administrator's password. Then, log in as the `administrator` and delete `carlos`.

You can log in to your own account using the following credentials: `wiener:peter`

Note that solving this lab requires basic familiarity with another topic that we've covered on the Web Security Academy.

Walk me through how to solve it.

## Analysis / Response

This PortSwigger Web Security Academy lab (Expert) covers Insecure deserialization: "Developing a custom gadget chain for Java deserialization".

## Solution steps

1. Log in to your own account and notice the session cookie contains a serialized Java object.
2. From the site map, notice that the website references the file `/backup/AccessTokenUser.java`. You can successfully request this file in Burp Repeater.
3. Navigate upward to the `/backup` directory and notice that it also contains a `ProductTemplate.java` file.
4. Notice that the `ProductTemplate.readObject()` method passes the template's `id` attribute into a SQL statement.
5. Based on the leaked source code, write a small Java program that instantiates a `ProductTemplate` with an arbitrary ID, serializes it, and then Base64-encodes it. Template In case you get stuck, we've also provided a ready-to-use program that you can run instead. If you're using our program, all you need to change is the `"your-payload-here"` string in the `Main.java` file. This instantiates and serializes a new `ProductTemplate` with its `id` set to whatever payload you enter here. The object is then Base64-encoded and output to the console ready for you to copy.
6. Use your Java program to create a `ProductTemplate` with the `id` set to a single apostrophe. Copy the Base64 string and submit it in a request as your session cookie. The error message confirms that the website is vulnerable to Postgres-based SQL injection via this deserialized object.

## Vulnerability note

Underlying issue: Insecure deserialization (CWE-502). Avoid deserializing untrusted data; use allowlists, signing, and safer formats like JSON with schema validation.
