# CMDI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: cmdi
- cwe: CWE-78

## Scenario

I'm doing an authorized application security review. Regarding Incrementing Pointers Incorrectly (part 2): what does thorough assessment require?

## Analysis / Response

From a software security assessment perspective (Chapter 8: Strings and Metacharacters — C String Handling), here is how auditors handle Incrementing Pointers Incorrectly (part 2).

The third example of incrementing outside a buffer's bounds usually occurs when
programmers make assumptions on the content of the buffer they're parsing. An
attacker can use intentionally malformed data to take advantage of these
assumptions and force the program into doing something it shouldn't. Say you have

a string containing variables submitted by a form from a Web site, and you want to
parse and store these variables. This process involves decoding hexadecimal
sequences in the form %XY; X and Y are hexadecimal characters (09, af, and AF)
representing a byte value. If the application fails to ensure that one of the two
characters following the % is a NUL terminator, the application might attempt to
decode the hexadecimal sequence and then skip the NUL byte and continue
processing on uninitialized memory. Listing 8-5 shows an example of this error.

Listing 8-5. Vulnerable Hex-Decoding Routine for URIs
/*
 * Decoding URI-encoded strings
 */
void
nmz_decode_uri(char *str)
{
 int i, j;
 for (i = j = 0; str[i]; i++, j++) {
 if (str[i] == '%') {
 str[j] = decode_uri_sub(str[i + 1], str[i + 2]);
 i += 2;
 } else if (str[i] == '+') {
 str[j] = ' ';
 } else {
 str[j] = str[i];
 }
 }
 str[j] = '\0';
}

This code contains a simple mistake in the bolded line: The developer makes the
assumption that two valid characters follow a % character, which also assumes that
the string doesn't terminate in those two bytes. Strings can often have a more
complicated structure than the developer expects, however. Because there are
multiple state variables that affect how the parsing function interprets text, there are
more possibilities to make a mistake such as this one. Listing 8-6 shows another
example of this type of error. It's taken from the mod_dav Apache module and is used
to parse certain HTTP headers.

Listing 8-6. If Header Processing Vulnerability in Apache's mod_dav Module
while (*list) {
 /* List is the entire production (in a URI scope) */
switch (*list) {

case '<':
 if ((state_token = dav_fetch_next_token(&list, '>'))
 == NULL) {
 /* ### add a description to this error */
 return dav_new_error(r->pool, HTTP_BAD_REQUEST,
 DAV_ERR_IF_PARSE, NULL);
 }
 if ((err = dav_add_if_state(r->pool, ih, state_token,

dav_if_opaquelock, condition, locks_hooks))
 != NULL) {
 /* ### maybe add a higher level description */
 return err;
 }
 condition = DAV_IF_COND_NORMAL;
 break;

case 'N':
 if (list[1] == 'o' && list[2] == 't') {
 if (condition != DAV_IF_COND_NORMAL) {
 return dav_new_error(r->pool, HTTP_BAD_REQUEST,
 DAV_ERR_IF_MULTIPLE_NOT,
 "Invalid \"If:\" header: "
 "Multiple \"not\" entries "
 "for the same state.");
 }
 condition = DAV_IF_COND_NOT;
 }
 list += 2;
 break;

case ' ':
case '\t':
 break;

default:
 return dav_new_error(r->pool, HTTP_BAD_REQUEST,
 DAV_ERR_IF_UNK_CHAR,
 apr_psprintf(r->pool,
 "Invalid \"If:\" "
 "header: Unexpected "
 "character encountered "
 "(0x%02x, '%c').",
 *list, *list));

}
 list++;
}
break;

This code fails to check for NUL terminators correctly when it encounters an N
character. The N case should check for the presence of the word "Not" and then skip
over it. However, the code skips over the next two characters anytime it encounters
an N character. An attacker can specify a header string ending with an N character,
meaning an N character followed by a NUL character. Processing will continue past the
NUL character to data in memory adjacent to the string being parsed. The vulnerable
code path is demonstrated by the bolded lines in the listing.
