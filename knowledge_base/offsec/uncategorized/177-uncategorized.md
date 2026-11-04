# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

Explain the common techniques and commands for Web.

## Analysis / Response

## Web

- [Nikto](https://tools.kali.org/information-gathering/nikto) (if allowed)
    - automatically looks for vulnerabilities
- [gobuster](https://tools.kali.org/web-applications/gobuster) (if allowed)
    - Brute forces directories and files
- [hydra](https://tools.kali.org/password-attacks/hydra) (if allowed)
    - Brute forces logins for various services
- [BurpSuite](https://portswigger.net/burp)
    - Intercepts web requests and allows you to modify them
- [Wireshark](https://www.wireshark.org/)
    - Analyze live network traffic and pcap files
- [php reverse shell](https://raw.githubusercontent.com/pentestmonkey/php-reverse-shell/master/php-reverse-shell.php)
    - Useful for websites that allow you to upload files
    - This file needs to be executed on the server to work
- [WPScan](http://wpscan.com)
    - Scan wordpress websites
    - Use `wpscan --url <site> --plugins-detection mixed -e` with an api key for best results
- [jwt](https://jwt.io/)
    - You can identify a JWT token since base64-encoded json (and thus jwt tokens) begins with "ey"
    - This site will decode JSON web tokens
    - You can crack the secret for the JSON web token to modify and sign your own tokens
        - `echo <token> > jwt.txt`
        - `john jwt.txt`
- SQL injection
    - sqlmap
        - `sqlmap --forms --dump-all -u <url>`
        - Automates the process of SQL injection
    - Basic SQL injection
        - Enter `'OR 1=1--` in login form
        - On the server this will evaluate to `SELECT * FROM Users WHERE User = '' OR 1=1--'  AND Pass = ''`
        - `1=1` evaluates to true, which satisfies the `OR` statement, and the rest of the query is commented out by the `--`
- [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings)
    - Great resource for web exploitation with lots of payloads
- Template Injection
    - [tplmap](https://github.com/epinna/tplmap)
        - Automated server-side template injection
    - Jinja Injection
        - \{\{ config.items() \}\}
    - Flask Injection
        - \{\{ config \}\}
    - Python eval() function
        - `__import__.('subprocess').getoutput('<command>')`
            - make sure to switch the parentheses if it doesn't work
        - `__import__.('subprocess').getoutput('ls').split('\\n')`
            - list files in system
    - [More python injection](https://medium.com/swlh/hacking-python-applications-5d4cd541b3f1)
- Cross Site Scripting
    - [CSP Evaluator](https://csp-evaluator.withgoogle.com/)
        - Google's Content Security Policy Evaluator
