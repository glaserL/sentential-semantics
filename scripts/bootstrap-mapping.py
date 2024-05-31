import re,sys,os,traceback,json,argparse
from pprint import pprint
from copy import deepcopy

# read conllu files from stdin with shallow SRL annotations in column 9 (DEPS)
# for every lemma, create a probabilistic mapping from role labels to macro roles
lemma2pb2mr2freq={}

class PFrameLex:
		
	disambiguated=False
		
	def __init__(self):
		self.pred2mr2role2freq={}
		
	def disambiguate(self):
		""" reduce mappings from one PB role to multiple macro roles *if one macro role encodes it unambiguously* """
		if not self.disambiguated:
			for pred in self.pred2mr2role2freq:
				mr2role2freq=deepcopy(self.pred2mr2role2freq[pred])
				role2mr2freq={}
				for mr in mr2role2freq:
					for role in mr2role2freq[mr]:
						if not role in role2mr2freq:
							role2mr2freq[role]={mr : mr2role2freq[mr][role] }
						else:
							role2mr2freq[role][mr] = mr2role2freq[mr][role]
				for role in list(role2mr2freq.keys()):
					if len(role2mr2freq)>1:
						cand_mr=None
						freq=0
						for mr in sorted(role2mr2freq[role]):
							if len(mr2role2freq[mr])==1:
								if cand_mr==None or role2mr2freq[role][mr]>freq:
									cand_mr=mr
									freq=role2mr2freq[role][mr]
						if cand_mr!=None:
							for mr in sorted(self.pred2mr2role2freq[pred].keys()):
								if role in self.pred2mr2role2freq[pred][mr] and mr!=cand_mr:
									self.pred2mr2role2freq[pred][mr].pop(role)
									if len(self.pred2mr2role2freq[pred][mr])==0:
										self.pred2mr2role2freq[pred].pop(mr)
									
		self.disambiguated=True
		
	def add(self, pred, mr, role, freq=1):
		if self.disambiguated:
			raise Exception("no additions after disambiguate()")
			
		if not pred in self.pred2mr2role2freq:
			self.pred2mr2role2freq[pred]={ mr : { role : freq }}
		elif not mr in self.pred2mr2role2freq[pred]:
			self.pred2mr2role2freq[pred][mr] = { role : freq }
		elif not role in self.pred2mr2role2freq[pred][mr]:
			self.pred2mr2role2freq[pred][mr][role] = freq
		else:
			self.pred2mr2role2freq[pred][mr][role] += freq
	
	def add_sentence(self, buffer):
		id2row={}
		pid2mr2role={}
		for row in buffer:
			id2row[row[0]]=row
			if not row[8] in ["","_","-","O","0"]:
				for dep in row[8].split("|"):
					dep=dep.split(":")
					pid=dep[0]
					roles=dep[1].split("-")
					role=roles[-1]
					if role.startswith("ARG"):
						role=None
					mr=dep[1].split("-")[0]
					if not mr.startswith("ARG"):
						mr=None
					if mr!=None and role!=None:
						if not pid in pid2mr2role:
							pid2mr2role[pid] = {mr : role}
						else:
							pid2mr2role[pid][mr]=role
		for pid in pid2mr2role:
			pred=id2row[pid][2]
			for mr in pid2mr2role[pid]:
				role = pid2mr2role[pid][mr]
				self.add(pred,mr,role)
				
	def revise(self, buffer):
		""" given a buffer, extract shallow SRL annotations and apply the most frequent mapping """
		id2row={}
		pid2orig2args={}		
		pid2role2args={}
		pid2mr2args={}
		for row in buffer:
			id2row[row[0]]=row
			if not row[8] in ["","_","-","O","0"]:
				for dep in row[8].split("|"):
					dep=dep.split(":")
					pid=dep[0]
					if not pid in pid2orig2args:
						pid2orig2args[pid] = { dep[1] : [row[0]] }
					elif not dep[1] in pid2orig2args[pid]:
						pid2orig2args[pid][dep[1]]=[row[0]]
					else:
						pid2orig2args[pid][dep[1]].append(row[0])
		
					roles=dep[1].split("-")
					role=roles[-1]
					if role.startswith("ARG"):
						if not pid in pid2mr2args:
							pid2mr2args[pid] = { role : [row[0]] }
						elif not role in pid2mr2args[pid]:
							pid2mr2args[pid][role]= [ row[0] ]
						else:
							pid2mr2args[pid][role].append(row[0])
					else:
						if not pid in pid2role2args:
							pid2role2args[pid] = { role : [row[0]]}
						elif not role in pid2role2args[pid]:
							pid2role2args[pid][role] = [row[0]]
						else:
							pid2role2args[pid][role].append(row[0])
		
		pid2role2args_orig=deepcopy(pid2role2args)
		
		for pid in pid2role2args:
			if not pid in pid2mr2args:
				pid2mr2args[pid]={}
			if pid in id2row:
				pred=id2row[pid][2]
				if pred in self.pred2mr2role2freq:
					for mr in self.pred2mr2role2freq[pred]:
						if not mr in pid2mr2args[pid]:
							freq=max(self.pred2mr2role2freq[pred][mr].values())
							cands=[ role for role in self.pred2mr2role2freq[pred][mr] if self.pred2mr2role2freq[pred][mr][role]==freq ]
							for c in cands:
								if c in pid2role2args[pid]:
									pid2mr2args[pid][mr]=pid2role2args[pid].pop(c)
									break
		
		pid2role2args=pid2role2args_orig
		arg2pid2role={}
		for pid in pid2orig2args:
			if not pid in pid2mr2args:	# macro role prediction failed => resort to raw extract (this is for low-frequency frames of ambiguous predicates)
				for orig in pid2orig2args[pid]:
					for arg in pid2orig2args[pid][orig]:
						if not arg in arg2pid2role:
							arg2pid2role[arg]={pid : orig }
						elif not pid in arg2pid2role:
							arg2pid2role[arg][pid] = orig
			else:
				for mr in sorted(pid2mr2args[pid].keys()):	# ARG0 > ARG1 > ARG2
					for arg in pid2mr2args[pid][mr]:
						if not arg in arg2pid2role:
							arg2pid2role[arg]={ pid : mr }
						elif not pid in arg2pid2role[arg]:
							arg2pid2role[arg][pid]=mr

				if pid in pid2role2args:
					for role in pid2role2args[pid]:
						for arg in pid2role2args[pid][role]:
							if not arg in arg2pid2role:
								arg2pid2role[arg] = { pid : role }
							elif not pid in arg2pid2role[arg]:
								arg2pid2role[arg][pid] = role
							else:
								arg2pid2role[arg][pid]=arg2pid2role[arg][pid]+"-"+role
						
		buffer=[]
		for id,row in id2row.items():
			if id in arg2pid2role:
				deps=[ pid+":"+role for pid, role in arg2pid2role[id].items() ]
				deps="|".join(deps)
				row[8]=deps
			buffer.append(row)
		
		return buffer

args=argparse.ArgumentParser(description="Bootstrap mapping from role labels to macro roles")
args.add_argument("files",action="append", nargs="+", type=str, help="raw conllu file with shallow SRL annotations in column 9 (DEPS), bootstrap probabilistic frame inventory and refine macro roles in data read from stdin")
args.add_argument("-d","--disambiguate",action="store_true", help="if this flag is set, perform an initial pruning step over the frame inventory, i.e., reduce mapping ambiguity")
args=args.parse_args()

i=0
while(i<len(args.files)):
	if type(args.files[i])==list:
		args.files=args.files[0:i]+args.files[i]+args.files[i+1:]
	else:
		i+=1
			
lex=PFrameLex()
for file in args.files:
	with open(file,"r") as input:
		buffer=[]
		for line in input:
			line=line.strip()
			fields=line.split("\t")
			if fields[0]=="1" or line=="":
				lex.add_sentence(buffer)
				buffer=[]
			if re.match(r"^[0-9]+$",fields[0]) and len(fields)>8:
				buffer.append(fields)
		if len(buffer)>0:
			lex.add_sentence(buffer)

if args.disambiguate:
	lex.disambiguate()
			
buffer=[]
for line in sys.stdin:
			line=line.strip()
			fields=line.split("\t")
			if fields[0]=="1" or line=="":
				buffer=lex.revise(buffer)
				print("\n".join(["\t".join(row) for row in buffer ]))
				buffer=[]
			if re.match(r"^[0-9]+$",fields[0]):
				buffer.append(fields)
			else:
				print(line)

if len(buffer)>0:
				buffer=lex.revise(buffer)
				print("\n".join(["\t".join(row) for row in buffer ]))
				
sys.stderr.write(json.dumps(lex.pred2mr2role2freq,indent=2)+"\n")
