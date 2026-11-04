# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

I'm preparing a bug bounty test plan covering Web Application Hacker's Handbook 2e — Chapter 5 n Bypassing Client-Side Controls            141. What does the source recommend?

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Chapter 5 n Bypassing Client-Side Controls            141):

from within Burp. The most reliable way to do this is to select the Headers tab
                 within the response viewer, right-click the lower pane containing the response
                 body, and select Copy to File from the context menu.

               Decompiling the Bytecode
               Bytecode usually is distributed in a single-ﬁle package, which may need to be
               unpacked to obtain the individual bytecode ﬁles for decompilation into source
               code.
                 Java applets normally are packaged as .jar (Java archive) ﬁles, and Silverlight
               objects are packaged as .xap ﬁles. Both of these ﬁle types use the zip archive
               format, so you can easily unpack them by renaming the ﬁles with the .zip
               extension and then using any zip reader to unpack them into the individual ﬁles
               they contain. The Java bytecode is contained in .class ﬁles, and the Silverlight
               bytecode is contained in .dll ﬁles. After unpacking the relevant ﬁle package,
               you need to decompile these ﬁles to obtain source code.
                 Flash objects are packaged as .swf ﬁles and don’t require any unpacking
               before you use a decompiler.
                 To perform the actual bytecode decompilation, you need to use some speciﬁc
               tools, depending on the type of browser extension technology that is being used,
               as described in the following sections.

               Java Tools

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report.
