# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

What should a web pentester know about From Day Zero to Zero Day — Automated Variant Analysis: This tells you exactly where the patch occurs and, more importantly,?

## Analysis / Response

Based on From Day Zero to Zero Day (web-relevant) (This tells you exactly where the patch occurs and, more importantly,):

This tells you exactly where the patch occurs and, more importantly,
what it patches. In this case, it adds two comparison checks on parser->
m_groupSize to ensure that it’s no larger than (unsigned int)(-1) / 2u ¶ or

                                                          Automated Variant Analysis   89

                 (size_t)(-1) / sizeof(int) ·, the values that you multiply parser->m_groupSize
                 by before passing it as the size argument to the REALLOC macro.
                     Take a moment to analyze the REALLOC macro. In the C programming
                 language, macros are named fragments of code. To find the definition of the
                 REALLOC macro, search for #define REALLOC in the code:

                 #define REALLOC(parser, p, s) (parser->m_mem.realloc_fcn((p), (s)))

                      When compiling the code, the C preprocessor expands all occurrences
                 of REALLOC and their arguments to (parser->m_mem.realloc_fcn((p), (s))). How-
                 ever, this doesn’t confirm whether m_mem.realloc_fcn is equivalent to the
                 realloc standard library function. If you search for realloc_fcn in the code,
                 you’ll find the following:

parserCreate(const XML_Char *encodingName,
             const XML_Memory_Handling_Suite *memsuite, const XML_Char *nameSep,
             DTD *dtd) {
    XML_Parser parser;

     if (memsuite) { ¶
         XML_Memory_Handling_Suite *mtemp;
         parser = (XML_Parser)memsuite->malloc_fcn(sizeof(struct XML_ParserStruct));
         if (parser != NULL) {
              mtemp = (XML_Memory_Handling_Suite *)&(parser->m_mem);
              mtemp->malloc_fcn = memsuite->malloc_fcn;
              mtemp->realloc_fcn = memsuite->realloc_fcn;
              mtemp->free_fcn = memsuite->free_fcn;
         }
     } else {
         XML_Memory_Handling_Suite *mtemp;
         parser = (XML_Parser)malloc(sizeof(struct XML_ParserStruct));
         if (parser != NULL) {
              mtemp = (XML_Memory_Handling_Suite *)&(parser->m_mem);
              mtemp->malloc_fcn = malloc;
              mtemp->realloc_fcn = realloc; ·
              mtemp->free_fcn = free;
         }
     }

                     Unless you pass an alternative memory handling suite to parserCreate ¶,
                 realloc_fcn is assigned as realloc ·. This may seem like a long detour to con-
                 firm your suspicions, but it’s important to be thorough. After all, the REALLOC
                 macro could be a safe wrapper around the realloc function, a common prac-
                 tice by many developers.

Use only on systems you are authorized to test; capture evidence and include remediation.
