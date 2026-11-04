# RESOURCE — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: resource
- cwe: CWE-190

## Scenario

In the context of 'Abstract Syntax Notation (ASN.1)', what should I know about Constrained and Semiconstrained Lengths when performing a design or code-level security review?

## Analysis / Response

From a software security assessment perspective (Chapter 16: Network Application Protocols — Abstract Syntax Notation (ASN.1)), here is how auditors handle Constrained and Semiconstrained Lengths.

A constrained length is encoded as a bit field; its size varies depending on the range
of lengths that can be supplied. There are several different ways to encode
constrained lengths, depending on the range. The length is encoded as "length lower

bound," which conserves space and prevents users from being able to specify illegal
length values for constrained numbers. In general, a constrained length is encoded by
determining the range of values (per the ASN.1 specification for the data being
transmitted), and then using a bit field that's the exact size required to represent that
range. For example, say a field can be between 1,000 and 1,008 bytes. The range of
lengths that can be supplied is 8, so the bit field would be 3 bits.

Note

This discussion is a slight oversimplification of how constrained lengths are encoded,
but it's fine for the purposes of this chapter. Interested readers can refer to Clause
10.5 of the PER specification (X.691-0207) for full details.

PER implementations can have a variety of integer-related issues, as in BER. The
problems in PER are a little more restricted, however, especially for constrained
values. Even for unconstrained lengths, you're limited to sending sequences of 64KB
chunks, which can prevent integer overflows from occurring. Implementations that
make extensive use of 16-bit integers are definitely at high risk, however, as they can
be made to wrapparticularly because the length attribute might represent a count of
elements (so an allocation would multiply the count by the size of each element).
Errors in decoding lengths could also result in integer overflows of 16-bit integers.
Specifically, unconstrained lengths allow you to specify large blocks of data in 64KB
chunks, and each chunk has a size determined by getting the bottom 6 bits of the
octet and multiplying it by 16KB. You're supposed to encode only a value of 1 to 4, but
the implementation might not enforce this rule, as in the following example:

#define LENGTH_16K (1024 * 16)

unsigned short decode_length(PER_BUFFER *buffer)
{
 if(GetBits(buffer,1) == 0)
 return GetBits(buffer, 7);
 if(GetBits(buffer,1) == 0)
 return GetBits(buffer, 14);
 return GetBits(buffer, 6) * LENGTH_16K;
}

unsigned char *decode_octetstring(PER_BUFFER *buffer)
{
 unsigned char *bytes;
 unsigned long length;

length = decode_length(buffer);

bytes = (unsigned char *)calloc(length+1,
 sizeof(unsigned char));

if(!bytes)
 return NULL;

decode_bytes(bytes, buffer, length);

return bytes;
}

In this example, no verification is done to ensure that the low 6 bits of a large object
encode only a value between 1 and 4 (inclusive). By specifying a larger value, the
multiplication of 16KB causes truncation of the high 16 bits of the result (because
decode_length() returns a 16-bit integer).

Another thing to be wary of is checking return values incorrectly. Take a look at the
previous example modified slightly:

#define LENGTH_16K (1024 * 16)

int decode_length(PER_BUFFER *buffer)
{
 if(bytes_left(buffer) <= 0)
 return -1;
 if(GetBits(buffer,1) == 0)
 return GetBits(buffer, 7);
 if(GetBits(buffer,1) == 0){
 if(bytes_left(buffer) < 2)
 return -1;
 return GetBits(buffer, 14);
 }
 return GetBits(buffer, 6) * LENGTH_16K;
}

unsigned char *decode_octetstring(PER_BUFFER *buffer)
{
 unsigned char *bytes;
 unsigned long length;

length = decode_length(buffer);

bytes = (unsigned char *)calloc(length+1,
 sizeof(unsigned char));

if(!bytes)
 return NULL;

decode_bytes(bytes, buffer, length);

return bytes;
}

In this example, you can't trigger a 16-bit integer wrap because decode_length()
returns an integer; however, the function now returns -1 on error, which isn't checked
for. In fact, if an error is returned, the -1 is passed as a length to calloc(). It's then
added to 1, resulting in 0 bytes allocated, followed by a large copy in decode_bytes().
