from Compiler.tools.dataStructure import *


class ItemSetFamily():
	def __init__(self, cfg):
		self.terminal = cfg.terminal
		self.start = cfg.start
		self.Nonterminal = cfg.Nonterminal
		self.EndSymbol = cfg.EndSymbol
		self.epsilon = cfg.epsilon

		self.symbols = self.terminal + self.Nonterminal
		self.itemPool = cfg.items
		self.itemSets = []
		self.edges = []
		self.firstSet = cfg.firstSet
		return

	def getLeftNT(self, NT):
		res = []
		for item in self.itemPool:
			if item.left == NT and item.dotPos == 0:
				res.append(item)
		return res

	def getLR1Closure(self, I):
		res = []
		res.extend(I)

		rstStr = [item.toString() for item in res]
		while True:
			flag = 0
			for item in res:
				right = item.right
				for i in range(len(right)+1):
					if item.dotPos == len(right):
						continue
					if right[item.dotPos]['class'] == 'T':
						continue
					tempRst = self.extendItem(item)
					for i in tempRst:
						tempStr = i.toString()
						if tempStr not in rstStr:
							rstStr.append(tempStr)
							res.append(i)
							flag = 1
			if flag == 0:
				break
		return res

	def GO(self, I, X):
		J = []
		if len(I.items) == 0 or X == self.epsilon:
			return J
		for item in I.items:
			if item.dotPos == len(item.right):
				continue
			if len(item.right) == 1 and item.right[0] == self.epsilon:
				continue
			if item.right[item.dotPos]['type'] == X:
				temp = item.nextItem()
				if temp != None:
					J.append(temp)
		return self.getLR1Closure(J)

	def edge2str(self, edge):
		return edge['start']+'->'+edge['symbol']+'->'+edge['end']

	def getFirstSet(self, symbols):
		res = []
		flag = 0
		for item in symbols:
			tempSet = [i for i in self.firstSet[item]]
			if self.epsilon in tempSet:
				if flag == 0:
					flag = 1
				res.extend([i for i in tempSet if i != self.epsilon])
			else:
				flag = -1
				res.extend(tempSet)
				break
		if flag == 1:
			res.append(self.epsilon)
		return res

	def extendItem(self, item):
		res = []
		if item.right[item.dotPos]['class'] != 'NT':
			return res
		str2BgetFirstSet = []
		for rightIdx in range(item.dotPos+1, len(item.right)):
			str2BgetFirstSet.append(item.right[rightIdx]['type'])
		nextItem = self.getLeftNT(item.right[item.dotPos]['type'])
		str2BgetFirstSet.append(item.terms[0])
		tempFirsts = self.getFirstSet(str2BgetFirstSet)
		for i in nextItem:
			for j in tempFirsts:
				res.append(Item(i.left, i.right, 0, [j]))
		return res

	def buildFamily(self):
		iS = self.itemSets
		startI = []
		startI.append(self.itemPool[0])
		iS.append(ItemSet('s0', self.getLR1Closure(
			[startI[0]] + self.extendItem(startI[0]))))

		setCnt = 1
		setStrings = {}
		setStrings['s0'] = iS[0].toString()
		edgeStrings = []

		while True:
			flag = 0
			for item in iS:
				for subitem in self.symbols:
					rstGO = self.GO(item, subitem)
					if len(rstGO) == 0:
						continue
					tempItemSet = ItemSet('s'+str(setCnt), rstGO)

					if tempItemSet.toString() in setStrings.values():
						tempItemSet.name = list(setStrings.keys())[list(
							setStrings.values()).index(tempItemSet.toString())]
					else:
						setStrings[tempItemSet.name] = tempItemSet.toString()
						iS.append(tempItemSet)
						flag = 1
						setCnt = setCnt + 1

					tempEdge = {'start': item.name,
								'symbol': subitem, 'end': tempItemSet.name}
					tempEdgeStr = self.edge2str(tempEdge)

					if tempEdgeStr not in edgeStrings:
						self.edges.append(tempEdge)
						edgeStrings.append(tempEdgeStr)
						flag = 1
			if flag == 0:
				break
		return


class ItemSet():
	def __init__(self, name, items):
		self.name = name
		self.items = items

		self.string = []
		for item in self.items:
			itemStr = item.toString()
			if itemStr not in self.string:
				self.string.append(itemStr)
		self.string = sorted(self.string)
		return

	def toString(self):
		return "\n".join(self.string)


class Item():
	def __init__(self, left, right, dotPos=0, terms=['#']):
		self.right = right
		self.left = left
		self.dotPos = dotPos
		self.terms = terms
		return

	def nextItem(self):
		return Item(self.left, self.right, self.dotPos + 1, self.terms) \
			if self.dotPos < len(self.right) + 1 else None

	def toString(self):
		res = self.left + '->'
		pos = 0
		for right in self.right:
			if pos == self.dotPos:
				res += '@'
			res += right['type'] + ' '
			pos += 1
		if pos == self.dotPos:
			res += '@'
		for term in self.terms:
			res += term + ' '
		return res
