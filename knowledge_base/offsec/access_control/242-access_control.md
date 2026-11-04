# ACCESS_CONTROL — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: access_control
- cwe: CWE-269

## Scenario

I'm doing an authorized application security review. Regarding Dropping Supplemental Group Privileges: what does thorough assessment require?

## Analysis / Response

From a software security assessment perspective (Chapter 9: UNIX I: Privileges and Files — Privilege Vulnerabilities), here is how auditors handle Dropping Supplemental Group Privileges.

Programs running as daemons can run into security issues related to dropping
privileges that are a little different from setuid programs. This is because they are
typically started as a privileged user and then assume the role of an unprivileged user
based on user input. In this situation, you have to be cognizant of supplemental group
IDs because if they aren't updated when privileges are dropped, they could leave the
process with access to privileged resources.

Certain implementations of the rsync application contained a vulnerability of this
nature, which is detailed at http://cve.mitre.org/cgi-bin/cvename.cgi?name=. If
rsync runs as a daemon, it starts off with the user ID and groups of the user running
the daemon (typically root). If the rsync daemon needs to operate as an unprivileged
user, it runs the following code:

if (am_root) {
 if (setgid(gid)) {
 rsyserr(FERROR, errno, "setgid %d failed",
 (int) gid);
 io_printf(fd,"@ERROR: setgid failed\n");
 return -1;
 }

if (setuid(uid)) {
 rsyserr(FERROR, errno, "setuid %d failed",
 (int) uid);
 io_printf(fd,"@ERROR: setuid failed\n");
 return -1;
 }

am_root = (getuid() == 0);
 }

This code releases the effective group ID before the effective user ID, so it should
drop those privileges in the correct order. However, this code doesn't drop the

supplementary group privileges! The developers solved this problem by inserting the
following code:

#ifdef HAVE_SETGROUPS
 /* Get rid of any supplementary groups this process
 * might have inherited. */
 if (setgroups(0, NULL)) {
 rsyserr(FERROR, errno, "setgroups failed");
 io_printf(fd, "@ERROR: setgroups failed\n");
 return -1;
 }
#endif
...
 if (setgid(gid)) {

Note that setgroups() works only if you are the superuser and have an effective user
ID of 0. This is another reason it's important to relinquish privileges in the correct
order.
