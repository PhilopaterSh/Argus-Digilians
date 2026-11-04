# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

What concrete techniques from software security assessment apply when reviewing Cscope?

## Analysis / Response

From a software security assessment perspective (Chapter 4: Application Review Process — Code Auditor's Toolbox), here is how auditors handle Cscope.

Cscope, summarized in Table 4-21, is a useful utility with cross-referencing features
in an easy-to-use text interface and search-and-replace features for making text
substitutions over multiple source files. This utility doesn't offer a satisfactory code
navigation environment because of the limited features it supports, but it's not
designed to be an auditing environment. However, it can be a useful complement to
other products, particularly Ctags, as both products make up for each other's
drawbacks.

Table 4-21. Cscope

Operating system Most UNIX-based operating systems (Linux, BSD, Solaris)

Product requirements None

Free version available Yes

URL http://cscope.sourceforge.net/

Key features Cross-referencing

Text searching and replacing

Ctags

Ctags is an extension of the VIM editor designed for navigating source code. It offers
a number of interesting features, although many features listed in Table 4-22 are
actually part of VIM, not Ctags. It works by generating a file containing locations of
data elements (structures, functions, variables, type definitions, preprocessor
macros, and so on), and then referring to that file when users look up definitions. It's
easy to use (for those familiar with VIM), and when combined with features already in
VIM, it creates a functional code-navigating environment.

Table 4-22. Ctags

Operating system Most UNIX-based operating systems (Linux, BSD, Solaris)

Free version available Yes

URL http://ctags.sourceforge.net/

Key features Multiple language support

Definition lookups

Syntax highlighting

Navigational shortcuts

One of the main drawbacks of Ctags is that occasionally it jumps to the wrong place
during a definition lookup. It might jump to a prototype instead of the actual function,
for example. It can be particularly problem prone when a lot of indirection is involved
in the code being examined. The second main drawback is that it doesn't have

cross-referencing features; however, using this tool with Cscope can work around
that limitation.

Source Navigator

Source Navigator (see Table 4-23) is a GUI IDE developed primarily for use on Linux
(and other UNIX-based OSs), but it also runs on Windows. It offers a rich feature set,
including support for multiple languages, cross-referencing (text as well as pictorial),
text searching, and definition lookups. It's an excellent product because the interface
is simple and fast, and the engine works well. (It doesn't get definition lookups wrong,
as other products sometimes do.)

Table 4-23. Source Navigator
