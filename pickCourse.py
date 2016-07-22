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

#自动帮你选专选课，如果想要选公选/专必课/公必，去找到对应的教学班号，写在jxhbs里

sid = "1433xxxx" #学号
password = "xxxxxxxx" #密码
jxbhs = ["16210060161001"] # 教学班号，自己去找对应的教学班号，手动修改在这里
password = hashlib.md5(password.encode('utf-8')).hexdigest().upper()
session = requests.Session()

#先登录该网站获取cookie
res = session.get("http://uems.sysu.edu.cn/elect/");

#获取验证码
res = session.get("http://uems.sysu.edu.cn/elect/login/code")
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
j_code = input("please input the captcha\n>")

#登陆
data = {
  "username": sid,
  "password": password,
  "j_code": j_code,
  "It": "",
  "_eventId": "submit",
  "gateway": "true"
}
res = session.post("http://uems.sysu.edu.cn/elect/login", data = data);
if res.status_code == 200:
  sid = res.url[res.url.find("sid=")+4:]
else:
  pass

# 获取课程编号
now = datetime.datetime.now()
y = now.date().year
m = now.date().month
d = now.date().day
xnd = 0
xq = 0
if m >= 6 and m <= 9:
  xnd = str(y)+"-"+str(y+1)
  xq = '1'
elif m >= 1 and m <= 4:
  xq = '2'
  xnd = str(y-1)+"-"+str(y)
url = "http://uems.sysu.edu.cn/elect/s/courses?kclb=21&xnd=" + xnd + "&xq=" + xq + "&fromSearch=false&sid=" + sid
res = session.get(url)
soup = BeautifulSoup(res.text, 'html.parser')
courses = soup.select("table#courses td a[jxbh]");
courseIds = []
for course in courses:
  courseId = course.get("jxbh")
  courseIds.append(courseId)


courseIds.extend(jxbhs)

# 获取课程信息
# for i in courseIds:
#   res = session.get("http://uems.sysu.edu.cn/elect/s/courseDet?id=" + i + "&xnd=undefined&xq=undefined&sid=" + sid)
#   soup = BeautifulSoup(res.text, 'html.parser')
#   course = soup.find("td", class_="lab", text="课程名称：")
#   course = course.find_next_sibling("td").text
#   teacher = soup.find("td", class_="lab", text="任课教师：")
#   teacher = teacher.find_next_sibling("td").text;
#   print(course + "任课老师:" + teacher);

#选课，每隔两秒选一次
print(courseIds)
def selectSingleCourse(courseId):
  result = True
  while result:
    res = session.get("http://uems.sysu.edu.cn/elect/s/courseDet?id=" + courseId + "&xnd=undefined&xq=undefined&sid=" + sid)
    soup = BeautifulSoup(res.text, 'html.parser')
    course = soup.find("td", class_="lab", text="课程名称：")
    course = course.find_next_sibling("td").text
    teacher = soup.find("td", class_="lab", text="任课教师：")
    teacher = teacher.find_next_sibling("td").text;
    data = {
      "jxbh": courseId,
      "sid": sid
    }
    print("正在选:" + course + " 任课老师是" + teacher)
    res = session.post("http://uems.sysu.edu.cn/elect/s/elect", data = data)
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
    time.sleep(2)
threads = []
for i in courseIds:
  t1 = threading.Thread(target=selectSingleCourse, args=(i,))
  threads.append(t1)

for t in threads:
  t.setDaemon(True)
  t.start() 

while True:
    time.sleep(2)
# while courseIds:
#   print("正在选课\n")
#   for i in courseIds:
#     res = session.get("http://uems.sysu.edu.cn/elect/s/courseDet?id=" + i + "&xnd=undefined&xq=undefined&sid=" + sid)
#     soup = BeautifulSoup(res.text, 'html.parser')
#     course = soup.find("td", class_="lab", text="课程名称：")
#     course = course.find_next_sibling("td").text
#     teacher = soup.find("td", class_="lab", text="任课教师：")
#     teacher = teacher.find_next_sibling("td").text;
#     data = {
#       "jxbh": i,
#       "sid": sid
#     }
#     res = session.post("http://uems.sysu.edu.cn/elect/s/elect", data = data)
#     soup = BeautifulSoup(res.text, 'html.parser')
#     textarea = soup.find("textarea");
#     content = textarea.text
#     # txt = html.unescape(res.content.decode("utf-8"))
#     # txt = txt.find("<textareax")
#     infoData = json.loads(content)
#     if infoData['err']['code'] == 0:
#       print ( "successfully select %s of %s" % (course, teacher))
#       courseIds.remove(i)
#     elif infoData["err"]["caurse"]:
#       print ( infoData["err"]["caurse"],'已从待选列表中去除')
#       courseIds.remove(i)
  # #每隔一秒选一次，可以自定义设置
  # time.sleep(1)

