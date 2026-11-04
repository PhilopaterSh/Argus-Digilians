# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

Explain the Linux - Privilege Escalation technique for Methodology and Resources and list the concrete payloads I can try.

## Analysis / Response

**Linux - Privilege Escalation** — this technique applies to Methodology and Resources. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

# Linux - Privilege Escalation

:warning: Content of this page has been moved to [InternalAllTheThings/redteam/persistence/linux-persistence](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/)

- [Tools](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#tools)
- [Checklist](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#checklists)
- [Looting for passwords](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#looting-for-passwords)
    - [Files containing passwords](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#files-containing-passwords)
    - [Old passwords in /etc/security/opasswd](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#old-passwords-in-etcsecurityopasswd)
    - [Last edited files](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#last-edited-files)
    - [In memory passwords](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#in-memory-passwords)
    - [Find sensitive files](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#find-sensitive-files)
- [SSH Key](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#ssh-key)
    - [Sensitive files](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#sensitive-files)
    - [SSH Key Predictable PRNG (Authorized_Keys) Process](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#ssh-key-predictable-prng-authorized_keys-process)
- [Scheduled tasks](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#scheduled-tasks)
    - [Cron jobs](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#cron-jobs)
    - [Systemd timers](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#systemd-timers)
- [SUID](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#suid)
    - [Find SUID binaries](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#find-suid-binaries)
    - [Create a SUID binary](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#create-a-suid-binary)
- [Capabilities](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#capabilities)
    - [List capabilities of binaries](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#list-capabilities-of-binaries)
    - [Edit capabilities](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#edit-capabilities)
    - [Interesting capabilities](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#interesting-capabilities)
- [SUDO](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#sudo)
    - [NOPASSWD](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#nopasswd)
    - [LD_PRELOAD and NOPASSWD](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#ld_preload-and-nopasswd)
    - [Doas](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#doas)
    - [sudo_inject](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#sudo_inject)
    - [CVE-2019-14287](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#cve-2019-14287)
- [GTFOBins](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#gtfobins)
- [Wildcard](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#wildcard)
- [Writable files](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#writable-files)
    - [Writable /etc/passwd](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#writable-etcpasswd)
    - [Writable /etc/sudoers](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#writable-etcsudoers)
- [NFS Root Squashing](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#nfs-root-squashing)
- [Shared Library](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#shared-library)
    - [ldconfig](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#ldconfig)
    - [RPATH](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#rpath)
- [Groups](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#groups)
    - [Docker](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#docker)
    - [LXC/LXD](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#lxclxd)
- [Hijack TMUX session](https://swisskyrepo.github.io/InternalAllTheThings/redteam/escalation/linux-privilege-escalation/#hijack-tmux-session)
- [Kernel Ex
