from flask import Flask,render_template,request,redirect, url_for, flash, session
from flask_bootstrap import Bootstrap
import random,datetime
from functools import wraps
import time
import functools
import os

'''
西门子库文件 python-snap7
'''
# import s7read
from snap7 import *
import snap7.client as client
from snap7.util import *
from snap7.snap7types import *

'''
罗克韦尔AB Pylogix
'''
from pylogix import *

'''
倍福库文件 PyADS
'''
'''
influxDB 库文件
'''
from influxdb_client import InfluxDBClient,Point
# from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import random
import time

########登陆信息 暂时使用 还没启用数据库管
users = [
    {
        'username': 'root',
        'password': 'root'
    },
    {
        'username': 'username',
        'password': 'password'
    }
]

app = Flask(__name__)

## 设置密钥可以有效防止跨站请求伪造的攻击
app.config['SECRET_KEY'] = 'myproject'
app.secret_key = 'myproject'

############ 登陆验证 不登陆无法进入其它页面 ###################
def is_login(f):
    """用来判断用户是否登录成功"""
    # 保证函数在加了装饰器之后返回的不是wrapper函数名，而是原函数名

    @functools.wraps(f)
    def inner(*args, **kwargs):
        # 判断session对象中是否有seesion['user'],
        # 如果包含信息， 则登录成功， 可以访问主页；
        # 如果不包含信息， 则未登录成功， 跳转到登录界面;
        # next_url = request.path
        if session.get('user', None):
            return f(*args, **kwargs)
        else:
            # flash('用户必须登陆才能访问%s' % f.__name__)
            return redirect(url_for('home'))##返回首页 url_for 调用的是函数名
    return inner 
#################################################################

@app.route("/")
def home():
    return render_template("home.html")
    # time1=random.randint(1,10)
    # print(time1)
    # return render_template("home.html",time=time1)

def is_admin(f):
    """用来判断用户是否登录成功"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        # 判断session对象中是否有seesion['user']等于root,
        # 如果包含信息， 则登录成功， 可以访问主页；
        # 如果不包含信息， 则未登录成功， 跳转到登录界面;；
        if session.get('user', None) == 'root':
            return f(*args, **kwargs)
        else:
            flash('只有管理员root才能访问%s' % f.__name__)
            return redirect(url_for('login'))

    return wrapper

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', None)
        password = request.form.get('password', None)
        # 当所有的信息遍历结束， 都没有发现注册的用户存在， 则将注册的用户添加到服务器， 并跳转登录界面;
        for user in users:
            if user['username'] == username:
                return render_template('register.html', messages='用户%s已经存在' % username)
        else:
            users.append(dict(username=username, password=password))
            # 出现一个闪现信息;
            flash('用户%s已经注册成功，请登陆.....' % username, category='info')
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', None)
        password = request.form.get('password', None)
        for user in users:
            if user['username'] == username and user['password'] == password:
                #  将用户登录的信息存储到session中;
                session['user'] = username
                return redirect(url_for('setting'))
            if user['username'] == username and user['password'] != password:
                # 出现一个闪现信息;
                flash("密码错误，请重新登陆","wrong")
                return redirect("#idlogin")
                # return redirect(request.url)
        else:
            # flash(ss,"ss")
            flash("该用户不存在，请重新登陆","none")
            return redirect("#idlogin")
    return render_template("home.html")

@app.route('/list')
@is_login
def list():
    return render_template('list.html', users=users)


@app.route('/logout')
def logout():
    #  将用户存储到session中的信息删除;
    session.pop('user')
    flash('注销成功....')
    return render_template('home.html')

@app.route('/delete/<string:username>/')
def delete(username):
    for user in users:
        # 用户存在， 则删除;
        if username == user['username']:
            users.remove(user)
            flash('删除%s用户成功' % username)
    # else:
    #     flash('用户%s不存在'%username)

    # 删除成功， 跳转到/list/路由中.....
    return redirect(url_for('list'))

@app.route("/setting")
@is_login
def setting():
    return render_template("setting.html")

@app.route("/siemens",methods=("GET","POST"))
@is_login
def siemens():
    ## 反馈系统运行状态

    if request.method =="POST":
            flash("run", "run")
            forminfo = request.form.to_dict()
            # 该页面的表单信息，只要submit都传到这里，其中包括plc的连接信息 ip[str] rack[int] slot[int]
            # 还包括变量地址信息以及influxdb配置信息，通过字典长度区分各个表单
            global plc
            # plc=1## 用全局变量传递plc client
            if len(forminfo)==3: #PLC 连接信息
                print(forminfo)
                plc=s7connect(str(forminfo["ipaddress"]),int(forminfo["rack"]),int(forminfo["slot"])) #数据类型转换
                # ip=forminfo["ipaddress"]
                # print(ip)
                # print(plc)
            if len(forminfo)==2: #变量地址
                print(forminfo)
                data=s7read(plc,forminfo["iqm"],forminfo["address"])
                print(data)
                    # return data

            elif len(forminfo)==4: # influxdb连接信息
                print(forminfo)
                influxdbip = forminfo["influxdb"]
                token = forminfo["token"]
                measurement = forminfo["measurement"]
                cycle=forminfo["cycle"]
                influxDB(influxdbip,token,measurement,cycle)
            # flash(forminfo,"connect1")
            return redirect("#")
            # return render_template("siemens.html")
    return render_template("siemens.html")

@app.route("/beckoff",methods=["POST","GET"])
@is_login
def beckoff():
    # return render_template("b.html")
    # if request.method=='POST':
    #     aa=request.files.get("ss")
    return render_template("beckoff.html")

@app.route("/rockwell")
@is_login
def rockwell():
    # return render_template("b.html")
    return render_template("rockwell.html")

@app.route("/opcua")
@is_login
def opcua():
    # return render_template("b.html")
    return render_template("opcua.html")

@app.route("/a")
@is_login
def a():
    print("ssssssssssssssss")
    ss="sssssssssssssssssssssssss"
    return redirect("/siemens#influxdbsetting")
    # return render_template("siemens.html",ss=ss)


@app.route("/",methods=("POST","GET"))
@is_login
def c():
    if request.method == "POST":
        aa=request.form.to_dict()
        print(aa)
        return render_template("c.html")

def s7connect(ip,rack,slot):
    try:
        plc = client.Client()
        # print(ip,rack,slot)
        plc.connect(ip, rack, slot)
    except Exception as e:
        flash("连接失败，请确认IP或网络连通性","connect0")
    else:
        state=plc.get_cpu_state()
        flash(ip+" 连接成功","connect1")
        return plc

@app.route("/dis",methods=("POST","GET"))
@is_login
def s7disconnect():
    try:
        print("disconnect")
        # plc = client.Client()
        plc.disconnect()
    except Exception:
        flash("断开失败","connect0") ##connect0 失败提醒
    else:
        flash("已断开连接","connect1") ## connect1 操作成功提示
    return redirect("/siemens#connection")

@app.route("/siemens",methods=("POST","GET"))
@is_login
def s7read(plc,iqm,address):

    # t = (address[0])

    # if request.methods=="POST":
    #     aa=request.form.to_dict
    #     print(aa)
    #     iqm=aa[("iqm")]
    #     address=aa[("address")]
    #     t=iqm
    #     b = int((address.split(".")[0][1:]))
    #     c = int((address.split(".")[1]))
    tt=""
    t=areas[iqm]
    # print(address)
    if address=='':
        address2=0.0
    else:
        address2=(float(address))
    if t ==129:
        tt = "I "
    if t == 130:
        tt = "Q "
    if t == 131:
        tt = "M "

    b = (int(address2))
    c = (int((address2-b)*10))

    print(t,b,c)
    try:
        variable = tt + address
        print(variable)
        timenow = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        result=plc.read_area(t,0,b,8)  ## 变量类型，0，地址起始，固定8位
        data = get_bool(result, 0, c)  ## 地址偏移值
    except Exception as e:
        print(e)
    else:
        flash(data, "value")
        flash(timenow, "time")
        flash(variable,"variable")
        return data

    # except Exception as e:
    #     print(e)
    #     flash(e,"connect1")
    # else:
    #     pass
    #     redirect("#iqmselect")


@app.route("/influxDB",methods=("POST","GET"))
@is_login
def influxDB(influxdbip,token,measurement,cycle):
    a=1
    bucket = "test"
    token="HTvG6oIApfABybjjYd_6Jehf8AEWkLStYw0qftanx9ijF05-UsLZ9pVqI604PwuRlhv8IkuIZshYaqVFTC0DXA=="
    client = InfluxDBClient(url=influxdbip,token=token,org="su")
    write_api = client.write_api(write_options=SYNCHRONOUS)
    query_api = client.query_api()
    cycle=int(cycle)
    cycle=(cycle/1000)
    flash("开始写入influxDB","influx")
    while 1:
        try:
            ss=1
            xx=2
            p = Point(measurement).tag("location", "108厂房").field("温度", ss)
            q = Point(measurement).tag("location", "beijing").field("2", xx)
            write_api.write(bucket=bucket, org="su", record=[p,q])
            print("2222")
            time.sleep(cycle)

        except Exception as e:
            print(e)
            break



##################################################
app.run(host="0.0.0.0",port=5000)