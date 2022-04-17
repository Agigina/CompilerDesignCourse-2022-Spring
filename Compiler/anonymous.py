from email import message
from flask import Blueprint, render_template, request, send_from_directory, redirect, url_for
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
            tokens = load.input_token(content)
            for item in tokens:
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
        ana = SyntacticAnalyzer(load, family)
        ana.getTables()
        ana.isRecognizable(content)

        if not ana.syntacticRst:
            return redirect(url_for("blue_print.error", errorname=200))
        if not ana.grammarRst:
            return redirect(url_for("blue_print.error", errorname=300))
        
        ana.getParseRst()
        return main()
    return render_template('upload.html')


@blue_print.route('/main')
def main():
    return render_template('main.html')


@blue_print.route('/download/<filename>', methods=["GET", "POST"])
def download(filename):
    return send_from_directory("", filename, as_attachment=True)


@blue_print.route('/s')
def s():
    return render_template('s.html')


@blue_print.route('/m')
def m():
    return render_template('m.html')


@blue_print.route('/p')
def p():
    return render_template('p.html')


@blue_print.route('/l')
# lex
def l():
    if not os.path.exists("Lex.csv"):
        return redirect(url_for("blue_print.error", errorname=400))
    df=pd.read_csv("Lex.csv",usecols=[1,2,3])
    lex=[]
    for i in range(len(df)):
        lex.append(dict(df.iloc[i]))
    return render_template('l.html',lex=lex)


@blue_print.route('/t')
def t():
    return render_template('t.html')


@blue_print.route('/g')
def g():
    return render_template('g.html')


@blue_print.route('/error/<errorname>')
def error(errorname):
    if errorname == "100":
        message = "词法分析出错"
    elif errorname == "200":
        message = "语法分析出错"
    elif errorname == "300":
        message = "语义分析出错"
    elif errorname=="400":
        message="请重新上传文件"
    else:
        message = "未知错误"
    return render_template('LogInFirst.html', message=message)
