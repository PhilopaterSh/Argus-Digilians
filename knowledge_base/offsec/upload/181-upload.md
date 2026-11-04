# UPLOAD — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: upload
- cwe: CWE-434

## Scenario

What payloads and steps should I use for .htaccess when working on Upload Insecure Files?

## Analysis / Response

**.htaccess** — this technique applies to Upload Insecure Files. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

Uploading an .htaccess file to override Apache rule and execute PHP.
"Hackers can also use “.htaccess” file tricks to upload a malicious file with any extension and execute it. For a simple example, imagine uploading to the vulnerable server an .htaccess file that has AddType application/x-httpd-php .htaccess configuration and also contains PHP shellcode. Because of the malicious .htaccess file, the web server considers the .htaccess file as an executable php file and executes its malicious PHP shellcode. One thing to note: .htaccess configurations are applicable only for the same directory and sub-directories where the .htaccess file is uploaded."
