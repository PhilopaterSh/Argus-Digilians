# CMDI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: cmdi
- cwe: CWE-59

## Scenario

How do issues involving Cryogenic Sleep Attacks arise, and how would you identify and assess them during an authorized review?

## Analysis / Response

From a software security assessment perspective (Chapter 9: UNIX I: Privileges and Files — Temporary Files), here is how auditors handle Cryogenic Sleep Attacks.

Olaf Kirch, a well known security researcher, published an interesting vulnerability
related to reusing temporary files. The following code, which is slightly modified from
Olaf's Bugtraq post (available at http://seclists.org/bugtraq/2000/Jan/0016.html),
represents an idiom for a safe way to open a persistent temporary file:

if (lstat(fname, &stb1) >= 0)
 {
 if (!S_ISREG(stb1.st_mode) ||
 (stb1.st_nlink>1))
 raise_big_stink();

fd = open(fname, O_RDWR);
 if (fd < 0 || fstat(fd, &stb2) < 0)
 raise_big_stink();
 if (stb1.st_ino != stb2.st_ino ||
 stb1.st_dev != stb2.st_dev ||
 stb2.st_nlink>1)
 raise_big_stink();
 }
 else
 {
 fd = open(fname, O_RDWR | O_CREAT | O_EXCL, FMODE);
 if (fd < 0)
 raise_big_stink();
 }

This code represents a reasonably safe idiom for opening a potentially existing file in
a public directory. The code first checks the file with lstat() and stores the results in
the stat buffer structure stb1. If the lstat() fails, indicating that the file doesn't exist,
the code attempts to create the file by using open() with the O_CREAT | O_EXCL flags.
This open() doesn't follow symbolic links in the last path component, and it succeeds
only if it's successful in creating the file.

So if the file doesn't exist, the open() call attempts to create it in a safe fashion. If the
file does exist, it's first analyzed with lstat() to make sure it's not a symbolic link or

hard link. Naturally, attackers could delete or rename the file and replace it with
another file, device file, hard link, or symbolic link immediately after the lstat()
security check. So the program opens the file and uses fstat(), and then uses the
inode and device numbers from the fstat() and lstat() calls to check that the
pathname hasn't been manipulated in the time that has elapsed since the program
first called lstat(). If the pathname hasn't been tampered with, lstat() and fstat()
should both indicate that the file has the same device and inode numbers. Note that
the call to open() in the first block uses the O_RDWR flag, but not O_CREAT, ensuring that
it doesn't create a file accidentally.

This solution seems fairly robust, assuming the application can deal with the file open
failing if tampering is detected. Kirch observed that in some situations, the inode and
device check might be circumvented. Say that attackers create a regular file in the
temporary directory with the filename the program is expecting. This program would
call lstat() on the regular file and learn that it existed and wasn't a symbolic link. Say
attackers then manage to send a job control signal, such as a SIGSTOP, to the
application immediately after the lstat() but before the call to open(). This would be
possible if the program is a setuid root program users had started in their terminal
session.

At this point, attackers would make note of the inode and device of the temporary file
they created. They would then delete that file and wait for a sensitive file to be
created with the same inode and device number. They could simply wait for
something to happen, or they could call other privileged programs in ways designed
to get them to create sensitive files.

As soon as a sensitive file is created with an inode and device number equal to that of
the original file, attackers would create a symbolic link to that file and resume the
program. The program would perform the open() call, which would follow the
symbolic link and open the sensitive file. However, when it analyzes the file, it would
find that the inode and device numbers hadn't changed, so it wouldn't suspect
anything odd was afoot.
