# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

For authorized testing, explain: Web Application Hacker's Handbook 2e — Potentially Dangerous APIs

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Potentially Dangerous APIs):

Potentially Dangerous APIs
               This section describes some common Java APIs that can introduce security
               vulnerabilities if used in an unsafe manner.

               File Access
               The main class used to access ﬁles and directories in Java is java.io.File.
               From a security perspective, the most interesting uses of this class are calls to
               its constructor, which may take a parent directory and ﬁlename, or simply a
               pathname.
                  Whichever form of the constructor is used, path traversal vulnerabilities
               may exist if user-controllable data is passed as the ﬁlename parameter without
               checking for dot-dot-slash sequences. For example, the following code opens a
               ﬁle in the root of the C:\ drive on Windows:
                 String userinput = “..\\boot.ini”;
                 File f = new File(“C:\\temp”, userinput);

                 The classes most commonly used for reading and writing ﬁle contents in
               Java are:
                  n    java.io.FileInputStream
                  n    java.io.FileOutputStream
                  n    java.io.FileReader
                  n    java.io.FileWriter

                 These classes take a File object in their constructors or may open a ﬁle
               themselves via a ﬁlename string, which may again introduce path traversal
               vulnerabilities if user-controllable data is passed as this parameter. For example:
                 String userinput = “..\\boot.ini”;
                 FileInputStream fis = new FileInputStream(“C:\\temp\\” + userinput);

c19.indd 713                                                                                         8/19/2011 12:18:35 PM

                                                                       Stuttard c19.indd V2 - 08/11/2011 Page 714

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.
