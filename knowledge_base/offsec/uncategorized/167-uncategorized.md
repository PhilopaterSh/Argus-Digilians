# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

How do I test for Web Application Hacker's Handbook 2e — Because the debugger is working at the bytecode level, it can be easily used on an in-scope web application?

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Because the debugger is working at the bytecode level, it can be easily used):

Because the debugger is working at the bytecode level, it can be easily used
               to control and understand the ﬂow of execution. In particular, if source code
               can be obtained through decompilation, breakpoints can be set on speciﬁc
               lines of code, allowing the understanding gained through decompilation to be
               supported by practical observation of the code path taken during execution.
                  Although efﬁcient debuggers are not fully matured for all the browser exten-
               sion technologies, debugging is well supported for Java applets. By far the best
               resource for this is JavaSnoop, a Java debugger that can integrate Jad to decom-
               pile source code, trace variables through an application, and set breakpoints on
               methods to view and modify parameters. Figure 5-6 shows JavaSnoop being
               used to hook directly into a Java applet running in the browser. Figure 5-7
               shows JavaSnoop being used to tamper with the return value from a method.

               Figure 5-6: JavaSnoop can hook directly into an
               applet running in the browser

                 NOTE It’s best to run JavaSnoop before the target applet is loaded.

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.
