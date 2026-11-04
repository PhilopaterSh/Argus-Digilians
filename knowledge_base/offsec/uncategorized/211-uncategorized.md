# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

Walk me through compromising the box 'Bashed' from recon to root.

## Analysis / Response

### nmap
`nmap -sC -sV 10.10.10.68 -o Bashed.nmap`
```
Starting Nmap 7.80 ( https://nmap.org ) at 2020-11-23 05:01 EST
Nmap scan report for 10.10.10.68
Host is up (0.051s latency).
Not shown: 999 closed ports
PORT   STATE SERVICE VERSION
80/tcp open  http    Apache httpd 2.4.18 ((Ubuntu))
|_http-server-header: Apache/2.4.18 (Ubuntu)
|_http-title: Arrexel's Development Site

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 8.87 seconds
```
* Looks like we only have port 80 with apache running
