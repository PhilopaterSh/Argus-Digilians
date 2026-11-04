# CMDI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: cmdi
- cwe: CWE-74

## Scenario

What follow-on steps make sense after confirming injection attacks against API parameters (angle: error-based discovery) [Ch 12: API Injection]?

## Analysis / Response

## Overview
The -r option lets you specify the path to the saved request. The -p option lets you specify the exact parameters you’d like to test for SQL injec tion.

## Key points
If you do not specify a parameter to attack, SQLmap will attack every parameter, one after another. Typically, this is great for performing a thorough attack of a simple request, but a request with many parameters can be fairly time-consuming. SQLmap tests one parameter at a time and tells you when a parameter is unlikely to be vulnerable. To skip a parameter, use the CTRL-C keyboard shortcut to pull up SQLmap’s scan options and use the n command to move to the next parameter.

## Approach
1. If you do not specify a parameter to attack, SQLmap will attack every parameter, one after another.
2. Typically, this is great for performing a thorough attack of a simple request, but a request with many parameters can be fairly time-consuming.
3. SQLmap tests one parameter at a time and tells you when a parameter is unlikely to be vulnerable.
4. To skip a parameter, use the CTRL-C keyboard shortcut to pull up SQLmap’s scan options and use the n command to move to the next parameter.
5. A useful way to think about this is that when SQLmap indicates that a certain parameter may be injectable, attempt to exploit it.

## Example
```
                   $ sqlmap -r /home/hapihacker/burprequest1 -p password
                   $ sqlmap -r /home/hapihacker/burprequest1 -p vuln-param –dump-all
$ sqlmap -r /home/hapihacker/burprequest1 -p vuln-param –dump -T users -C password -D helpdesk
```

## Scope & safety
If a step could affect availability or other users, pause and check the engagement rules first.
