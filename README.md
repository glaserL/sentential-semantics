# sentential-semantics

PropBank-based SRL with RRG-based macro (core) roles and human-readable labels

## Idea: Revised sentential

Idea is to develop a vocabulary that builds on FrameNet, PropBank, NomBank, VerbNet and PrepWiki, but one that is closer to syntax , that uses a smaller and interpretable inventory of roles and a clear-cut (i.e., syntactically defined) distinction between core roles and modifiers.

- designed primarily for accusative languages
- the replacement for core roles are RRG ACTOR (`ARG0`: proto-subject), UNDERGOER (`ARG1`: proto-object) and THEME (`ARG2`: third argument, indirect object)
- all other roles are identified by human-readable labels, we do not distinguish core roles and modifiers, but macro roles and semantic role labels
- role labels are based on PropBank labels (optional in PropBank)
- abandon sense/predicate differences, instead, we assume that different senses require different roles. Underspecification is not sufficient to distinguish different senses.
- reduce SRL span annotations to head annotation
- seamless integration with CoNLL-U format (as `DEPS` annotation)

## Building

Current SSRL derived corpus is in `data/export`

Make sure to install python requirements in `requirements.txt`
See `Makefile`, for further information on the conversion of annotated corpora to sentential semantics based SRL: see in sub-folders:

    * `data/pmb/` manually corrected Gold subcorpus of the Parallel Meaning Bank (constructed examples) => sentential semantics based SRL edition, see there
