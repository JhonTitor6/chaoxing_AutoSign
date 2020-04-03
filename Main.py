import requests, json, time, datetime

username = []
passwd = []

# server酱推送
SCKEY = ''
# 设置轮询间隔(单位:秒,建议不低于5)
speed = 90

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.108 Safari/537.36'}

uid = []
cookies = []
coursedata = [[] for i in range(20)]
activeList = []
course_index = 0
status = 0
activates = []
a = 1   #状态
index = 0  #课程数量，打印课程用

#用户数据保存在 userinfo.txt  格式为 一行帐号，一行密码
def getuser():
    with open("userinfo.txt", "r") as f:  # 打开文件
        data = f.readlines()  # 读取文件
        isusername=1    #交替输入username和passwd
        for each in data:
            each = each.replace('\n','').replace(' ','')
            if(isusername):
                username.append(each)
                isusername=0
            else:
                passwd.append(each)
                isusername=1
'''         
    global username,passwd
    print("请输入您的帐号密码：")
    for i in range(100):
        temp=input()
        if(temp==''):
            break
        username.append(temp.replace(' ',''))
        passwd.append(input().replace(' ',''))
'''
def login(username, passwd):  # 获取cookie
    url = 'https://passport2-api.chaoxing.com/v11/loginregister'
    data = {'uname': username, 'code': passwd, }
    session = requests.session()
    cookie_jar = session.post(url=url, data=data, headers=headers).cookies
    cookie_t = requests.utils.dict_from_cookiejar(cookie_jar) #cookiejar转字典
    return cookie_t

#需要传入cookie
def taskactivelist(courseId, classId, i, cookie):
    global a
    url = "https://mobilelearn.chaoxing.com/ppt/activeAPI/taskactivelist?courseId=" + str(courseId) + "&classId=" + str(
        classId) + "&uid=" + uid
    res = requests.get(url, headers=headers, cookies=cookie)
    respon = res.status_code
    if respon == 200:  # 网页状态码正常
        data = json.loads(res.text)
        activeList = data['activeList']
        # print(activeList)
        for item in activeList:
            if ("nameTwo" not in item):
                continue
            if (item['activeType'] == 2 and item['status'] == 1):
                signurl = item['url']  # 提取activePrimaryId
                aid = getvar(signurl)
                if (aid not in activates):
                    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '[签到]', coursedata[i]['name'],
                          '查询到待签到活动 活动名称:%s 活动状态:%s 活动时间:%s aid:%s' % (
                          item['nameOne'], item['nameTwo'], item['nameFour'], aid))
                    sign(aid, uid, i)  # print('调用签到函数')
                    a = 2
    else:
        print('error', respon)  # 不知道为啥...


def getvar(url):
    var1 = url.split("&")
    for var in var1:
        var2 = var.split("=")
        if (var2[0] == "activePrimaryId"):
            return var2[1]
    return "ccc"

def writelog(msg):
    with open('chaoxinglog.txt','r+') as f:
        f.read()
        f.write(str(msg))
        if('\n' not in msg):
            f.write("\n")

#需要传入cookie
def sign(aid, uid, i, cookie):
    global status, activates
    url = "https://mobilelearn.chaoxing.com/pptSign/stuSignajax?activeId=" + aid + "&uid=" + uid + "&clientip=&latitude=-1&longitude=-1&appType=15&fid=0"
    res = requests.get(url, headers=headers, cookies=cookie)
    #push(SCKEY, res.text)
    if (res.text == "success"):
        #写入log
        msg = "用户:" + uid + ' 课程: ' + coursedata[i]['name'] +" 签到成功！"
        writelog(msg)
        print(msg)
        activates.append(aid)
        status = 2
    else:
        #写入log
        msg = res.text + '签到失败'
        writelog(msg)
        print(msg)
        activates.append(aid)

'''
def push(SCKEY, msg):
    if SCKEY.isspace() or len(SCKEY) == 0:
        return
    else:
        api = 'https://sc.ftqq.com/' + SCKEY + '.send'
        title = u"签到辣!"
        content = '课程: ' + coursedata[i]['name'] + '\n\n签到状态:' + msg
        data = {
            "text": title,
            "desp": content
        }
        req = requests.post(api, data=data)
'''
#传入cookie userindex用于打印username      传出coursedata
def getclass(cookie, userindex):
    tempcoursedata=[]
    url = "http://mooc1-api.chaoxing.com/mycourse/backclazzdata?view=json&rss=1"
    res = requests.get(url, headers=headers, cookies=cookie)
    cdata = json.loads(res.text)
    if (cdata['result'] != 1):
        print("课程列表获取失败")
    for item in cdata['channelList']:
        if ("course" not in item['content']):
            continue
        pushdata = {}
        pushdata['courseid'] = item['content']['course']['data'][0]['id']
        pushdata['name'] = item['content']['course']['data'][0]['name']
        # pushdata['imageurl']=item['content']['course']['data'][0]['imageurl']
        pushdata['classid'] = item['content']['id']
        tempcoursedata.append(pushdata)
    print("获取成功:")
    index=0
    for item in tempcoursedata:  # 打印课程
        print(str(index) + '.[用户帐号]',username[userindex],"课程名称:" + item['name'])
        index += 1
    return tempcoursedata
#传入第X号用户的序号
def monitor(userindex):
    global a
    tempcoursedata = coursedata[userindex][0]
    nowtime = datetime.datetime.now().strftime('%H:%M:%S')
    # 时段内监控，防止老师炸鱼
    if((nowtime.__gt__ ("07:30:00") and nowtime.__lt__ ("12:00:00")) or
            (nowtime.__gt__ ("14:30:00") and nowtime.__lt__ ("18:00:00"))):
        #第i号课程
        for i in range(len(tempcoursedata)):
            tempcourseid = tempcoursedata[i]['courseid']
            tempclassid = tempcoursedata[i]['classid']
            taskactivelist(tempcourseid, tempclassid, i, cookies[userindex])
            if a == 2:
                a = 0
            else:
                print(
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '[监控运行中][用户帐号]',username[userindex],
                    '课程:', format(tempcoursedata[i]['name'],"<20"), '未查询到签到活动')
        #else:
            #print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),"在7：30 - 12：00 and 14：30 - 18：00才监控")


def main():
    getuser()
    global cookies,uid
    #获取cookie uid
    for i in range(len(username)):
        tempcookie=login(username[i], passwd[i])
        cookies.append(tempcookie)
        uid = cookies[i]['UID']
        # 84529014
    #获取coursedata
    for i in range(len(username)):
        tempcoursedata = getclass(cookies[i], i)
        coursedata[i].append(tempcoursedata)
    #死循环遍历每个人的每门课程,第i个人
    count=0
    while(1):
        writelog(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'\t\t\t运行轮数'+str(count))
        count+=1
        for i in range(len(username)):
            monitor(i)
            print("-------------------------------------------------------------------------------------")
        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        time.sleep(2)  # 休眠时间在最上面设置

if __name__ == '__main__':
    main()