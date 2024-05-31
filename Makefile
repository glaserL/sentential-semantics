propbank-mapping:
	@test -d propbank-frames || git clone https://github.com/propbank/propbank-frames
	python3 scripts/convert-pb-frames.py propbank-frames/frames/*.xml  > scripts/propbank-mapping.json
	python3 scripts/convert-pb-frames.py propbank-frames/frames/*.xml  -o nt > scripts/propbank-mapping.nt

lib/conll-rdf/target:
	@test -d lib/conll-rdf || git clone https://github.com/acoli-repo/conll-rdf lib/conll-rdf
	(cd lib/conll-rdf; ./compile.sh)

data/pmb/silver: lib/conll-rdf/target propbank-mapping
    (cd data/pmb; make)

data/export: data/pmb/silver
	(cd data/export; ./build.sh)
