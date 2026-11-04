# MEMORY_SAFETY — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: memory_safety
- cwe: CWE-119

## Scenario

From Chapter 16 (Network Application Protocols), section 'Hypertext Transfer Protocol': Explain the key software security issues around Utility Functions. What should a code auditor look for?

## Analysis / Response

From a software security assessment perspective (Chapter 16: Network Application Protocols — Hypertext Transfer Protocol), here is how auditors handle Utility Functions.

Most HTTP servers include a lot of utility functions that have interesting security
implications. In particular, there are functions for URL handlingdealing with URL
components such as ports, protocols, and paths; stripping extraneous paths; dealing
with hexadecimal decoding; protecting against double dots; and so forth. Quite a
large codebase can be required just for dealing with untrusted data, so checking for
buffer overflows and similar problems is certainly worthwhile. In addition, logging
utility functions can be interesting, as most HTTP servers log paths and methods,
which could create an opportunity to perform format string attacks. Here's an
example of some vulnerable code:

int log(char *fmt, ...)
{
 va_list ap;

va_start(ap, fmt);
 vfprintf(logfd, fmt, ap);
 va_end(ap);

return 0;
}

int log_access(char *path, char *remote_address)
{
 char buf[1024];

snprintf(buf, sizeof(buf), "[ %s ]: %s accessed by %s\n",
 g_sname, path, remote_address);

return log(buf);
}

This type of code isn't uncommon (at least it wasn't when format string vulnerabilities
were first brought to public attention). By having multiple layers of functions that take
variable arguments, code can easily be susceptible to format string attacks, and
logging utility functions are one of the most common areas for this code to appear.

Another potential danger area in HTTP occurs when handling input supplied via the
POST method. There are two methods used when supplying data via a POST method: a
simple counted data post and chunked encoding.

In a simple counted data post, a block of data is supplied to the HTTP server in a
message. The size of this data is specified by using the Content-Length header. A
request might look like this:

POST /app HTTP/1.1
Host: 127.0.0.1
Content-Length: 10

1234567890

In this request, the block of data is supplied after the request headers. How this
length value is interpreted, however, could create a serious vulnerability for an HTTP
server. Specifically, you must consider that large values might result in integer
overflows or sign issues (covered in Chapter 6, "C Language Issues").
Here's an example of a simple integer overflow:

char *read_post_data(int sock)
{
 char *content_length, *data;
 size_t clen;

content_length = get_header("Content-Length");

if(!content_length)
 return NULL;

clen = atoi(content_length);

data = (char *)malloc(clen + 1);

if(!data)
 return NULL;

tcp_read_data(s, data, clen);

data[clen] = '\0';

return data;
}

The Content-Length value is converted from a string to an integer and then used to
allocate a block of data. Because the conversion is unchecked, a client could supply
the maximum representable integer. When it's added to in the argument to malloc(),
an integer overflow occurs and a small allocation takes place. The following call to
tcp_read_data() then allows data read from the network to overwrite parts of the
process heap. Also, note that the line in the code that NUL-terminates the
user-supplied buffer writes a NUL byte out of bounds (because clen is 0xFFFFFFFF,
which is equivalent to data[-1]one byte before the beginning of the buffer).

The second issue in dealing with Content-Length header interpretation involves
handling signed Content-Length values. If the length value is interpreted as a
negative number, size calculation errors likely occur, with memory corruption being
the end result. Consider the following code (originally from AOLServer):

typedef struct Request {
 ... other members ...

char *next; /* Next read offset. */
 char *content; /* Start of content. */
 int length; /* Length of content. */
 int avail; /* Bytes avail in buffer. */
 int leadblanks; /* # of leading blank lines read */

... other members ...
} Request;

static int
