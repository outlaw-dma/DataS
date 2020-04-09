from blueprints.influxdb import *
from blueprints.login import is_login

rockwell_ = Blueprint("rockwell_",__name__)

'''
罗克韦尔AB Pylogix 0.6.2
'''
# from pylogix import *
from pylogix import PLC

class Timer(object):

    def __init__(self, data):
        self.PRE = unpack_from('<i', data, 6)[0]
        self.ACC = unpack_from('<i', data, 10)[0]
        bits = unpack_from('<i', data, 2)[0]
        self.EN = get_bit(bits, 31)
        self.TT = get_bit(bits, 30)
        self.DN = get_bit(bits, 29)

class Motion(object): # Su 仿照Timer类型添加Motion类型 ToDo

    def __init__(self, data):
        self.PRE = unpack_from('<i', data, 6)[0]
        self.ACC = unpack_from('<i', data, 10)[0]
        bits = unpack_from('<i', data, 2)[0]
        self.EN = get_bit(bits, 31)
        self.TT = get_bit(bits, 30)
        self.DN = get_bit(bits, 29)

def get_bit(value, bit_number):
    '''
    Returns the specific bit of a word
    '''
    mask = 1 << bit_number
    if (value & mask):
        return True
    else:
        return False


######################### 罗克韦尔 ##############################

global rockwellip,rockwell_device_list,taglist
rockwellip=''
rockwelldata=()
ttt=''

@rockwell_.route("/rockwell",methods=["POST","GET"])
@is_login
def rockwell():
    ## Rockwell AB PLC # #108厂房设备
    return render_template("rockwell.html")

@rockwell_.route("/rockwellread")
@is_login
def rockwellread():    #'读取函数'
    print("readlist")
    print(taglist)

    ### 分批读取函数 每次读取10个变量
    def readten(tags_list):
        l = len(tags_list)  # 变量表长度，如果大于10 必须分批读取保证不报错
        x = l // 10  # 取整
        y = l % 10  # 取余数
        a = 0  # 每一组变量的上标
        val = []  # 初始化列表 每一组变量值
        for n in range(x):
            if n < x:
                val = val + comm.Read(tags_list[10 * a:10 * (a + 1)])
                a += 1
                n += 1
            if n == x and y != 0:
                val = val + comm.Read(tags_list[10 * a:10 * a + y])
        vall = val
        return vall

    with PLC() as comm:
        tagname=[]
        tagvalue=[]
        comm.IPAddress=rockwellip
        aa=readten(taglist) #调用函数分批读取变量
        ttt=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(aa)
        for a in aa:
            tagname.settingsend(a.TagName)
            tagvalue.settingsend(a.Value)
        # 输出到前端页面
        rockwelldata=dict(zip(tagname,tagvalue))
        print(rockwelldata)
        # return redirect("#data")
    return render_template("rockwell.html",rockwelldata=rockwelldata,ttt=ttt)
    # return render_template("rockwell.html")

def rockwellreadexcel(file):
    print("readexcel"+file.filename)
    # data = pd.DataFrame(pd.read_excel(file))
    # data2 = pd.read_excel(file, usecols=[0], header=None)  ##第一列 无表头 输出为DataFrame格式 带索引
    data2 = pd.read_excel(file)  ##输出为DataFrame格式 后续剔除未知类型
    # data2=data2.dropna() ##剔除异常的nan
    data2 = data2[data2['TagType'].isin(["BOOL"])] ##可以读取的类型 ["BOOL", "TIMER", "REAL"]
    ##剔除程序名和已知类型之外的数据
    data2 = data2['TagName']
    print(data2)
    global taglist
    taglist = data2.to_numpy().tolist()  # 转数组 转列表
    # taglist = sum(data2, [])  # 嵌套列表平铺 变量表list
    print(taglist)

@rockwell_.route("/rockwellscan",methods=["POST","GET"])
@is_login
def rockwellscan():
    with PLC() as comm:
        # 设备扫描
        deviceip = []
        devicename = []
        devices = comm.Discover()
        for device in devices.Value:
            deviceip.settingsend(device.IPAddress)
            devicename.settingsend(device.ProductName + ' ' + device.IPAddress)
        global rockwell_device_list
        rockwell_device_list = dict(zip(devicename, deviceip))  # 创建设备字典 写入全局变量
        scanresult="扫描到"+str(len(rockwell_device_list))+"台设备"
        print(scanresult)
        flash(scanresult,"scanresult") #扫描完成flash提示
        return redirect(("rockwellscan2"))
        # dev_list=str(device_dict)
        # return redirect(url_for(rockwell)) # url_for函数跳转
        # flash(device_dict,"device_dict") #设备扫描结果显示到前端页面下拉列表

@rockwell_.route("/rockwellscan2",methods=["POST","GET"])
@is_login
def rockwellscan2():
        if request.method == "POST":
            flash("run", "run")
            forminfo=request.form.to_dict() ## to_dict()加括号
            # 该页面的表单信息，只要submit都传到这里
            # forminfo=request.form.get('devicelist') # 获取到的value是str字符串
            # 还包括变量地址信息以及influxdb配置信息，通过字典长度区分各个表单
            print(forminfo)
            # print(type(forminfo))
            # aa=type(forminfo)

            ######## 每次“开始连接”实际只是获取选择的设备ip并写入全局变量
            # 程序逻辑调整为rockwellscan运行后跳转rockwellscan2 但是页面会整体刷新造成列表变化~~~~~~~~~~~
            if len(forminfo)==1 : # AB PLC 连接信息 只需要IP
                print(forminfo)
                aa=(forminfo["devicelist"]).split(" ")
                aa=aa[len(aa)-1] #获取ip
                global rockwellip # 全局变量 要先声明globa 再修改
                rockwellip=aa
                ss=("已连接到 "+str(forminfo["devicelist"]))
                flash(ss, "scanresult")  # 连接完成
                # print(rockwellip)

            # if (forminfo)=={}:  # 上传变量表 #
            if len(forminfo)==2: #### 是excel就调用readexcel
                print("22222222222")
                try:
                    file = request.files.get('file')
                    file.save('D:/' + secure_filename(file.filename))  ## C盘写入权限受限Permission denied 暂存在D盘，linux中应该没问题
                    rockwellreadexcel(file)
                except Exception as e:
                    print(e)
                    flash(e, "uploadstatus")
                else:
                    # 保存测试
                    flash("变量表上传成功", "uploadstatus")

            # if len(forminfo) == 2:  # 变量地址
            #     print(forminfo)
            #     data = s7read(plc, forminfo["iqm"], forminfo["address"])
            #     print(data)
            #     # return data

            elif len(forminfo) == 4:  # influxdb连接信息
                # print("11111111111")
                print(forminfo)
                influxdbip = forminfo["influxdb"]
                token = forminfo["token"]
                measurement = forminfo["measurement"]
                cycle = forminfo["cycle"]
                influxDB(influxdbip, token, measurement, cycle)
            # flash(forminfo,"connect1")
        # return redirect("#")
        # flash(rockwell_device_list,"dev_list") # flash只能传递字符串
        # return jsonify()
        # return redirect(url_for("rockwell"))
        return render_template("rockwell.html",dev_list=rockwell_device_list)#设备扫描结果显示到前端页面下拉列表
    ## 定向页面逻辑，此处要在rockwellscan中处理POST请求
    ## 前端调用后台程序 href=“xx” 通过路由调用，还有没有别的方法 采用url_for()跳转 参考登录函数处理方法
    # return redirect("#")

@rockwell_.route("/rockwell_get_all_vars")
@is_login
#### 获取所有变量 并下载 # 待办，剔除程序名称，编写变量读取函数，连续获取变量表 时间不变bug
def rockwell_get_all_vars(): #
    # print("111111111111111")
    with PLC() as comm:
        # print("111111111111")
        ####### 无法连续运行重复获取变量表？ 连续点击不进入循环 直接下载附件？？ 如果要刷新变量表需要再次“开始连接”##############
        print(rockwellip)
        if rockwellip=='':
            print("请先选择设备IP地址")
        else:
            print(rockwellip)
            comm.IPAddress = rockwellip #全局变量
            # comm.IPAddress="192.168.100.200"
            print("2222222222")
            try:
                tags = comm.GetTagList() #输出是Response结构体类型需要解析
                comm.Close()
            except Exception as e:
                print(e)
                #缺一个return ，读取错误的错误处理
            else:
                tagname=[]
                tagtype=[]
                head=["TagName","TagType"]
                for t in tags.Value:
                    tagname.settingsend(t.TagName)
                    tagtype.settingsend(t.DataType)
                taglist = pd.DataFrame({'tagname': tagname, 'tagtype': tagtype}) #采用Pandas格式化
                # print(taglist)
                tt = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S') #时间标识符
                filepath=("D:/Taglist "+tt+".xlsx")
                print(filepath)
                ## 变量表文件暂存以备发送和自动读取
                taglist.to_excel(filepath, encoding='utf-8', index=False, header=head) #写入excel
                ## 变量表文件下载
                return send_file(filepath,as_attachment=True) #向前端发送文件 下载 比send_from_directory简化
                # return send_from_directory(filepath,as_attachment=True) #