# SQLI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: sqli
- cwe: CWE-89

## Scenario

In the context of 'ASP', what important patterns and pitfalls related to Command.ActiveConnection = Connection should auditors watch for in application reviews?

## Analysis / Response

From a software security assessment perspective (Chapter 18: Web Technologies — ASP), here is how auditors handle Command.ActiveConnection = Connection.

querystr = "SELECT * FROM users WHERE name='" & user & "'"

cmd.CommandText = querystr
 Command.Execute

A third common way to run a SQL query is for the application to create a RecordSet
object and then call the Open() method, as shown in the following code:

user = Request.Form("username")

querystr = "SELECT * FROM users WHERE name='" & user & "'"

Set rs = Server.CreateObject("ADODB.Recordset")
 rs.Open querystr, "DSN=

All three of these types of statements are vulnerable to SQL injection attacks when
handling user supplied data, so you should look for any instances of their use. ADO
also supports parameterized queries via the Command object. You can identify these
queries by the ? placeholder in the query string and the use of the CreateParameter()
method to add bound parameters.

For the sake of thoroughness, when auditing an ASP application for SQL problems,
you will also want to search for specific strings to try to find all the database
interaction code. Good search candidates are SQL substrings, such as INSERT, SELECT,
or WHERE, as well as methods that manipulate the database, such as Execute() or
Open().

ASP access to the file system is usually performed with the
Scripting.FileSystemObject object, which defines a number of methods for standard
file manipulation tasks, such as creating, deleting, reading, writing, and renaming
files. When performing a security audit, examine every use of the FileSystemObject,
as most of the methods have security consequences if user input is involved. Here's
an example of a problem-prone attempt to write a file with the CreateTextFile()
method:

username = Request.Form("username")

path = server.MapPath("/profiles/")

Set objFSO = Server.CreateObject("Scripting.FileSystemObject")
Set objFSOFile = objFSO.CreateTextFile(path + "\" + username)

This example is vulnerable to a direct path traversal attack, allowing an attacker to
create an arbitrary text file on the system. The NUL-byte issue affects ASP code as
well, so attackers can easily circumvent code that appends a suffix or file extension to
a user-supplied filename. This code also demonstrates a good method for identifying
locations that handle user supplied paths. The Server.MapPath() function is commonly
used when manipulating file paths. It's responsible for converting a path in the Web
tree into a real physical drive path. Therefore, it ends up being used in most code
dealing with the file system, even if that code uses a mechanism other than

FileSystemObject. In practice, you can find most file system manipulation code by
performing a non-case-sensitive search for FileSystemObject, MapPath, and filename.
