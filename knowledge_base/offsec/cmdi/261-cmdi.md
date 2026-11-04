# CMDI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: cmdi
- cwe: CWE-20

## Scenario

What payloads or techniques are useful when testing API fuzzing and parameter mutation, especially regarding parameter mutation [Ch 9: API Fuzzing]?

## Analysis / Response

## Overview
208 Chapter 9 replacement of your choice. Importantly, if you were attacking the Pixi API, for example, you might notice that many placeholder parameters use tags like <email>, and replace with either with legitimate ones or one of your fuzzing vari Next, try creating a simple test in the Tests panel to help you detect anomalies.

## Key points
A useful way to think about this is that for instance, you could set up the test covered in Chapter 4 for a status code of 200 across a collection: With this test, Postman will check that responses have a status code of 200, and when a response is 200, it will pass the test. From a tester's perspective, you can easily customize this test by replacing 200 with your preferred status code. There are several ways to launch the Collection Runner. You can click the Runner Overview button, the arrow next to a collection, or the Run button.

## Approach
1. A useful way to think about this is that for instance, you could set up the test covered in Chapter 4 for a status code of 200 across a collection: With this test, Postman will check that responses have a status code of 200, and when a response is 200, it will pass the test.
2. From a tester's perspective, you can easily customize this test by replacing 200 with your preferred status code.
3. There are several ways to launch the Collection Runner.
4. You can click the Runner Overview button, the arrow next to a collection, or the Run button.
5. During authorized testing, as mentioned earlier, you’ll need to develop a baseline of normal responses by sending requests with no values or expected values to the targeted field.

## Example
```
<number>, <string>, and <boolean>. This makes it easy to search for these values
ables, like {{fuzz1}}.
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});
```

## Scope & safety
Confirm findings on your own test accounts whenever possible and prefer non-destructive proofs.
