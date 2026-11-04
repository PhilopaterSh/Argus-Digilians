# ACCESS_CONTROL — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: access_control
- cwe: CWE-284

## Scenario

Walk me through Web Security for Developers — Permissions: Testing Access Control with practical steps from the source material.

## Analysis / Response

Based on Web Security for Developers (Testing Access Control):

Testing Access Control
It’s important to test your access control system critically. Make sure your
testing procedures genuinely attempt to find holes in your access control
scheme; if you treat it like an attacker would, you’ll be better prepared
when your first real attack occurs.
      Write unit tests that make assertions about who can access certain
resources and, more importantly, who shouldn’t be able to access them. Get
in the habit of writing new unit tests describing access control rules as you
add features to your site. This is especially important if your site has admin-
istrative interfaces, since they’re a common backdoor that attackers exploit
when hacking websites. Listing 11-3 shows a simple unit test in Ruby that
asserts that users must be logged in before performing a sensitive action.

class PostsTest < ApplicationSystemTestCase
  test "users should be redirected to the login page if they are not logged in" do
     visit publish_post_url
     assert_response :redirect
     assert_selector "h1", text: "Login"
  end
end

Listing 11-3: A Ruby unit test that checks if an unauthorized user is redirected to the login
page if they attempt to publish a post
