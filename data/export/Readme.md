# Export to traditional SRL formats

At the moment, we only provide conversion to the OntoNotes 5.0 "formatted" (CoNLL/Skel) format (cf. https://github.com/ontonotes/conll-formatted-ontonotes-5.0). When other formats are added, group data folders accordingly.

Note that we follow OntoNotes-2012 terminology and mark the predicate as `V`, also for prepositions and adnominal relations. More correct, however, would be to use `P`.

Build it using

		$> bash -e ./build.sh

> Note that predicate identifiers are derived from LEMMA + POS. Fine-grained lemmata are not supported.
