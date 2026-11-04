# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

What should a web pentester know about Web Security for Developers — Compromising Authentication: Now that we understand what happens when users and web servers?

## Analysis / Response

Based on Web Security for Developers (Now that we understand what happens when users and web servers):

Now that we understand what happens when users and web servers
                  open a session, let’s look at how websites implement these sessions. There
                  are two common implementations, typically described as server-side ses-
                  sions and client-side sessions. Let’s review how these methods work, so you
                  can see where the vulnerabilities occur.

                  Server-Side Sessions
                  In a traditional model of session management, the web server keeps the
                  session state in memory, and both the web server and browser pass the ses-
                  sion identifier back and forth. This is called a server-side session. Listing 10-1
                  shows the Ruby on Rails implementation of server-side sessions.

                  # Get a session from the cache.
                  def find_session(env, sid)
                    unless sid && (session = @cache.read(cache_key(sid))w)

94   Chapter 10

    sid, session = generate_sidu, {}
  end
  [sid, session]
end

# Set a session in the cache.
def write_session(env, sid, session, options)
  key = cache_key(sid)
  if session
 v @cache.write(key, session, expires_in: options[:expire_after])
  else
    @cache.delete(key)
  end
  sid
end

Listing 10-1: Ruby on Rails implements server-side sessions using the session ID (sid).

     The session object is created at u, written to the server’s memory at v,
and then reloaded from memory at w.

Use only on systems you are authorized to test; capture evidence and include remediation.
