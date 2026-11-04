# MEMORY_SAFETY — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: memory_safety
- cwe: CWE-119

## Scenario

When auditing software for an authorized assessment, how should I approach XML Encoding Rules?

## Analysis / Response

From a software security assessment perspective (Chapter 16: Network Application Protocols — Abstract Syntax Notation (ASN.1)), here is how auditors handle XML Encoding Rules.

XML Encoding Rules (XER) provides a standard for encoding ASN.1 in XML
documents. XML is complex markup language, and basic XML rules aren't covered in
this section. XER is quite different from the other encoding formats; it's a textual
representation of ASN.1 objects, as opposed to the other encoding formats, which are
binary. Therefore, the problems you run into with XER are likely to be far different.

Note

Should you be confronted with the task of auditing an XER implementation, you'll
probably need to analyze the XML implementation to ensure that the code is secure.
After all, if the XML parser is broken, it doesn't matter what XER bugs you might fix
because the underlying XML parser can be attacked directly.

An XER-encoded object consists of two parts: an XML prolog and an XML document
element that describes a single ASN.1 object. The XML document element contains
the actual ASN.1 object data. It's simply encoded by using standard document
element conventions in XML. The XML prolog doesn't have to be used. If it is, it's a
standard XML header tag, which might look like this:

<?xml version = "1.0" encoding="UTF-8">

The most likely vulnerabilities in XER are obviously text-based errorssimple buffer
overflows or pointer arithmetic bugs. When auditing XER implementations,
remember that programs that exchange data by using XER are often exposing a huge
codebase to untrusted data. This applies not just to XER but to the XML
implementation and encoding schemes for transmitting and storing XML data. In
particular, check the UTF encoding schemes for encoding Unicode codepoints, which
are discussed in depth in Chapter 8.
