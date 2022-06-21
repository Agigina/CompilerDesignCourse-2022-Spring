from Compiler.tools.dataStructure import *
from Compiler.tools.Item import *
import re
import sys


class loading():
	def __init__(self):
		self.left = []
		self.expressions = []
		self.items = []
		self.begin = None
		self.firstSet = {}
		self.words = {'if': 'IF', 'else': 'ELSE', 'while': 'WHILE',
					'int': 'INT', 'return': 'RETURN', 'void': 'VOID'}
		self.type = ['seperator', 'operator', 'identifier', 'int']

		self.regexs = ['\{|\}|\[|\]|\(|\)|,|;', '\+|-|\*|/|==|!=|>=|<=|>|<|=',
				 '[a-zA-Z][a-zA-Z0-9]*', '\d+']
		self.CURRENT_LINE = 0

		self.terminal = []
		self.start = None
		self.origin = None
		self.Nonterminal = []
		self.EndSymbol = None
		self.epsilon = None

		self.pInputStr = 0
		self.idname = []

		# for item in self.words:
		#	 self.idname.append(item)

		return

	def readGrammarFile(self, path):
		self.start = 'program_'
		self.origin = 'program'
		self.expressions.append(
			Item(self.start, [{'type': self.origin, 'class': 'NT', 'name': ''}]))
		self.Nonterminal.append(self.start)

		cntProd = 0
		liss = []
		with open(path, 'r') as fd:
			while True:
				line = fd.readline().replace('\n', '')
				if not line:
					break
				lis1 = []
				lis3 = []
				lis1.append({'type': line, 'class': 'NT', 'name': line})
				while True:
					lis2 = []
					line = fd.readline().replace('\n', '')
					if not line:
						break
					if line[0] == '\t':
						line = line.strip('\t').split(' ')
						if line[0] == '#':
							liss.append({'left': lis1, 'right': lis3})
							break
						cntProd = cntProd + 1
						for item in line:
							match = 0
							for regex in self.regexs[0:2]:
								result = re.match(regex, item)
								if result:
									match = 1
									break
							if match == 1:
								tempToken2 = {'type': item, 'class': 'T',
															'name': self.type[self.regexs.index(regex)].upper()}
							elif item in self.words:
								tempToken2 = {'type': item, 'class': 'T', 'name': item}
							elif item == 'id':
								tempToken2 = {'type': 'IDENTIFIER', 'class': 'T', 'name': 'IDENTIFIER'}
							elif item == '$':
								tempToken2 = {'type': item, 'class': 'T', 'name': item}
							elif item == 'num':
								tempToken2 = {'type': 'INT', 'class': 'T', 'name': 'INT'}
							else:
								tempToken2 = {'type': item, 'class': 'NT', 'name': item}

							lis2.append(tempToken2)
						lis3.append(lis2)
			fd.close()

		for t in liss:
			if t['left'][0]['type'] not in self.Nonterminal:
				self.Nonterminal.append(t['left'][0]['type'])
			for i in range(len(t['right'])):
				self.expressions.append(Item(t['left'][0]['type'], t['right'][i]))
				for j in range(len(t['right'][i])):
					if t['right'][i][j]['class'] == 'T' and \
						t['right'][i][j]['type'] not in self.terminal:
						self.terminal.append(t['right'][i][j]['type'])

		self.EndSymbol = '#'
		self.terminal.append(self.EndSymbol)
		self.epsilon = '$'
		return

	def set_First(self):
		for item in self.terminal:
			self.firstSet[item] = [item]
		for item in self.Nonterminal:
			self.firstSet[item] = []
		for item in self.Nonterminal:
			self.calNTFirstSetImprove(item)
		return

	def set_NTFirst(self, symbol):
		eps = {'class': 'T', 'name': '', 'type': self.epsilon}
		num = -1
		res = []
		rstStr = []
		prods = [item for item in self.expressions if item.left == symbol]
		if len(prods) == 0:
			return res

		flag = 1
		while flag:
			flag = 0
			for item in prods:
				num = 0
				for subitem in item.right:
					if num >= 0:
						num = num + 1
					if subitem['class'] == 'T' or\
						(subitem['type'] == self.epsilon and len(item.right) == 1):
						if subitem['type'] not in rstStr:
							res.append(subitem)
							rstStr.append(subitem['type'])
						num = -2
						break
					tempRstSet = []
					if subitem['type'] in self.firstSet.keys():
						tempRstSet = self.firstSet[subitem['type']]
					else:
						if subitem['type'] == symbol:
							break
						tempRstSet = self.set_NTFirst(subitem['type'])
					if eps in tempRstSet:
						if num == 1:
							num = -1
						tempRstSet = [
							right for right in tempRstSet if right['type'] != eps['type']]
						for tempRst in tempRstSet:
							if tempRst['type'] not in rstStr:
								res.append(tempRst)
								rstStr.append(tempRst['type'])
								flag = 1
					else:
						num = -2
						for tempRst in tempRstSet:
							if tempRst['type'] not in rstStr:
								res.append(tempRst)
								rstStr.append(tempRst['type'])
								flag = 1
						break

				if num == -1:
					flag = 1
					rstStr.append(self.epsilon)
					res.append(eps)
		return res

	def calNTFirstSetImprove(self, symbol):
		num = -1
		prods = [item for item in self.expressions if item.left == symbol]
		if len(prods) == 0:
			return
		flag = 1
		while flag:
			flag = 0
			for item in prods:
				num = 0
				for subitem in item.right:
					if subitem['class'] == 'T' or\
						(subitem['type'] == self.epsilon and len(item.right) == 1):
						if subitem['type'] not in self.firstSet[symbol]:
							self.firstSet[symbol].append(subitem['type'])
							flag = 1
						break
					if len(self.firstSet[subitem['type']]) == 0:
						if subitem['type'] != symbol:
							self.calNTFirstSetImprove(subitem['type'])
					if self.epsilon in self.firstSet[subitem['type']]:
						if num == 1:
							num = 1
						elif num == 0:
							num = 1
					for f in self.firstSet[subitem['type']]:
						if f != self.epsilon and f not in self.firstSet[symbol]:
							self.firstSet[symbol].append(f)
							flag = 1
				if num == 1:
					if self.epsilon not in self.firstSet[symbol]:
						self.firstSet[symbol].append(self.epsilon)
						flag = 1
		return

	def get_dot(self):
		for item in self.expressions:
			if len(item.right) == 1 and item.right[0]['type'] == self.epsilon:
				self.items.append(Item(item.left, item.right, 0, ['#']))
				continue
			for i in range(len(item.right) + 1):
				self.items.append(Item(item.left, item.right, i, ['#']))

	def annotation(self, str):
		annotations = re.findall('//.*?\n', str, flags=re.DOTALL)
		if(len(annotations) > 0):
			str = str.replace(annotations[0], "")
		annotations = re.findall('/\*.*?\*/', str, flags=re.DOTALL)
		if(len(annotations) > 0):
			str = str.replace(annotations[0], "")
		return str.strip()

	def get_str(self, line):
		max = ''
		target_regex = self.regexs[0]
		flag = False
		for item in self.regexs:
			res = re.match(item, line)
			if res:
				res = res.group(0)
				if len(res) > len(max):
					flag = True
					max = res
					target_regex = item
		if not flag:
			return {"data": line[0], "regex": None, "remain": line[1:]}
		else:
			return {"data": max, "regex": target_regex, "remain": line[len(max):]}

	def get_line(self, conten):
		lis = []
		res = conten.strip().strip('\t')
		origin = res
		while True:
			if res == "":
				break
			before = res
			res = self.get_str(res)
			if res['regex']:
				dict = {}
				dict['class'] = "T"
				dict['row'] = self.CURRENT_LINE
				dict['colum'] = origin.find(before)+1
				dict['name'] = self.type[self.regexs.index(res['regex'])].upper()
				dict['data'] = res['data']
				dict['type'] = dict['name']

				if res['data'] in self.words:
					dict['name'] = self.words[res['data']].lower()
					dict['type'] = dict['name']
					dict['idnum'] = '-'
				elif dict['name'] == "operator".upper() or dict['name'] == "seperator".upper():
					dict['type'] = dict['data']
					dict['idnum'] = '-'
				elif dict['name'] == "INT":
					dict['data'] = dict['data']
					dict['idnum'] = '-'
				elif res['data'] not in self.idname:
					self.idname.append(res['data'])
					dict['idnum'] = self.idname.index(res['data'])+6
				elif res['data'] in self.idname:
					dict['idnum'] = self.idname.index(res['data'])+6
				else:
					dict['idnum'] = '-'

				lis.append(dict)
			res = res['remain'].strip().strip('\t')
			if (res == ""):
				return lis
		return lis

	def input_token(self, inputStr):
		lines = self.annotation(inputStr).split('\n')
		lis = []
		for line in lines:
			temp = self.get_line(line)
			lis += temp
			self.CURRENT_LINE += 1
		return lis

	def get_line_token(self, inputStr):
		if self.pInputStr >= len(inputStr):
			return []
		while True:
			idx = inputStr.find('\n', self.pInputStr)
			if idx == -1:
				idx = len(inputStr)-1
			line = inputStr[self.pInputStr:idx+1].strip()
			self.pInputStr = idx + 1
			if line == '':
				continue
			else:
				break

		res = self.get_line(line)
		sys.stdout.flush()
		return res
