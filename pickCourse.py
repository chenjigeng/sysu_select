# -*- coding=utf-8 -*-

from PIL import Image
import requests
import hashlib
from bs4 import BeautifulSoup
import datetime
import time
import json
import html
import threading
import os

#自动帮你选专选课,无需手动操作，如果想要选公选/专必课/公必，去找到对应的教学班号，写在jxhbs里

jxbhs = ["16210060161001"] # 教学班号，自己去找对应的教学班号，手动修改在这里

class Student:
  #初始化
  def __init__(self, jxbhs):
    self.sid = input("请输入学号:")
    self.password = input("请输入密码:")
    self.jxbhs = jxbhs
    self.login()
    self.getCourses()

  #登陆教务系统
  def login(self):
    self.password = hashlib.md5(self.password.encode('utf-8')).hexdigest().upper()
    self.session = requests.Session()

    #先登录该网站获取cookie
    res = self.session.get("http://uems.sysu.edu.cn/elect/");

    #获取验证码
    res = self.session.get("http://uems.sysu.edu.cn/elect/login/code")
    with open('captcha.jpg', 'wb') as f:
      f.write(res.content)
      f.close()
        # 用pillow 的 Image 显示验证码
        # 如果没有安装 pillow 到源代码所在的目录去找到验证码然后手动输入
    try:
      im = Image.open('captcha.jpg')
      im.show()
      im.close()
    except:
      print(u'请到 %s 目录找到captcha.jpg 手动输入' % os.path.abspath('captcha.jpg'))
    self.j_code = input("请输入验证码(已经帮你打开图片了):")

    #登陆
    data = {
      "username": self.sid,
      "password": self.password,
      "j_code": self.j_code,
      "It": "",
      "_eventId": "submit",
      "gateway": "true"
    }

    res = self.session.post("http://uems.sysu.edu.cn/elect/login", data = data);
    if res.status_code == 200:
      self.sid = res.url[res.url.find("sid=")+4:]
    else:
      #登陆失败，退出程序
      print("账号或者密码错误,或者服务器改变了验证方式")
      os._exit(0)

  # 获取课程编号
  def getCourses(self):
    now = datetime.datetime.now()
    y = now.date().year
    m = now.date().month
    d = now.date().day
    xnd = 0
    xq = 0
    if m >= 6 and m <= 9:
      self.xnd = str(y)+"-"+str(y+1)
      self.xq = '1'
    elif m >= 1 and m <= 4:
      self.xq = '2'
      self.xnd = str(y-1)+"-"+str(y)
    url = "http://uems.sysu.edu.cn/elect/s/courses?kclb=21&xnd=" + self.xnd + "&xq=" + self.xq + "&fromSearch=false&sid=" + self.sid
    res = self.session.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    courses = soup.select("table#courses td a[jxbh]");
    self.courseIds = []
    for course in courses:
      courseId = course.get("jxbh")
      self.courseIds.append(courseId)
    self.courseIds.extend(self.jxbhs)
    
  #选择单个课程，用来创建线程，默认每隔两秒选一次，可手动修改
  def selectSingleCourse(self, courseId):
    result = True
    while result:
      res = self.session.get("http://uems.sysu.edu.cn/elect/s/courseDet?id=" + courseId + "&xnd=undefined&xq=undefined&sid=" + self.sid)
      soup = BeautifulSoup(res.text, 'html.parser')
      course = soup.find("td", class_="lab", text="课程名称：")
      course = course.find_next_sibling("td").text
      teacher = soup.find("td", class_="lab", text="任课教师：")
      teacher = teacher.find_next_sibling("td").text;
      data = {
        "jxbh": courseId,
        "sid": self.sid
      }
      print("正在选:" + course + " 任课老师是" + teacher)
      res = self.session.post("http://uems.sysu.edu.cn/elect/s/elect", data = data)
      soup = BeautifulSoup(res.text, 'html.parser')
      textarea = soup.find("textarea");
      content = textarea.text
      infoData = json.loads(content)
      if infoData['err']['code'] == 0:
        print ( "successfully select %s of %s" % (course, teacher))
        result = False
      elif infoData["err"]["caurse"]:
        print ( infoData["err"]["caurse"],'已从待选列表中去除')
        result = False
        
      # 通过这个来设置抢课间隔,默认为2秒
      time.sleep(2)

  #抢课函数
  def pickCourses(self):
    #创建多个线程，每一个线程负责抢一个课
    threads = []
    for i in self.courseIds:
      t1 = threading.Thread(target=self.selectSingleCourse, args=(i,))
      threads.append(t1)

    for t in threads:
      t.setDaemon(True)
      t.start() 

    # 保证父进程不被中止，不用join()的原因是，用了join之后你没办法手动结束
    while True:
        time.sleep(1000)

  #显示你已选上的课程
  def showCourses(self):
    url = "http://uems.sysu.edu.cn/elect/s/courseAll?xnd="+ self.xnd + "&xq=" + self.xq + "&sid=" + self.sid
    res = self.session.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    courses = soup.select("td a")
    print("已选课程如下:")
    for course in courses:
      print(course.text)

student = Student(jxbhs)
student.showCourses()
student.pickCourses()

