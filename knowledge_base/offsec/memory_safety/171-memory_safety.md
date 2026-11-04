# MEMORY_SAFETY — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: memory_safety
- cwe: CWE-119

## Scenario

What classes of memory errors commonly become security vulnerabilities in C/C++ software?

## Analysis / Response

Typical security-relevant memory errors include using memory the code does not own (NULL pointer dereferences), using more memory than allocated (buffer overflows), using uninitialized memory, and faulty heap management such as double frees. Incorrect use of explicit memory management and pointer arithmetic is a frequent root cause. Memory corruption is the subcategory where the process or kernel modifies a location it should not, or corrupts that location's state. Many other vulnerability classes exist—logic bugs, XSS, CSRF, SQLi—but classic systems bug hunting often centers on memory errors because they can yield instruction-pointer influence. Demonstrating EIP/RIP/PC influence with a recognizable pattern is a standard way to show that a bug crosses from crash to security impact for an advisory, after which further engineering may or may not be pursued depending on policy and law. Chapter 1 also surveys tools—WinDbg, Immunity/Olly, gdb, mdb, and IDA Pro—and frames memory errors (NULL deref, overflows, uninitialized use, double free) as the diary’s focus, distinct from web-only classes. Instruction-pointer influence (EIP/RIP/PC) is the recurring severity demonstration pattern in later chapters.
