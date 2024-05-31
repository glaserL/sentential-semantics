#!/bin/bash
# call without args in the local directory

preferred_source="consolidated silver transformed"

for dir in ../pmb; do
	tgt=./$(basename $dir)
	for key in $preferred_source; do
		if [ ! -e $tgt ]; then
			src=$(find $dir | egrep 'conll$|conllu$' | egrep -m 1 $key/ | sed s/$key'\/.*'/$key'\/'/)
			if [ -n $src ]; then
				mkdir $tgt
				for file in $src/*conll $src/*conllu; do
					if [ -e $file ]; then
						tgtfile=$tgt/$(basename $file | sed s/'conllu$'/'conll'/)
						echo $file ">" $tgtfile 1>&2
						cat $file | (
							cd ../../scripts/
							bash -e ./ssrl2on_formatted.sh
						) >$tgtfile
					fi
				done
				rmdir $tgt >&/dev/null
			fi
		fi
	done
done
