import copy
import sys

from Compiler.tools.dataStructure import *
from Compiler.tools.Item import *
from Compiler.tools.loading import *

class SyntacticAnalyzer():
    def __init__(self, loading, family):
        self.loading = loading
        self.family = family
        self.EndSymbol = loading.EndSymbol
        self.origin = loading.origin
        self.start = loading.start
        self.terminal = loading.terminal
        self.Nonterminal = loading.Nonterminal

        self.itemSets = family.itemSets
        self.edges = family.edges
        self.numSet = len(self.itemSets)

        action_name = self.terminal
        action_name.append(self.EndSymbol)

        self.ACTION={y.name: {x:' ' for x in action_name} for y in self.itemSets}
        self.GOTO={y.name: {x:' ' for x in self.Nonterminal} for y in self.itemSets}

        self.expressions = loading.expressions
        self.prodStrs = [i.toString() for i in self.expressions]

        self.M_name = self.terminal + self.Nonterminal
        self.M={y.name: {x:' ' for x in self.M_name} for y in self.itemSets}

        self.sStack = []
        self.symbolTable = []
        self.curFunc = 0
        self.curTempId = 0
        self.curOffset = 0
        self.curFuncSymbol = None
        self.funcTable = []
        self.curLabel = 0

        f = FunctionSymbol()
        f.name = 'global' 
        f.label = 'global'
        self.updateFuncTable(f)
        self.curFuncSymbol = f

        self.middleCode = []
        self.mipsCode = []

        self.syntacticRst = True
        self.syntacticErrMsg = "语法Done"
        self.grammarRst = True
        self.grammarErrMsg = "语义Done"
        return

    def item2prod(self, item):
        tempStr = item.left + '->@'
        for right in item.right:
            tempStr += (right['type'] + ' ' )
        tempStr += '# '
        return self.prodStrs.index(tempStr)
    
    def getParseRst(self):
        return self.parseRst

    def getTables(self):
        self.rst = []
        for item in self.edges:
            if item['symbol'] in self.terminal:
                self.M[item['start']][item['symbol']] = 'shift '+ item['end']
            if item['symbol'] in self.Nonterminal:
                self.M[item['start']][item['symbol']] = 'goto '+ item['end']

        for I in self.itemSets:
            for item in I.items:
                if item.dotPos == len(item.right):
                    if item.left == self.origin and item.terms[0] == '#':
                        if self.M[I.name][item.terms[0]] != ' ':
                            print('rewrite error!!!')
                        self.M[I.name][item.terms[0]] = 'acc'
                    else:
                        if self.M[I.name][item.terms[0]] != ' ':
                            print('rewrite error!!!')
                        self.M[I.name][item.terms[0]] = 'reduce ' + str(self.item2prod(item))
                    continue

                if len(item.right) == 1 and item.right[0]['type'] == '$':
                    if item.left == self.origin and item.terms[0] == '#':
                        if self.M[I.name][item.terms[0]] != ' ':
                            print('rewrite error!!!')
                        self.M[I.name][item.terms[0]] = 'acc'
                    else:
                        if self.M[I.name][item.terms[0]] != ' ':
                            print('rewrite error!!!')
                        self.M[I.name][item.terms[0]] = 'reduce ' + str(self.item2prod(item))
                    continue
        return

    def isRecognizable(self, origin):
        inputStr = []
        inputStr += self.loading.get_line_token(origin)
        sys.stdout.flush()
        stateStack = []
        shiftStr = []

        self.parseRst = []

        wallSymbol = {'class':'T', 'type':'#'}
        shiftStr.append(wallSymbol)
        stateStack.append('s0')
        X = inputStr[0]
        while True:
            if len(inputStr) <= 2:
                tmpInputStr = self.loading.get_line_token(origin)
                if not tmpInputStr:
                    inputStr.append(wallSymbol)
                else:
                    inputStr += tmpInputStr

            self.parseRst.append({'stateStack':copy.deepcopy(stateStack), 'shiftStr':copy.deepcopy(shiftStr), 'inputStr': copy.deepcopy(inputStr)})

            mv = self.M[stateStack[-1]][X['type']].split(' ')[0]
            target = self.M[stateStack[-1]][X['type']].split(' ')[1] \
                if len(self.M[stateStack[-1]][X['type']].split(' '))==2 else None

            if mv =='shift':
                stateStack.append(target)
                inputStr.pop(0)
                shiftStr.append(X)
                X = inputStr[0]
            elif mv == 'goto':
                stateStack.append(target)
                shiftStr.append(X)
                X = inputStr[0]
            elif mv == 'reduce':
                prodIdx = int(target)
                prod = self.expressions[prodIdx]

                self.grammarAnalyze(prod, shiftStr)
                if not self.grammarRst:
                    return False

                rightLen = len(prod.right)
                stateLen = len(stateStack)

                if rightLen == 1 and prod.right[0]['type'] == '$':
                    dst = self.M[stateStack[-1]][prod.left].split(' ')[1]
                    stateStack.append(dst)
                    shiftStr.append({'class':'NT', 'type': prod.left})
                    X = inputStr[0]
                else:
                    stateStack = stateStack[0:stateLen - rightLen]
                    shiftStr = shiftStr[0:stateLen - rightLen]
                    X = {'class':'NT', 'type': prod.left}

            elif mv == 'acc':
                self.grammarAnalyze(self.expressions[1], shiftStr)
                return True
            else:
                print('error')
                self.syntacticRst = False
                sys.stdout.flush()
                self.syntacticErrMsg = "语法分析错误：" + str(X['row']) + "行" + str(X['colum']) + "列"
                return False

    def grammarAnalyze(self, prod, shiftStr):
        nt = prod.left
        r = prod.right

        sys.stdout.flush()

        if nt == 'program':
            n = self.sStack.pop(-1)
            n.name = nt
            for node in n.stack:
                for code in node.code:
                    n.code.append(code)
            self.middleCode = copy.deepcopy(n.code)
            self.sStack.append(n)
        elif nt in ['statement','block']:
            n = self.sStack.pop(-1)
            n.name = nt
            self.sStack.append(n)
        elif nt == 'declarationChain':
            n = Node()
            if len(r) == 2:
                n = self.sStack.pop(-1)
                n.stack.insert(0, self.sStack.pop(-1))               
            n.name = nt
            self.sStack.append(n)

        elif nt == 'typeSpecifier':
            n = Node()
            n.name = nt
            n.type = shiftStr[-1]['type']
            self.sStack.append(n)
        elif nt == 'declaration':
            n = self.sStack.pop(-1)
            n.name = nt
            if len(r) == 3:
                defType = n.type
                defName = shiftStr[-2]['data']
                s = self.find(defName, self.curFuncSymbol.label)
                if s != None:
                    print("multi defination?")
                    self.grammarRst = False
                    self.grammarErrMsg = "变量重定义：" + str(shiftStr[-2]['row']) + "行" + str(shiftStr[-2]['colum']) +  "列"
                    return
                else:
                    s = Symbol()
                if n.place == None:
                    s.name = defName
                    s.place = self.getNewTemp()
                    s.type = defType
                    s.function = self.curFuncSymbol.label
                    s.size = 4
                    s.offset = self.curOffset
                    self.curOffset += s.size
                    self.updateSymbolTable(s)
                    if n.data != None:
                        code=(':=',n.data,'_',s.place)
                        n.code.append(code)
                else:
                    s.name = defName
                    s.place = n.place
                    s.type = defType
                    s.function = self.curFunc
                    s.size = 4
                    s.offset = self.curOffset
                    self.curOffset += s.size
                    self.updateSymbolTable(s)
                    for code in n.code:
                        n.code.stack.insert(0, code)
            self.sStack.append(n)
        elif nt == 'completeFunction':
            n = self.sStack.pop(-1)
            nDefine = self.sStack.pop(-1)
            n.name = nt
            codeTmp = []
            codeTmp.append((nDefine.data,':','_','_'))                       
            for node in nDefine.stack:
                codeTmp.append(('pop','_', 4 * nDefine.stack.index(node), node.place))
            if len(nDefine.stack) > 0:
                codeTmp.append(('-', 'fp', 4 * len(nDefine.stack), 'fp'))
            for code in reversed(codeTmp):
                n.code.insert(0, code)
            code_end = n.code[-1]
            if code_end[0][0] == 'l':
                label = code_end[0]
                n.code.remove(code_end)
                for code in n.code:
                    if code[3] == label:
                        n.code.remove(code)  
            self.sStack.append(n)
        elif nt == 'declareFunction':
            n = self.sStack.pop(-1)
            n.name = nt
            nFuncReturnType = self.sStack.pop(-1)
            f = FunctionSymbol()
            f.name = shiftStr[-4]['data']
            f.type = nFuncReturnType.type
            if f.name == 'main':
                f.label = 'main'
            else:
                f.label = self.getNewFuncLabel()
            
            for item in n.stack:
                s = Symbol()
                s.name = item.data
                s.place = item.place
                s.type = item.type
                s.function = f.label
                s.size = 4
                s.offset = self.curOffset
                self.curOffset += s.size
                self.updateSymbolTable(s)
                f.params.append((item.data, item.type, item.place))
            n.data = f.label
            self.updateFuncTable(f)
            self.stack = []
            self.curFuncSymbol = f
            self.sStack.append(n)

        elif nt == 'formalParaList':
            n = Node() 
            if len(r) == 3:
                n = self.sStack.pop(-1)
                n.name = nt
                n.stack.insert(0, self.sStack.pop(-1))
            elif len(r) == 1 and (r[0]['type'] in ['$', 'void']):
                n.name = nt
            elif len(r) == 1 and r[0]['type'] == 'para':
                n.stack.insert(0, self.sStack.pop(-1))
                n.name = nt
            self.sStack.append(n)

        elif nt == 'para':
            n = self.sStack.pop(-1)
            n.name = nt
            n.place = self.getNewTemp()
            n.data = shiftStr[-1]['data']
            self.sStack.append(n)

        elif nt == 'statementChain':
            if len(r) == 1:
                n = Node()
                n.name = nt
                self.sStack.append(n)
            elif len(r) == 2:
                n = self.sStack.pop(-1)
                n.stack.insert(0, self.sStack.pop(-1))
                n.name = nt
                for code in reversed(n.stack[0].code):
                    n.code.insert(0, code)
                self.sStack.append(n)
            
        elif nt == 'assignStatement':
            id = shiftStr[-4]['data']
            n = copy.deepcopy(self.sStack.pop(-1))
            n.name = nt
            self.calExpression(n)
            s = self.find(id, self.curFuncSymbol.label)
            if not s:
                print("Assign before defination")
                self.grammarRst = False
                self.grammarErrMsg = "使用未定义变量：" + str(shiftStr[-4]['row']) + "行" + str(shiftStr[-4]['colum']) +  "列"
                return

            if s.type != n.type:
                token = shiftStr[-4]
                self.grammarRst = False
                self.grammarErrMsg = "赋值时变量类型错误：" + token['data'] + \
                    '，在' + str(token['row']) + "行" + \
                        str(token['colum']) +  "列"
                return

            sys.stdout.flush()
            code = None
            if n.place != None:
                code = (':=', n.place, '_', s.place)
            else:
                code = (':=', n.data, '_', s.place)
            n.code.append(code)
            sys.stdout.flush()
            self.sStack.append(n)

        elif nt == 'returnStatement':
            n = None
            if len(r) == 3:
                n = self.sStack.pop(-1)
                self.calExpression(n)
                n.type = r[0]['type']
                nRst = None
                if n.place != None:
                    nRst = n.place
                else:
                    nRst = n.data
                n.code.append((':=', nRst, '_', 'v0'))
            elif len(r) == 2:
                n = Node()
                n.type = r[0]['type']

            n.code.append((n.type, '_', '_', '_'))
            n.name = nt
            self.sStack.append(n)

        elif nt == 'expression':
            n = None
            if len(r) == 1:
                n = copy.deepcopy(self.sStack[-1])
                sys.stdout.flush()
                n.stack.insert(0 ,self.sStack.pop(-1))
                
            elif len(r) == 3:
                n = copy.deepcopy(self.sStack.pop(-1))
                n.stack.insert(0, self.sStack.pop(-1))
                n.stack.insert(0, self.sStack.pop(-1)) 

            n.name = nt
            self.sStack.append(n)
            sys.stdout.flush()
            
        elif nt == 'primaryExpression':
            n = Node()
            if len(r) == 1 and r[0]['type'] == 'INT':
                n.data = shiftStr[-1]['data']
                n.type = shiftStr[-1]['type'].lower()

            elif len(r) == 4 and r[0]['type'] == 'IDENTIFIER':
                function = self.findFuncSymbolByName(shiftStr[-4]['data'])
                n = self.sStack.pop(-1)
                n.name = nt
                if not function:
                    print('function not defined!')
                    self.grammarRst = False
                    self.grammarErrMsg = "未定义的函数：" + \
                            shiftStr[-4]['data'] + "，在" + \
                            str(shiftStr[-4]['row']) + "行" + str(shiftStr[-4]['colum']) + "列"
                    return
                
                if len(function.params) != len(n.stack):
                    print('function params do not fit!')
                    sys.stdout.flush()
                    self.grammarRst = False
                    self.grammarErrMsg = "实参和形参个数不匹配：" + \
                            shiftStr[-4]['data'] + "，在" + \
                            str(shiftStr[-4]['row']) + "行" + str(shiftStr[-4]['colum']) + "列"
                    return
                code_temp=[]
                symbol_temp_list = copy.deepcopy(self.curFuncSymbol.params)
                code_temp.append(('-', 'sp', 4 * len(symbol_temp_list) + 4, 'sp'))
                code_temp.append(('store', '_', 4 * len(symbol_temp_list), 'ra'))
                for symbol in symbol_temp_list:
                    code_temp.append(('store','_',4 * symbol_temp_list.index(symbol),symbol[2]))
                for code in reversed(code_temp):
                    n.code.insert(0, code)

                if function.params:
                    n.code.append(('+', 'fp', 4*len(function.params), 'fp'))

                for node in n.stack:
                    if node.place != None:
                        node_result = node.place
                    else:
                        node_result = node.data
                    n.code.append(('push','_',4 * n.stack.index(node),node_result))
                n.code.append(('call', '_', '_', function.label))

                symbol_temp_list.reverse()
                for symbol in symbol_temp_list:
                    n.code.append(('load', '_', 4 * symbol_temp_list.index(symbol), symbol[2]))
                n.code.append(('load', '_', 4 * len(symbol_temp_list), 'ra'))
                n.code.append(('+', 'sp', 4 * len(self.curFuncSymbol.params) + 4, 'sp'))

                n.place = self.getNewTemp()
                n.code.append((':=', 'v0', '_', n.place))
                n.stack = [] 
            elif len(r) == 1 and r[0]['type'] == 'IDENTIFIER':
                n.data = shiftStr[-1]['data']
                nTmp = self.find(n.data, self.curFuncSymbol.label)
                n.type = nTmp.type
                n.place = nTmp.place
                if not n:
                    print('undifined variable used!')
                    self.grammarRst = False
                    self.grammarErrMsg = "未定义的变量：" + \
                            shiftStr[-1]['data'] + "，在" + \
                            str(shiftStr[-1]['row']) + "行" + str(shiftStr[-1]['colum']) + "列"
                    return

            elif len(r) == 3 and r[1]['type'] == 'expression':
                n = self.sStack.pop(-1)
                self.calExpression(n)

            n.name = nt
            self.sStack.append(n)
            sys.stdout.flush()
            
        elif nt == 'operator':
            n = Node()
            n.name = 'operator'
            n.type = ''
            for i in range(len(r)):
                token = shiftStr[-(len(r) - i)]
                n.type += token['type']
            self.sStack.append(n)

        elif nt == 'actualParaList':
            n = None
            if len(r) == 3:
                n = self.sStack.pop(-1)
                nExp = self.sStack.pop(-1)
                self.calExpression(nExp)
                n.stack.insert(0, nExp)

            elif len(r) == 1 and (r[0]['type'] in ['$']):
                n = Node()
            elif len(r) == 1 and r[0]['type'] == 'expression':
                n = copy.deepcopy(self.sStack.pop(-1))
                self.calExpression(n)
            n.name = nt
            self.sStack.append(n)
            sys.stdout.flush()
            
        elif nt == 'ifStatement':
            n = Node()
            n.name = nt
            if len(r) == 5:
                n.true = self.getNewLabel()
                n.end = self.getNewLabel()
                nT = self.sStack.pop(-1)
                nExp = self.sStack.pop(-1)
                self.calExpression(nExp)
                n.code.extend(nExp.code)
                n.code.append(('j>', nExp.place, '0', n.true))
                n.code.append(('j', '_', '_', n.end))
                n.code.append((n.true, ':', '_', '_'))
                for code in nT.code:
                    n.code.append(code)
                n.code.append((n.end,':','_','_'))

            elif len(r) == 7: 
                n.true = self.getNewLabel()
                n.false = self.getNewLabel()
                n.end = self.getNewLabel()
                nF = self.sStack.pop(-1)
                nT = self.sStack.pop(-1)
                nExp = self.sStack.pop(-1)
                self.calExpression(nExp)

                n.code.extend(nExp.code)
                n.code.append(('j>', nExp.place, '0', n.true))
                n.code.append(('j', '_', '_', n.false))
                n.code.append((n.true, ':', '_', '_'))
                for code in nT.code:
                    n.code.append(code)
                n.code.append(('j', '_', '_', n.end))
                n.code.append((n.false, ':', '_', '_'))
                for code in nF.code:
                    n.code.append(code)
                n.code.append((n.end,':','_','_'))
            
            self.sStack.append(n)

        elif nt == 'iterStatement':
            n = Node()
            n.name = nt
            n.true = self.getNewLabel()
            n.false = self.getNewLabel()
            n.begin = self.getNewLabel()
            n.end = self.getNewLabel()

            if r[0]['type'] == 'while':
                statement = self.sStack.pop(-1)
                expression = self.sStack.pop(-1)
                self.calExpression(expression)
                n.code.append((n.begin, ':', '_', '_'))
                for code in expression.code:
                    n.code.append(code)
                n.code.append(('j>', expression.place, '0', n.true))
                n.code.append(('j', '_', '_', n.false))
                n.code.append((n.true,':','_','_'))
                for code in statement.code:
                    if code[0] == 'break':
                        n.code.append(('j','_','_', n.false))
                    elif code[0] == 'continue':
                        n.code.append(('j','_','_', n.begin))
                    else:
                        n.code.append(code)
                n.code.append(('j', '_', '_', n.begin))
                n.code.append((n.false,':','_','_'))

            self.sStack.append(n)

        sys.stdout.flush()
        return
  
    def find(self, name, function):
        for s in self.symbolTable:
            if s.name == name and s.function == function:
                return s
        return None

    def updateSymbolTable(self, symbol):
        for item in self.symbolTable:
            if item.name == symbol.name and item.function == symbol.function:
                self.symbolTable.remove(item)
                break
        self.symbolTable.append(symbol)
        return

    def getNewTemp(self):
        self.curTempId += 1
        return "t" + str(self.curTempId)

    def getNewFuncLabel(self):
        self.curFunc+=1
        return 'f' + str(self.curFunc)

    def updateFuncTable(self, functionSymbol):
        for item in self.funcTable:
            if item.name == functionSymbol.name:
                self.funcTable.remove(item)
                break
        self.funcTable.append(functionSymbol)
        return

    def calExpression(self, n):        
        if len(n.stack) == 1:
            n = copy.deepcopy(n.stack[0])
            n.stack = []
            return True
        n.code = [] 
        sys.stdout.flush()
        nLeft = n.stack.pop(0)
        while len(n.stack) > 0:
            nOp = n.stack.pop(0)
            nRight = n.stack.pop(0)
            if nLeft.place == None:
                arg1 = nLeft.data
            else:
                arg1 = nLeft.place
            if nRight.place == None:
                arg2 = nRight.data
            else:
                arg2 = nRight.place
            if len(nLeft.code) > 0:
                for code in nLeft.code:
                    n.code.append(code)
            if len(nRight.code) > 0:
                for code in nRight.code:
                    n.code.append(code)
            nRst = Node()
            nRst.name = None
            nRst.place = self.getNewTemp()
            nRst.type = nRight.type
            code = (nOp.type, arg1, arg2, nRst.place)
            n.code.append(code)
            nLeft = nRst
            n.type = nRight.type
        n.place = n.code[-1][3]
        return True

    def findFuncSymbolByName(self, name):
        for f in self.funcTable:
            if f.name == name:
                return f
        return None
        
    def getNewLabel(self):
        self.curLabel += 1
        return 'l' + str(self.curLabel)

    def saveMidCodeToFile(self):
        text = ''
        for code in self.middleCode:
            text += '{}, {}, {}, {}\n'.format(code[0], code[1], code[2], code[3])
        middleCodeObj = open("middleCodeFile.txt", 'w+')
        middleCodeObj.write(text)
        middleCodeObj.close()
        return True

class ObjectCodeGenerator():
    def __init__(self, middleCode, symbolTable):
        self.middleCode = copy.deepcopy(middleCode)
        self.mipsCode = []
        self.regTable = {'$' + str(i):'' for i in range(7, 26)}
        self.varStatus = {}
        self.DATA_SEGMENT = 10010000
        self.STACK_OFFSET = 8000
        self.symbolTable = copy.deepcopy(symbolTable)
        return

    def getRegister(self, identifier, codes):
        if identifier[0] != 't':
            return identifier
        if identifier in self.varStatus and \
            self.varStatus[identifier] == 'reg':
            for key in self.regTable:
                if self.regTable[key] == identifier:
                    return key

        while True:
            for key in self.regTable:
                if self.regTable[key] == '':
                    self.regTable[key] = identifier
                    self.varStatus[identifier] = 'reg'
                    return key
            self.freeRegister(codes)

    def freeRegister(self, codes):
        varRegUsed = list(filter(lambda x:x != '', self.regTable.values()))
        varUsageCnts = {}
        for code in codes:
            for item in code:
                tmp = str(item)
                if tmp[0] == 't':
                    if tmp in varRegUsed:
                        if tmp in varUsageCnts:
                            varUsageCnts[tmp] += 1
                        else:
                            varUsageCnts[tmp] = 1
                
        sys.stdout.flush()
        flag = False

        for var in varRegUsed:
            if var not in varUsageCnts:
                for reg in self.regTable:
                    if self.regTable[reg] == var:
                        self.regTable[reg] = ''
                        self.varStatus[var] = 'memory'
                        flag = True
        if flag:
            return

        sorted(varUsageCnts.items(), key=lambda x:x[1])
        varFreed = list(varUsageCnts.keys())[0]
        for reg in self.regTable:
            if self.regTable[reg] == varFreed:
                for item in self.symbolTable:
                    if item.place == varFreed:
                        self.mipsCode.append('addi $at, $zero, 0x{}'.format(self.DATA_SEGMENT))
                        self.mipsCode.append('sw {}, {}($at)'.format(reg, item.offset))
                        self.regTable[reg] = ''
                        self.varStatus[varFreed] = 'memory'
                        return
        return

    def genMips(self):
        mc = self.mipsCode
        dc = self.middleCode
        dc.insert(0, ('call', '_', '_', 'programEnd'))
        dc.insert(0, ('call', '_', '_', 'main'))
        mc.append('addiu $sp, $zero, 0x{}'.format(self.DATA_SEGMENT + self.STACK_OFFSET))
        mc.append('or $fp, $sp, $zero')

        while dc:
            code = dc.pop(0)
            tmp = []
            for item in code:
                if item=='v0':
                    tmp.append('$v0')
                else:
                    tmp.append(item)
            code = tmp
            
            if code[0] == ':=':
                src = self.getRegister(code[1], dc)
                dst = self.getRegister(code[3], dc)
                mc.append('add {},$zero,{}'.format(dst, src))

            elif code[1] == ':':
                if code[0][0] in ['f','main']:
                    mc.append('')
                mc.append('{}:'.format(code[0]))

            elif code[0] == 'call':
                mc.append('jal  {}'.format(code[3]))

            elif code[0] == 'push':
                if code[3] == 'ra':
                    mc.append('sw $ra, {}($fp)'.format(code[2]))
                else:
                    register = self.getRegister(code[3], dc)
                    if str(register)[0] != '$':
                        mc.append("add $a0, $zero, {}".format(register))
                        register = '$a0'
                    mc.append('sw {}, {}($fp)'.format(register, code[2]))

            elif code[0] == 'pop':
                if code[3] == 'ra':
                    mc.append('lw $ra, {}($fp)'.format(code[2]))
                else:
                    register = self.getRegister(code[3], dc)
                    mc.append('lw {}, {}($fp)'.format(register, code[2]))

            elif code[0] == 'store':
                if code[3] == 'ra':
                    mc.append('sw $ra, {}($sp)'.format(code[2]))
                else:
                    register = self.getRegister(code[3], dc)
                    if str(register)[0] != '$':
                        mc.append("add $a0,$zero,{}".format(register))
                        register = '$a0'
                    mc.append('sw {}, {}($sp)'.format(register, code[2]))

            elif code[0] == 'load':
                if code[3] == 'ra':
                    mc.append('lw $ra, {}($sp)'.format(code[2]))
                else:
                    register = self.getRegister(code[3], dc)
                    mc.append('lw {}, {}($sp)'.format(register, code[2]))

            elif code[0] == 'j':
                mc.append('j {}'.format(code[3]))
            elif code[0] == 'j>':
                arg1 = self.getRegister(code[1], dc)
                mc.append('bgt {},$zero,{}'.format(arg1, code[3]))
            elif code[0] == 'return':
                mc.append('jr $ra')
            
            else:
                if code[0] == '+':
                    if code[1] == 'fp':
                        mc.append("add $fp,$fp,{}".format(code[2]))
                    elif code[1]=='sp':
                        mc.append("add $sp,$sp,{}".format(code[2]))
                    else:
                        arg1 = self.getRegister(code[1], dc)
                        arg2 = self.getRegister(code[2], dc)
                        arg3 = self.getRegister(code[3], dc)
                        if str(arg1)[0] != '$':
                            mc.append("add $a1,$zero,{}".format(arg1))
                            arg1 = '$a1'
                        mc.append("add {},{},{}".format(arg3, arg1, arg2))

                elif code[0] == '-':
                    if code[1] == 'fp':
                        mc.append("sub $fp,$fp,{}".format(code[2]))
                    elif code[1] == 'sp':
                        mc.append("sub $sp,$sp,{}".format(code[2]))
                    else:
                        arg1 = self.getRegister(code[1], dc)
                        arg2 = self.getRegister(code[2], dc)
                        arg3 = self.getRegister(code[3], dc)
                        if str(arg1)[0]!='$':
                            mc.append("add $a1,$zero,{}".format(arg1))
                            arg1 = '$a1'
                        if str(arg2)[0]!='$':
                            mc.append("add $a2,$zero,{}".format(arg2))
                            arg2 = '$a2'
                        mc.append("sub {},{},{}".format(arg3, arg1, arg2))

                elif code[0] == '*':
                    arg1 = self.getRegister(code[1], dc)
                    arg2 = self.getRegister(code[2], dc)
                    arg3 = self.getRegister(code[3], dc)
                    if str(arg1)[0]!='$':
                        mc.append("add $a1,$zero,{}".format(arg1))
                        arg1 ='$a1'
                    if str(arg2)[0]!='$':
                        mc.append("add $a2,$zero,{}".format(arg2))
                        arg2 = '$a2'
                    mc.append("mul {},{},{}".format(arg3, arg1, arg2))

                elif code[0] == '/':
                    arg1 = self.getRegister(code[1], dc)
                    arg2 = self.getRegister(code[2], dc)
                    arg3 = self.getRegister(code[3], dc)
                    if str(arg1)[0]!='$':
                        mc.append("add $a1,$zero,{}".format(arg1))
                        arg1='$a1'
                    if str(arg2)[0]!='$':
                        mc.append("add $a2,$zero,{}".format(arg2))
                        arg2 = '$a2'
                    mc.append("div {},{},{}".format(arg3, arg1, arg2))
                        
                elif code[0] == '%':
                    arg1 = self.getRegister(code[1], dc)
                    arg2 = self.getRegister(code[2], dc)
                    arg3 = self.getRegister(code[3], dc)
                    if str(arg1)[0]!='$':
                        mc.append("add $a1,$zero,{}".format(arg1))
                        arg1='$a1'
                    if str(arg2)[0]!='$':
                        mc.append("add $a2,$zero,{}".format(arg2))
                        arg2 = '$a2'
                    mc.append("div {},{},{}".format(arg3, arg1, arg2))
                    mc.append("mfhi {}".format(arg3))

                elif code[0] == '<':
                    arg1 = self.getRegister(code[1], dc)
                    arg2 = self.getRegister(code[2], dc)
                    arg3 = self.getRegister(code[3], dc)
                    if str(arg1)[0]!='$':
                        mc.append("add $a1,$zero,{}".format(arg1))
                        arg1='$a1'
                    if str(arg2)[0]!='$':
                        mc.append("add $a2,$zero,{}".format(arg2))
                        arg2 = '$a2'
                    mc.append("slt {},{},{}".format(arg3, arg1, arg2))

                elif code[0] == '>':
                    arg1 = self.getRegister(code[1], dc)
                    arg2 = self.getRegister(code[2], dc)
                    arg3 = self.getRegister(code[3], dc)
                    if str(arg1)[0]!='$':
                        mc.append("add $a1,$zero,{}".format(arg1))
                        arg1='$a1'
                    if str(arg2)[0]!='$':
                        mc.append("add $a2,$zero,{}".format(arg2))
                        arg2 = '$a2'
                    mc.append("sgt {},{},{}".format(arg3, arg1, arg2))

                elif code[0] == '!=':
                    arg1 = self.getRegister(code[1], dc)
                    arg2 = self.getRegister(code[2], dc)
                    arg3 = self.getRegister(code[3], dc)
                    if str(arg1)[0] != '$':
                        mc.append("add $a1,$zero,{}".format(arg1))
                        arg1 = '$a1'
                    if str(arg2)[0] != '$':
                        mc.append("add $a2,$zero,{}".format(arg2))
                        arg2 = '$a2'
                    mc.append("sne {},{},{}".format(arg3, arg1, arg2))

                elif code[0] == '==':
                    arg1 = self.getRegister(code[1], dc)
                    arg2 = self.getRegister(code[2], dc)
                    arg3 = self.getRegister(code[3], dc)
                    if str(arg1)[0] != '$':
                        mc.append("add $a1,$zero,{}".format(arg1))
                        arg1 = '$a1'
                    if str(arg2)[0] != '$':
                        mc.append("add $a2,$zero,{}".format(arg2))
                        arg2 = '$a2'
                    mc.append("seq {},{},{}".format(arg3, arg1, arg2))
        
        sys.stdout.flush()
        return
