# coding=utf-8
import requests, json, time, datetime, os

username = []   # 账号
passwd = [] # 密码

# server酱推送SCKEY
SCKEY = ''

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.108 Safari/537.36'}

# 设置轮询间隔(单位:秒,建议不低于5)
speed = 90
uid = []
cookies = []
coursedata = [[] for i in range(20)]  # 20个用户的课程列表
activeList = []
monitor_list = [[] for i in range(20)]  # 20个用户的选中的监控课程
course_index = 0
status = 0
activates = [[] for i in range(20)]  # 20个用户的已签到列表
a = 0  # 状态
index = 0  # 课程数量，打印课程用
userindex = 0  # 当前监控的用户序号

# 从userinfo.txt读取用户
def getuser():
    with open("userinfo.txt", "r") as f:  # 打开文件
        data = f.readlines()  # 读取文件
        isusername = 1  # 交替输入username和passwd
        for each in data:
            if ('#' in each):
                continue
            each = each.replace('\n', '').replace(' ', '')
            if (isusername):
                username.append(each)
                isusername = 0
            else:
                passwd.append(each)
                isusername = 1


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

# 登录
def login(username, passwd):  # 获取cookie
    url = 'https://passport2-api.chaoxing.com/v11/loginregister'
    data = {'uname': username, 'code': passwd, }
    session = requests.session()
    cookie_jar = session.post(url=url, data=data, headers=headers).cookies
    cookie_t = requests.utils.dict_from_cookiejar(cookie_jar)  # cookiejar转字典
    return cookie_t

# 获取活动activePrimaryId
def getvar(url):
    var1 = url.split("&")
    for var in var1:
        var2 = var.split("=")
        if (var2[0] == "activePrimaryId"):
            return var2[1]
    return "ccc"


def writelog(msg):
    with open('chaoxinglog.txt', 'r+') as f:
        f.read()
        f.write(str(msg))
        if ('\n' not in msg):
            f.write("\n")


# 签到，需要传入cookie
def sign(aid, uid, coursename, cookie):
    global status, activates
    url = "https://mobilelearn.chaoxing.com/pptSign/stuSignajax?activeId=" + aid + "&uid=" + uid + "&clientip=&latitude=-1&longitude=-1&appType=15&fid=0"
    res = requests.get(url, headers=headers, cookies=cookie)
    # push(SCKEY, res.text)
    if (res.text == "success"):
        # 写入log
        msg = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "[用户] " + username[
            userindex] + ' [返回信息] ' + coursename + " 签到成功！"
        writelog(msg)
        print(msg)
        # 签到过的记录下来，防止反复检测到
        activates[userindex].append(aid)
        status = 2
    else:
        # 写入log
        msg = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " [用户] " + username[
            userindex] + ' [返回信息] ' + coursename + ' ' + res.text + ' 签到失败'
        writelog(msg)
        print(msg)
        activates[userindex].append(aid)


# 查看活动列表，需要传入cookie
def taskactivelist(courseId, classId, coursename, cookie, nowusername):
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
                if (aid not in activates[userindex]):
                    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '[用户]', nowusername, '[签到]',
                          coursename,
                          '查询到待签到活动 活动名称:%s 活动状态:%s 活动时间:%s aid:%s' % (
                              item['nameOne'], item['nameTwo'], item['nameFour'], aid))
                    try:
                        sign(aid, uid, coursename, cookie)  # print('调用签到函数')
                    except:
                        msg = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\t\t\ttaskactivelist error'
                        print(msg)
                        writelog(msg)
                    a = 2
    else:
        print('error', respon)  # 不知道为啥...


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


# 获取课程列表，传入cookie userindex用于打印username      传出coursedata
def getclass(cookie):
    tempcoursedata = []
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
    index = 0
    for item in tempcoursedata:  # 打印课程
        print(str(index) + '.[用户]', username[userindex], "课程名称:" + item['name'])
        index += 1
    return tempcoursedata


# 监控，传入第X号用户的序号
def monitor():
    global a
    tempcoursedata = coursedata[userindex][0]
    nowusername = username[userindex]
    # 第i号课程
    for wait in range(len(monitor_list[userindex])):
        i = monitor_list[userindex][wait]
        if i == '':
            continue
        # 输入的是字符串，转int
        if isinstance(i, str):
            if i.isspace() == True:
                continue
            i = int(i)
        tempcourseid = tempcoursedata[i]['courseid']
        tempclassid = tempcoursedata[i]['classid']
        try:
            taskactivelist(tempcourseid, tempclassid, tempcoursedata[i]['name'], cookies[userindex], nowusername)
        except:
            print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '\t\t\ttaskactivelist error')
            writelog(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\t\t\ttaskactivelist error')
        '''
        #后台运注释掉打印部分代码
        else:
            print(
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '[监控运行中][用户]',username[userindex],
                '课程:', format(tempcoursedata[i]['name'],"<20"), '未查询到签到活动')
        '''
    if a == 0 or a == 1:
        a = 0
        print(
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '[监控运行中][用户]', nowusername, '未查询到签到活动')
        # else:
        # print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),"在7：30 - 12：00 and 14：30 - 18：00才监控")


def main():
    print("程序开始")
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), " 程序开始")
    getuser()
    global cookies, uid, userindex

    # 获取cookie uids
    for i in range(len(username)):
        tempcookie = login(username[i], passwd[i])
        cookies.append(tempcookie)
        uid = cookies[i]['UID']
        # 84529014

    # 获取每个人的课程列表coursedata
    for i in range(len(username)):
        userindex = i
        try:
            tempcoursedata = getclass(cookies[i])
            coursedata[i].append(tempcoursedata)
            # 选择要监控的课程
            print("请输入要监控的课程；监控全部请直接回车；排除模式请输入!后接排除列表：")
            w = []
            w = input()
            if w == '':
                monitor_list[i] = range(len(coursedata[i][0]))
            elif '!' in w or '！' in w:
                w = w.replace('！','').replace('!','')
                #print('排除'+ str(w).replace('!',''))
                w = [int(n) for n in w.split()]
                for each in range(len(coursedata[i][0])):
                    # 遍历0到len(coursedata[i][0])，如果each不在用户输入的排除列表里，就加入到monitor_list[i]
                    if each not in w:
                        monitor_list[i].append(each)
            print(monitor_list[i])
        except:
            writelog("user " + username[i] + " getclass error!")
    print('----------------------------------输入结束----------------------------------')
    # 死循环遍历每个人的课程,第i个人
    count = 0
    firstprint = 0
    while (1):
        # 时段内监控，防止老师炸鱼
        weekday = datetime.datetime.now().isoweekday()
        if (weekday == 6 or weekday == 7):
            print("周末不监控")
            time.sleep(7200)
            continue
        nowtime = datetime.datetime.now().strftime('%H:%M:%S')
        if (nowtime.__gt__("07:30:00") and nowtime.__lt__("22:00:00")):
            writelog(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\t\t\t' + str(count))
            count += 1
            # 遍历每个人
            for i in range(len(username)):
                try:
                    global a
                    userindex = i
                    a = 1
                    monitor()
                except:
                    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '\t\t\tmonitor error')
                    writelog(
                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + username[i] + '\t\t\tmonitor error')
                if i != len(username)-1:
                    print('')
            print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        else:
            if (firstprint == 0):
                print("在7：30-12：00和14：30到22：00才开始监控")
                firstprint = 1
        time.sleep(speed)  # 休眠时间在最上面设置


if __name__ == '__main__':
    main()
