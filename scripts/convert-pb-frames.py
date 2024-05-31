import os, sys,re,traceback
import xmltodict,json
from pprint import pprint
import argparse
import urllib

formats=["json","json-ld","turtle","nt"]

args=argparse.ArgumentParser(description="load PB frame XML files and return mapping to simplified roles")
args.add_argument("files", action="append", nargs="*", type=str, help="frame files, PropBank xml format")
args.add_argument("-o", "--output_format", type=str, default="json", help="output format defaults to, choose one of "+", ".join(formats)+"; defaults to json")
args=args.parse_args()

if not args.output_format.lower() in formats:
	sys.stderr.write("warning: unsupported output format "+args.output_format+", resort to json\n")
	sys.stderr.flush()
	args.output_format="json"

i=0
while i< len(args.files):
	if type(args.files[i])==list:
		args.files=args.files[0:i]+args.files[i]+args.files[i+1:]
	else:
		i+=1

pred2lemma2pos2pb2tgt2val={}
for file in args.files:
	dict={}
	with open(file,"r") as input:
		try:
			dict=xmltodict.parse(input.read(),force_list=set(['roleset','predicate','alias','vnrole','role']))
			for predicate in dict["frameset"]["predicate"]:
				lemma=predicate["@lemma"]
				if "roleset" in predicate and predicate["roleset"]!=None:
					for roleset in predicate["roleset"]:
							pred=roleset["@id"]
							pred2lemma2pos2pb2tgt2val[pred]={}
							for alias in roleset["aliases"]["alias"]:
								form=alias["#text"]
								pos=alias["@pos"]
								if not form in pred2lemma2pos2pb2tgt2val[pred]:
									pred2lemma2pos2pb2tgt2val[pred][form]={ pos : {} }
								else:
									pred2lemma2pos2pb2tgt2val[pred][form][pos]={}
							if len(pred2lemma2pos2pb2tgt2val[pred])==0:
								pred2lemma2pos2pb2tgt2val[pred][lemma]={ "_": {} }	# shouldn't happen
							if roleset!=None and "roles" in roleset and not roleset["roles"]==None and "role" in roleset["roles"]:
								for lemma in pred2lemma2pos2pb2tgt2val[pred]:
									for pos in pred2lemma2pos2pb2tgt2val[pred][lemma]:
										for role in roleset["roles"]["role"]:
											pb="ARG"+role["@n"].upper()
											tgt=role["@f"].upper()
											pred2lemma2pos2pb2tgt2val[pred][lemma][pos][pb]={"tgt" : tgt }
											if "vnrole" in role:
												for vnrole in role["vnrole"]:
													pred2lemma2pos2pb2tgt2val[pred][lemma][pos][pb]["vn"]=vnrole["@vntheta"].lower()
													break
		except:
					traceback.print_exc()
					sys.stderr.write("while processing "+file+"\n")
					sys.stderr.flush()
					sys.exit()

					
# pprint(pred2lemma2pos2pb2tgt2val)

vn2tgt2freq={}
pb2tgt2freq={}
for pred in pred2lemma2pos2pb2tgt2val:
	for lemma in pred2lemma2pos2pb2tgt2val[pred]:
		for pos in pred2lemma2pos2pb2tgt2val[pred][lemma]:
			for pb in pred2lemma2pos2pb2tgt2val[pred][lemma][pos]:
				tgt=pred2lemma2pos2pb2tgt2val[pred][lemma][pos][pb]["tgt"]
				
				if not pb in pb2tgt2freq:
					pb2tgt2freq[pb]={tgt:1}
				elif not tgt in pb2tgt2freq[pb]:
					pb2tgt2freq[pb][tgt]=1
				else:
					pb2tgt2freq[pb][tgt]+=1
					
				if "vn" in pred2lemma2pos2pb2tgt2val[pred][lemma][pos][pb]:
					vn=pred2lemma2pos2pb2tgt2val[pred][lemma][pos][pb]["vn"]
					if not vn in vn2tgt2freq:
						vn2tgt2freq[vn]={tgt:1}
					elif not tgt in vn2tgt2freq[vn]:
						vn2tgt2freq[vn][tgt]=1
					else:
						vn2tgt2freq[vn][tgt]+=1
						
# pprint(vn2tgt2freq)
# pprint(pb2tgt2freq)

# use VerbNet to overcome VSPs
for pred in pred2lemma2pos2pb2tgt2val:
	for lemma in pred2lemma2pos2pb2tgt2val[pred]:
		for pos in pred2lemma2pos2pb2tgt2val[pred][lemma]:
			for pb in pred2lemma2pos2pb2tgt2val[pred][lemma][pos]:
				tgt=pred2lemma2pos2pb2tgt2val[pred][lemma][pos][pb]["tgt"]
				if tgt=="VSP":
					if "vn" in pred2lemma2pos2pb2tgt2val[pred][lemma][pos][pb]:
						vn=pred2lemma2pos2pb2tgt2val[pred][lemma][pos][pb]["vn"]
						freq=0
						for cand in vn2tgt2freq[vn]:
							if vn2tgt2freq[vn][cand]>freq:
								tgt="*"+cand+"<"+vn
								freq=vn2tgt2freq[vn][cand]
						if tgt.startswith("*VSP"):
							tgt="**"+vn
					
					# post hoc adjustments, as documented
					if tgt in ["**asset", "**value"]:
						tgt="**VAL"+"<"+tgt[2:]
					elif tgt in ["**material"]:
						tgt="**MAT"+"<"+tgt[2:]
					elif tgt in ["**proposition"]:
						tgt="**PRD"+"<"+tgt[2:]

					pred2lemma2pos2pb2tgt2val[pred][lemma][pos][pb]["tgt"]=tgt

# use other predicates of the same lexeme to overcome VSPs
for pred in pred2lemma2pos2pb2tgt2val:
	for lemma in pred2lemma2pos2pb2tgt2val[pred]:
		vsplabel2freq={}
		for pos in pred2lemma2pos2pb2tgt2val[pred][lemma]:
			for pb in pred2lemma2pos2pb2tgt2val[pred][lemma][pos]:
				label= pred2lemma2pos2pb2tgt2val[pred][lemma][pos][pb]["tgt"]
				if label.startswith("*"):
					if not label in vsplabel2freq:
						vsplabel2freq[label]=1
					else:
						vsplabel2freq[label]+=1
		if len(vsplabel2freq)>0:
			for pos in pred2lemma2pos2pb2tgt2val[pred][lemma]:
				for pb in pred2lemma2pos2pb2tgt2val[pred][lemma][pos]:
					tgt=pred2lemma2pos2pb2tgt2val[pred][lemma][pos][pb]["tgt"]
					if tgt=="VSP":
						freq=0
						for cand in vsplabel2freq:
							if vsplabel2freq[cand]>freq:
								tgt="("+cand+")"
								freq=vsplabel2freq[cand]

						pred2lemma2pos2pb2tgt2val[pred][lemma][pos][pb]["tgt"]=tgt

# pprint(pred2lemma2pos2pb2tgt2val)
						
# production mode, prune (drop non-characters from labels, drop VerbNet)
pred2lemma2pos2pb2val={}
for pred in pred2lemma2pos2pb2tgt2val:
	pred2lemma2pos2pb2val[pred]={}
	for lemma in pred2lemma2pos2pb2tgt2val[pred]:
		pred2lemma2pos2pb2val[pred][lemma]={}
		for pos in pred2lemma2pos2pb2tgt2val[pred][lemma]:
			pred2lemma2pos2pb2val[pred][lemma][pos]={}
			for pb in pred2lemma2pos2pb2tgt2val[pred][lemma][pos]:
				val = re.sub(r"^[^A-Z]*([A-Z]+)[^A-Z].*",r"\1",pred2lemma2pos2pb2tgt2val[pred][lemma][pos][pb]["tgt"].upper())
				pred2lemma2pos2pb2val[pred][lemma][pos][pb]=val

# pprint(pred2lemma2pos2pb2val)

# uri encode
if not args.output_format=="json":
	tmp={}
	for pred in pred2lemma2pos2pb2val:
		for lemma in pred2lemma2pos2pb2val[pred]:
			for pos in pred2lemma2pos2pb2val[pred][lemma]:
				for pb in pred2lemma2pos2pb2val[pred][lemma][pos]:
					myp=urllib.parse.quote(pred)
					myl=urllib.parse.quote(lemma)
					val=pred2lemma2pos2pb2val[pred][lemma][pos][pb]
					if not myp in tmp:
						tmp[myp]={ myl: { pos : { pb : val }}}
					elif not myl in tmp[myp]:
						tmp[myp][myl]= { pos : { pb : val }}
					elif not pos in tmp[myp][myl]:
						tmp[myp][myl][pos] = { pb : val }
					else:
						tmp[myp][myl][pos][pb]=val
	pred2lemma2pos2pb2val=tmp

# pprint(pred2lemma2pos2pb2val)
				
# convert to lemma2pred2pos2pb2val
result={}
for pred in pred2lemma2pos2pb2val:
	for lemma in pred2lemma2pos2pb2val[pred]:
		if not lemma in result:
			result[lemma]={pred : pred2lemma2pos2pb2val[pred][lemma] }
		else:
			result[lemma][pred] = pred2lemma2pos2pb2val[pred][lemma]
				
# output
context={ "@vocab" : "http://purl.org/acoli/open-ie/srl/" }
if args.output_format.startswith("json"):
	if args.output_format=="json-ld":
		tmp = { "@context" : context }
		tmp.update(result)
		result=tmp
	print(json.dumps(result,indent=2))
else:
	from rdflib import Graph, plugin
	import json, rdflib_jsonld
	from SPARQLWrapper import SPARQLWrapper
	from rdflib.plugin import register, Serializer
	register('json-ld', Serializer, 'rdflib_jsonld.serializer', 'JsonLDSerializer')

	g = Graph()
	g.parse(data=json.dumps(result), format='json-ld',context=context)
	print(g.serialize(format=args.output_format).decode())
	g.close()
