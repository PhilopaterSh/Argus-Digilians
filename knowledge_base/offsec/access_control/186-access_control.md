# ACCESS_CONTROL — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: access_control
- cwe: CWE-284

## Scenario

In the context of 'COM', what should I know about HKEY_LOCAL_MACHINE\SOFTWARE\Classes\CLSID\<GUID of control when performing a design or code-level security review?

## Analysis / Response

From a software security assessment perspective (Chapter 12: Windows II: Interprocess Communication — COM), here is how auditors handle HKEY_LOCAL_MACHINE\SOFTWARE\Classes\CLSID\<GUID of control.

class>\Implemented Categories\<GUID of category>. The safe for scripting category
GUID is {7DD95801-9882-11CF-9FA9-00AA006C42C4}, and the safe for
initialization category GUID is {7DD95802-9882-11CF-9FA9-00AA006C42C4}.

The second approach to marking a control as safe requires that the control implement
the IObjectSafety interface, which exposes the GetInterfaceSafetyOptions() method
to the hosting container. The hosting container calls this method to determine
whether a specific interface is marked as safe for scripting or initialization and can
also request that the control be marked as safe by calling the
IObjectSafety.SetInterfaceSafetyOptions() method.

Any control marked as safe for scripting can be instantiated and manipulated in
Internet Explorer. Microsoft advises marking a control as safe for scripting only if it
must be manipulated from Internet Explorer and doesn't provide any means for
unauthorized parties to alter the state of the local system or connected systems. This
guidance is given because a safe for scripting control exposes its methods to any site
users view, so attackers can leverage the functionally exposed by a control to exploit
client users. For example, say a scriptable control allows the manipulation of arbitrary
files. This issue might be part of a faulty design or the result of a vulnerability in path
checking. Regardless, it would present an unacceptable vulnerability for an ActiveX
control because it allows any remote attacker to drastically alter the victim's system
after connecting to a malicious Web site. When reviewing ActiveX controls, you need
to treat every scriptable method as attack surface and assess them as you would any
other potentially vulnerable code.

ActiveX controls can also store and retrieve data between instantiations by using the
IPersist interface, which is exposed to controls marked as safe for initialization.
Microsoft advises marking a control as safe for initialization only if it must store
persistent data internal to Internet Explorer and it handles this data properly. A
security vulnerability can occur if the object stores sensitive data and exposes it to an
untrusted source or if a control fails to treat persistent data as data originating from
an untrusted source.

Some people might be a little fuzzy on why a control must be separately marked as
safe for initialization. After all, the control is just a binary, so it can call any Windows
API function on its own. This means it can read the registry or file system without the
need for an IPersist interface, so exposing sensitive data is still a concern. However,
a control can be initialized with parameters provided by a Web site, as shown in this
HTML fragment that instantiates a control:

<OBJECT ID="MyControl"
