# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

How do I apply 'From Day Zero to Zero Day — Mapping Code to Attack Surface: Unfortunately, this meant there was a window of opportunity for an-' when testing an in-scope web application?

## Analysis / Response

Based on From Day Zero to Zero Day (web-relevant) (Unfortunately, this meant there was a window of opportunity for an-):

Unfortunately, this meant there was a window of opportunity for an-
                 other user to create the /tmp/.iroha_unix directory with world-writable per-
                 missions. Previously, this directory was configured in systemd to be created
                 by the root user at startup, leaving no chance for a low-privileged attacker
                 to override it. If Canna created a socket in the directory, an attacker could
                 replace it with their own controlled socket, effectively creating a man-in-the-
                 middle attack to intercept Japanese language user input in the operating
                 system.
                      UDSs provide one mechanism to prevent such attacks, as described in
                 the unix(7) Linux manual page: “UNIX domain sockets support passing file
                 descriptors or process credentials to other processes using ancillary data.”
                 This feature allows sockets to identify the sending process when receiving a
                 message by accepting additional data in the struct ucred format:

                 struct ucred {
                     pid_t pid;    /* Process ID of the sending process */
                     uid_t uid;    /* User ID of the sending process */
                     gid_t gid;    /* Group ID of the sending process */
                 };

Use only on systems you are authorized to test; capture evidence and include remediation.
