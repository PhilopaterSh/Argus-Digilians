# ACCESS_CONTROL — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: access_control
- cwe: CWE-602

## Scenario

How should I approach misplaced trust in client-side JavaScript during an authorized assessment, especially regarding hidden form fields [Ch 5: Misplaced Trust in the Client]?

## Analysis / Response

## Overview
In practice, 'success':True Basically, we have only one handler, FormHandler, which shows the form when we hit the / URL. A useful way to think about this is that the POST function simply receives the username and password.

## Key points
In practice, presumably, we can save this information for our new user. The templates Next, let's work on the client-side code. Create a new file in the templates/ folder and name it mistrust.html. Importantly, as usual, we start with a basic Bootstrap 3 template, which is as follows: error"></span> disabled>Submit</button> <!-- Bootstrap core JavaScript min.js"></script> bootstrap.min.js"></script> There is nothing special about this piece of code.

## Approach
1. In practice, presumably, we can save this information for our new user.
2. When reviewing an application, the templates Next, let's work on the client-side code.
3. Create a new file in the templates/ folder and name it mistrust.html.
4. Importantly, as usual, we start with a basic Bootstrap 3 template, which is as follows: error"></span> disabled>Submit</button> <!-- Bootstrap core JavaScript min.js"></script> bootstrap.min.js"></script> There is nothing special about this piece of code.
5. It is simply a HTML template showing a form.

## Example
```
        def post(self):
            print self.get_argument('username')
            print self.get_argument('password')
            data = {
            }
```

## Scope & safety
If a step could affect availability or other users, pause and check the engagement rules first.
