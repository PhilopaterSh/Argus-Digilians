# RESOURCE — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: resource
- cwe: CWE-400

## Scenario

Help me understand File Limits on FileSystem as it relates to Denial of Service, with the payloads from the field.

## Analysis / Response

**File Limits on FileSystem** — this technique applies to Denial of Service. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

When a process is writing a file on the server, try to reach the maximum number of files allowed by the filesystem format. The system should output a message: `No space left on device` when the limit is reached.

| Filesystem | Maximum Inodes             |
| ---------- | -------------------------- |
| BTRFS      | 2^64 (~18 quintillion)     |
| EXT4       | ~4 billion                 |
| FAT32      | ~268 million files         |
| NTFS       | ~4.2 billion (MFT entries) |
| XFS        | Dynamic (disk size)        |
| ZFS        | ~281 trillion              |

An alternative of this technique would be to fill a file used by the application until it reaches the maximum size allowed by the filesystem, for example it can occur on a SQLite database or a log file.

FAT32 has a significant limitation of **4 GB**, which is why it's often replaced with exFAT or NTFS for larger files.

Modern filesystems like BTRFS, ZFS, and XFS support exabyte-scale files, well beyond current storage capacities, making them future-proof for large datasets.
