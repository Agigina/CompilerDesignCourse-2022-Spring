from email import message
from flask import Blueprint, render_template, request, send_file, redirect, url_for
import shutil

from Compiler.tools import *
import os
import pandas as pd

blue_print = Blueprint('blue_print', __name__)


@blue_print.route('/', methods=["GET", "POST"])
def index():
	if request.method == "POST":
		load = loading()

		load.readGrammarFile('grammer_final.txt')
		f = request.files['myfiles']
		if os.path.exists("source.c"):
			os.remove("source.c")
		f.save(f.filename)
		if f.filename != "source.c":
			shutil.copy(f.filename, "source.c")
		print(f.filename)

		# 进行各种分析并且写入文件
		types = []
		datas = []
		idnums = []
		with open(f.filename, 'r') as fd:
			content = str(fd.read())
			words = load.input_token(content)
			for item in words:
				types.append(item["type"])
				datas.append(item["data"])
				idnums.append(item["idnum"])
			fd.close()

		df = pd.DataFrame({"类型": types, "值": datas, "属性值": idnums})
		df.to_csv("Lex.csv")

		load.get_dot()
		load.set_First()
		family = ItemSetFamily(load)
		family.buildFamily()
		grammars = SyntacticAnalyzer(load, family)
		grammars.getTables()
		grammars.isRecognizable(content)

		if not grammars.syntacticRst:
			return redirect(url_for("blue_print.error", errorname=200))
		if not grammars.grammarRst:
			return redirect(url_for("blue_print.error", errorname=300))

		parseRst = grammars.getParseRst()
		statestacks = []
		shifts = []
		inputs = []

		for item in parseRst:
			temp = item['stateStack']
			s = ''
			for subitem in temp:
				s += str(subitem)+' '
			statestacks.append(s.strip("->"))
			temp = item['shiftStr']
			s = ''
			for subitem in temp:
				s += str(subitem['type'])+' '
			shifts.append(s)
			temp = item['inputStr']
			s = ''
			for subitem in temp:
				s += str(subitem['type'])+' '
			inputs.append(s)

		df = pd.DataFrame({"状态栈": statestacks, "移动栈": shifts, "输入栈": inputs})
		df.to_csv("Grammar.csv")

		operations = []
		arg1s = []
		arg2s = []
		ress = []
		for item in grammars.middleCode:
			operations.append(item[0])
			arg1s.append(item[1])
			arg2s.append(item[2])
			ress.append(item[3])

		df = pd.DataFrame(
			{"operation": operations, "arg1": arg1s, "arg2": arg2s, "result": ress})
		df.to_csv("Fourth.csv")

		names = []
		types = []
		sizes = []
		offsets = []
		places = []
		functions = []

		for item in grammars.symbolTable:
			names.append(item.name)
			types.append(item.type)
			sizes.append(item.size)
			offsets.append(item.offset)
			places.append(item.offset)
			functions.append(item.function)

		df = pd.DataFrame(
			{"符号标识符": names, "类型": types, "长度": sizes, "偏移量": offsets,
			 "中间变量": places, "所在函数": functions})
		df.to_csv("Symbols.csv")

		code = ObjectCodeGenerator(grammars.middleCode, grammars.symbolTable)
		code.genMips()
		content = ''
		content2 = ''
		for item in code.mipsCode:
			content += item+'\n'
			content2 += item+'<br>'
		with open("Code.txt", 'w') as f:
			print(content, file=f)
			f.close()
		with open('Compiler/templates/m.html', 'w', encoding='utf-8') as f:
			pre = '''
<!DOCTYPE html>
<html lang="en" >
<head>
  <meta charset="UTF-8">
  <title>目标代码</title>
  <link rel="stylesheet" href="static/css/table_m.css">

</head>
<body>
<!-- partial:index.partial.html -->
<div class="flex-container">
	  <a class="open" href="/main" aria-hidden="true">
		<svg t="1650252646594" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="2576" width="200" height="200"><path d="M261.31 467.211l99.327-108.188-55.43-60.327L138.92 479.722l-27.648 30.141 193.981 211.39 55.34-60.55-99.283-108.188H677.5V467.21h-416.19zM442.423 1024h391.791a75.42 75.42 0 0 0 55.608-25.021 89.533 89.533 0 0 0 22.84-60.55V85.526A82.276 82.276 0 0 0 834.036 0H442.246v85.304H794.68a37.576 37.576 0 0 1 27.781 12.243 44.522 44.522 0 0 1 11.665 30.052v768.757a41.227 41.227 0 0 1-39.446 42.34H442.424V1024z m0 0" p-id="2577"></path></svg>	  </a>
	  </a>
	  <div class="vscode-window" id="vscode">
		<div class="title-bar" aria-hidden="true">
		  <a aria-hidden="true" class=close href="/download">
			<svg t="1650251848901" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="2645" width="16" height="16"><path d="M502.010485 765.939573c3.773953 3.719718 8.686846 5.573949 13.596669 5.573949 0.075725 0 0.151449-0.010233 0.227174-0.011256 0.329505 0.016373 0.654916 0.050142 0.988514 0.050142 0.706081 0 1.400906-0.042979 2.087545-0.116657 4.352121-0.366344 8.607028-2.190899 11.961426-5.496178l335.053985-330.166675c7.619538-7.509021 7.709589-19.773346 0.200568-27.393907s-19.774369-7.711636-27.39493-0.201591L536.193005 706.304358 536.193005 50.019207c0-10.698666-8.67252-19.371186-19.371186-19.371186s-19.371186 8.67252-19.371186 19.371186l0 657.032164-306.881342-302.44838c-7.618515-7.509021-19.883863-7.419993-27.393907 0.199545-7.509021 7.619538-7.419993 19.884886 0.199545 27.393907L502.010485 765.939573z" p-id="2646" fill="#e6e6e6"></path><path d="M867.170139 711.020776c-10.698666 0-19.371186 8.67252-19.371186 19.371186l0 165.419494c0 13.054317-10.620895 23.675212-23.676236 23.675212L205.182103 919.486668c-13.054317 0-23.676236-10.620895-23.676236-23.675212L181.505867 730.391962c0-10.698666-8.67252-19.371186-19.371186-19.371186s-19.371186 8.67252-19.371186 19.371186l0 165.419494c0 34.416857 28.000728 62.416562 62.417585 62.416562l618.941638 0c34.417881 0 62.417585-27.999704 62.417585-62.416562L886.540302 730.391962C886.541325 719.693296 877.868805 711.020776 867.170139 711.020776z" p-id="2647" fill="#e6e6e6"></path></svg>			
		  </a>
		  <div class="doc-name">
			目标代码 - Desktop - Visual Studio Code
		  </div>
		</div>
		<div class="content">'''
			after = '''
		</div>
	  </div>
	</div>
  <script  src="static/js/code.js"></script>

</body>
</html>
			'''
			print(pre, file=f)
			print(content2, file=f)
			print(after, file=f)
			f.close()
		return main()
	return render_template('upload.html')


@blue_print.route('/main')
def main():
	return render_template('main.html')


@blue_print.route('/download', methods=["GET", "POST"])
def download():
	# print("aaa",os.listdir())
	return send_file("../Code.txt", as_attachment=True)


@blue_print.route('/m')
def m():
	if not os.path.exists("Code.txt"):
		return redirect(url_for("blue_print.error", errorname=400))
	return render_template('m.html')


@blue_print.route('/p')
# fourth
def p():
	if not os.path.exists("Fourth.csv"):
		return redirect(url_for("blue_print.error", errorname=400))
	df = pd.read_csv("Fourth.csv", usecols=[1, 2, 3, 4])
	lex = []
	for i in range(len(df)):
		lex.append(dict(df.iloc[i]))
	return render_template('p.html', lis=lex)


@blue_print.route('/l')
# lex
def l():
	if not os.path.exists("Lex.csv"):
		return redirect(url_for("blue_print.error", errorname=400))
	df = pd.read_csv("Lex.csv", usecols=[1, 2, 3])
	lex = []
	for i in range(len(df)):
		lex.append(dict(df.iloc[i]))
	return render_template('l.html', lex=lex)


@blue_print.route('/t')
# grammar
def t():
	if not os.path.exists("Grammar.csv"):
		return redirect(url_for("blue_print.error", errorname=400))
	df = pd.read_csv("Grammar.csv", usecols=[1, 2, 3])
	lex = []
	for i in range(len(df)):
		lex.append(dict(df.iloc[i]))
	return render_template('t.html', lis=lex)


@blue_print.route('/g')
def g():
	if not os.path.exists("Symbols.csv"):
		return redirect(url_for("blue_print.error", errorname=400))
	df = pd.read_csv("Symbols.csv", usecols=[1, 2, 3, 4, 5, 6])
	lex = []
	for i in range(len(df)):
		lex.append(dict(df.iloc[i]))
	return render_template('g.html', lex=lex)


@blue_print.route('/error/<errorname>')
def error(errorname):
	if errorname == "100":
		message = "词法分析出错"
	elif errorname == "200":
		message = "语法分析出错"
	elif errorname == "300":
		message = "语义分析出错"
	elif errorname == "400":
		message = "请重新上传文件"
	else:
		message = "未知错误"
	return render_template('LogInFirst.html', message=message)
