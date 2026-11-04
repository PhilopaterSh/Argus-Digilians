# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized
- cwe: CWE-134

## Scenario

Explain the common techniques and commands for Format String Vulnerabilities.

## Analysis / Response

#### Format String Vulnerabilities

- Look at Table 2 for what to try if you see "printf(buf)" or something like that:
    - [https://owasp.org/www-community/attacks/Format_string_attack](https://owasp.org/www-community/attacks/Format_string_attack)
- Highly recommend looking at John Hammond doing 'echooo' challenge from picoCTF 2018
- Sometimes, trying to print only strings from the stack like this: '%s %s %s %s %s %s' may cause errors since not everything in the stack is a string.
- Try to minimize that by doing '%x %x %x %x %x %s' instead
- Instead of having to constantly increase how many %x and %s you type, you can pass a parameter to make it easier:
    - `%1$s` - This will print the first value in the stack (from what I understand, the one right next to your buffer) as a string.
    - `%2$s` - This will print the 2nd value as a string, and you get the idea
    - You can use one-liner loops to try to find the flag by leaking the stack. Press ^C (CTRL + C) to go to the next value.
        - `for i in {1..100}; do echo "%$i\$s" | nc [b7dca240cf1fbf61.247ctf.com](http://b7dca240cf1fbf61.247ctf.com/) 50478; done`
- You can control how much you leak using different size parameters:
    - `%hhx` leaks 1 byte (half of half of int size)
    - `%hx` leaks 2 bytes (half of int size)
    - `%x` leaks 4 bytes (int size)
    - `%lx` leaks 8 bytes (long size)
- very good video on modifying the stack with fstring vuln and %n:
    - [https://www.youtube.com/watch?v=gzLPVkZbaPA&ab_channel=MartinCarlisle](https://www.youtube.com/watch?v=gzLPVkZbaPA&ab_channel=MartinCarlisle)

#### Shellcode

- Good website to find different shellcode:
    - [http://shell-storm.org/shellcode/](http://shell-storm.org/shellcode/)
