#!/bin/bash
# read ssrl data from stdin or args and write OntoNotes "formatted" CoNLL format to stdout
# cf. https://github.com/ontonotes/conll-formatted-ontonotes-5.0 for the format

#
# config
##########

# set to your CoNLL-RDF installation or get it from https://github.com/acoli-repo/conll-rdf
CONLL_RDF=~/conll-rdf
LOAD=$CONLL_RDF/run.sh" CoNLLStreamExtractor '#' "
TRANSFORM=$CONLL_RDF/run.sh' CoNLLRDFUpdater -threads 1 -custom'        # for DEBUGGING (non-parallelized)
# TRANSFORM=$CONLL_RDF/run.sh' CoNLLRDFUpdater -custom'                         # for PRODUCTION mode (parallelized)
WRITE=$CONLL_RDF/run.sh' CoNLLRDFFormatter '

SCRIPTS=`dirname $0`/../../scripts


#
# convert
###########

cat $* | \
$LOAD ID WORD LEMMA UPOS XPOS FEATS HEAD EDGE DEPS MISC \
	-u ssrl2on_formatted.sparql | \
#$WRITE -grammar
# $WRITE -debug
$WRITE -conll DOC SENT_ID ID WORD XPOS PARSE PRED PRED_SENSE EMPTY1 EMPTY2 NER PRED_ARGs EMPTY3
# cat
