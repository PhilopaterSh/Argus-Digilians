# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

Walk through the 'gobuster' part of solving 'Blogger'.

## Analysis / Response

### gobuster

`gobuster dir -u http://192.168.211.217/ -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -t 100`
```
===============================================================
Gobuster v3.3
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@firefart)
===============================================================
[+] Url:                     http://192.168.211.217/
[+] Method:                  GET
[+] Threads:                 100
[+] Wordlist:                /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
[+] Negative Status codes:   404
[+] User Agent:              gobuster/3.3
[+] Timeout:                 10s
===============================================================
2023/05/08 22:48:01 Starting gobuster in directory enumeration mode
===============================================================
/assets               (Status: 301) [Size: 319] [--> http://192.168.211.217/assets/]
/css                  (Status: 301) [Size: 316] [--> http://192.168.211.217/css/]
/js                   (Status: 301) [Size: 315] [--> http://192.168.211.217/js/]
/images               (Status: 301) [Size: 319] [--> http://192.168.211.217/images/]
/server-status        (Status: 403) [Size: 280]
===============================================================
2023/05/08 22:50:46 Finished
===============================================================

```
The directories seem to have directory listing enabled.

One particularly interesting directory is `/assets/fonts/`, as it has a blog directory with a whole new website (which is quite unusual)

Here, we can see a wordpress blog with a login form. Some of the pages also leak the hostname as `blogger.thm`

# Exploitation
