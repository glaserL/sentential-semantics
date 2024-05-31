import sys,os,re,traceback,json,argparse

# call without args, return statistics for the overall corpus

corpus2files={
	"ewt" : [ "ewt/silver/dev.conllu", "ewt/silver/test.conllu", "ewt/silver/train.conllu" ],
	"streusle" : [ "streusle/transformed/dev.conllu", "streusle/transformed/test.conllu", "streusle/transformed/train.conllu"],
	"framenet" : [ "framenet/silver/framenet.corpus.conll" ],
	"amr" : [ "amr/silver/amr-release-bio-v3.0.txt.conllu", "amr/silver/amr-bank-struct-v3.0.txt.conllu"],
	"amr-bio" : [ "amr/silver/amr-release-bio-v3.0.txt.conllu"],
	"amr-lpp" : [ "amr/silver/amr-bank-struct-v3.0.txt.conllu"],
	"pmb" : ["pmb/silver/pmb-4.0.0.en.gold.conll"],
	"ibm-propbanks" : [ "ibm-propbanks/silver/contracts_proposition_bank.conllu", "ibm-propbanks/silver/finance_proposition_bank.conllu" ],
	"pb": [ "ewt/silver/dev.conllu", "ewt/silver/test.conllu", "ewt/silver/train.conllu", "ibm-propbanks/silver/contracts_proposition_bank.conllu", "ibm-propbanks/silver/finance_proposition_bank.conllu" ],
	"ibm-finprop" : [ "ibm-propbanks/silver/finance_proposition_bank.conllu" ],
	"ibm-conprop" : [ "ibm-propbanks/silver/contracts_proposition_bank.conllu" ],
	"all": 	[ 	"ewt/silver/dev.conllu", "ewt/silver/test.conllu", "ewt/silver/train.conllu", 
				"streusle/transformed/dev.conllu", "streusle/transformed/test.conllu", "streusle/transformed/train.conllu",
				"framenet/silver/framenet.corpus.conll" ,
				"amr/silver/amr-release-bio-v3.0.txt.conllu", "amr/silver/amr-bank-struct-v3.0.txt.conllu",
				"pmb/silver/pmb-4.0.0.en.gold.conll",
				"ibm-propbanks/silver/contracts_proposition_bank.conllu", "ibm-propbanks/silver/finance_proposition_bank.conllu" ]

}


def max_val(d): 
	# for a dict, max over values (recursively)
	# for a list, max over elements (recursively)
	# else trxy to cast to float and return numeral 
	if isinstance(d,dict):
		d=list(d.values())
	if isinstance(d,list):
		return max([ max_val(e) for e in d ])
	try:
		return float(d)
	except Exception:
		return 0.0


class Inventory:
	
	def __init__(self):
		self.corpus2pred2role2freq={}
		self.pred2corpus2freq={}
		
	def add_sentence(self, corpus, buffer:str):
		""" only evaluate DEPS column, assume these are all SRL annotations """

		id2row={}
		for line in buffer.split("\n"):
			line=line.strip()
			if(line!="" and not line.startswith("#")):
				row=line.split("\t")
				if(len(row)>8):
					id2row[row[0]]=row

		id2roles={}
		for row in id2row.values():
				deps=row[8].strip()
				if not deps in ["-","_",""]:
					for dep in deps.split("|"):
						dep=dep.split(":")
						id=dep[0]
						if id != row[0]:	# no self-referential rels
							role=dep[1]
							if not id in id2roles:
								id2roles[id]=[role]
							elif not role in id2roles:
								id2roles[id].append(role)
		
		for id in id2roles:
			if id in id2row:
				row=id2row[id]
				lemma=row[2]
				upos=row[3]
				pred=lemma+"/"+upos
				
				if not pred in self.pred2corpus2freq:
					self.pred2corpus2freq[pred] = { corpus : 1 }
				elif not corpus in self.pred2corpus2freq[pred]:
					self.pred2corpus2freq[pred][corpus]=1
				else:
					self.pred2corpus2freq[pred][corpus]+=1
					
				for role in set(id2roles[id]):
					if not corpus in self.corpus2pred2role2freq:
						self.corpus2pred2role2freq[corpus] = { pred : { role : 1 } }
					elif not pred in self.corpus2pred2role2freq[corpus]:
						self.corpus2pred2role2freq[corpus][pred] = { role : 1 }
					elif not role in self.corpus2pred2role2freq[corpus][pred]:
						self.corpus2pred2role2freq[corpus][pred][role] = 1
					else:
						self.corpus2pred2role2freq[corpus][pred][role]+=1

	def write_frames(self, pattern=None, corpora=[]):
		for pred in sorted(self.pred2corpus2freq.keys()):
			c=corpora
			if len(corpora)==0:
				c=sorted(self.pred2corpus2freq[pred])
			for corpus in c:
				if corpus in self.pred2corpus2freq[pred]:
					print(pred,corpus,self.pred2corpus2freq[pred][corpus])
	
	def compare_corpora(self, corpora=None, min_freq=0, tsv=False):
		if corpora==None or len(corpora)==0:
			corpora=sorted(self.corpus2pred2role2freq.keys())

		if len(corpora)>1:
	
			# core role mapping: identify majority mapping, mark whether this is identical
			c2p2m2role={}
			for c in corpora:
				if c in self.corpus2pred2role2freq:
					c2p2m2role[c]={}
					for pred in self.corpus2pred2role2freq[c]:
						p=pred
						c2p2m2role[c][p]={}
						m2r2f={}
						for role,f in self.corpus2pred2role2freq[c][pred].items():
							if re.match(r"^ARG[0-9]",role) and "-" in role:
								m=role.split("-")[0]
								r=role.split("-")[1]
								if not m in m2r2f:
									m2r2f[m]={r : f}
								elif not r in m2r2f:
									m2r2f[m][r]=f
								else:
									m2r2f[m][r]+=f
						for m in m2r2f:
							role=None
							for cand,f in m2r2f[m].items():
								if role==None or f>m2r2f[m][role]<f:
									role=cand
							c2p2m2role[c][p][m]=role


			while(len(corpora)>1):
				c1=corpora[0]
				if c1 in self.corpus2pred2role2freq:
					for c2 in corpora[1:]:
						if c2 in self.corpus2pred2role2freq:
							preds1=len(self.corpus2pred2role2freq[c1])
							preds2=len(self.corpus2pred2role2freq[c2])
							preds=[ p for p in self.corpus2pred2role2freq[c1] if p in self.corpus2pred2role2freq[c2]]
							same=0
							compatible=0
							total=0
							for p in preds:
								if max_val(self.corpus2pred2role2freq[c1][p]) > min_freq and max_val(self.corpus2pred2role2freq[c2][p]) >= min_freq:
									is_same=True
									is_compatible=True
									if len(c2p2m2role[c1][p])>0 and len(c2p2m2role[c2][p])>0:
										total+=1
										if len(c2p2m2role[c1][p])!=len(c2p2m2role[c2][p]):
											is_same=False
										for m in c2p2m2role[c1][p]:
											if m in c2p2m2role[c2][p] and c2p2m2role[c1][p][m]!=c2p2m2role[c2][p][m]:
												is_compatible=False
												is_same=False
												break
										if is_same:
											same+=1
										if is_compatible:
											compatible+=1
							results={ "c1": c1, "c2" : c2, 
									  "preds": len(preds), "pred overlap/c1": len(preds)/preds1, "pred overlap/c2": len(preds)/preds2, 
									  "same MR mapping": same/float(total), "compatible MR mapping": compatible/float(total), "min_freq": min_freq, "preds>min_freq": total }
							if tsv:
								print("\t".join([ str(r) for r in results.values() ]))
							else:
								print(json.dumps(results))
				corpora=corpora[1:]

args=argparse.ArgumentParser(description="statistics for individual subcorpora")
args.add_argument("corpora", type=str, nargs="*", help="corpora to be compared, chose from "+", ".join(sorted(corpus2files.keys())))
args.add_argument("-m", "--min_freq", type=int, help="minimum predicate frequency for agreement checks", default=0)
args.add_argument("-t", "--tsv_output", action="store_true", help="export as tsv rather than JSON-Line")
args=args.parse_args()

inventory=Inventory()

if len(args.corpora)==0:
	args.corpora=sorted(corpus2files.keys())

for corpus in args.corpora:
	if corpus in corpus2files: 
		for file in corpus2files[corpus]:
			with open(file,"r") as input:
				buffer=""
				for line in input:
					line=line.strip()
					if line=="":
						inventory.add_sentence(corpus,buffer)
						buffer=""
					else:
						buffer+=line+"\n"
				inventory.add_sentence(corpus,buffer)

# inventory.write_frames()
# for f in range(0,50):
# 	inventory.compare_corpora(min_freq=f)

inventory.compare_corpora(corpora=args.corpora,min_freq=args.min_freq, tsv=args.tsv_output)