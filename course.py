# coding=utf-8
from selenium import webdriver
import selenium
import requests
import hashlib
from PIL import Image, ImageEnhance, ImageDraw
import json
import re
from time import sleep


class RClient(object):

    def __init__(self, username, password, soft_id, soft_key):
        self.username = username
        m = hashlib.md5()
        m.update(password.encode("utf8"))
        self.password = m.hexdigest()
        self.soft_id = soft_id
        self.soft_key = soft_key
        self.base_params = {
            'username': self.username,
            'password': self.password,
            'softid': self.soft_id,
            'softkey': self.soft_key,
        }
        self.headers = {
            'Connection': 'Keep-Alive',
            'Expect': '100-continue',
            'User-Agent': 'ben',
        }

    def rk_create(self, im, im_type, timeout=60):
        """
        im: 图片字节
        im_type: 题目类型
        """
        params = {
            'typeid': im_type,
            'timeout': timeout,
        }
        params.update(self.base_params)
        files = {'image': ('a.jpg', im)}
        r = requests.post('http://api.ruokuai.com/create.json', data=params, files=files, headers=self.headers)
        return r.json()

    def rk_report_error(self, im_id):
        """
        im_id:报错题目的ID
        """
        params = {
            'id': im_id,
        }
        params.update(self.base_params)
        r = requests.post('http://api.ruokuai.com/reporterror.json', data=params, headers=self.headers)
        return r.json()


def get_pixel(image, x, y, G, N):
    L = image.getpixel((x, y))
    if L > G:
        L = True
    else:
        L = False

    near_dots = 0
    if L == (image.getpixel((x - 1, y - 1)) > G):
        near_dots += 1
    if L == (image.getpixel((x - 1, y)) > G):
        near_dots += 1
    if L == (image.getpixel((x - 1, y + 1)) > G):
        near_dots += 1
    if L == (image.getpixel((x, y - 1)) > G):
        near_dots += 1
    if L == (image.getpixel((x, y + 1)) > G):
        near_dots += 1
    if L == (image.getpixel((x + 1, y - 1)) > G):
        near_dots += 1
    if L == (image.getpixel((x + 1, y)) > G):
        near_dots += 1
    if L == (image.getpixel((x + 1, y + 1)) > G):
        near_dots += 1

    if near_dots < N:
        return image.getpixel((x, y - 1))
    else:
        return None


def clear_noise(image, G, N, Z):
    draw = ImageDraw.Draw(image)

    for i in range(0, Z):
        for x in range(1, image.size[0] - 1):
            for y in range(1, image.size[1] - 1):
                color = get_pixel(image, x, y, G, N)
                if color is not None:
                    draw.point((x, y), "white")


driver = webdriver.Chrome()

conf = json.load(open('./self_conf.json'))

login_url = 'http://credit2.stu.edu.cn/portal/stulogin.aspx'
beixuanke_url = 'http://credit2.stu.edu.cn/Elective/beixuankecheng.aspx'

# 登录帐号
txtUserID = conf['username']
txtUserPwd = conf['password']

driver.get(login_url)
driver.find_element_by_xpath('//*[@id="txtUserID"]').send_keys(txtUserID)
driver.find_element_by_xpath('//*[@id="txtUserPwd"]').send_keys(txtUserPwd)
driver.find_element_by_xpath('//*[@id="btnLogon"]').click()

# 选择课程页面
driver.get(beixuanke_url)

# 选择课程类型
if conf['type'] == 1:
    if conf['option'] == 1:
        driver.find_element_by_xpath('//*[@id="ctl00_cpNav_btnQuery"]').click()
    else:
        driver.find_element_by_xpath('//*[@id="ctl00_cpNav_ddlDept"]/option[' + str(conf['option']) + ']').click()
else:
    if conf['option'] == 1:
        driver.find_element_by_xpath('//*[@id="ctl00_cpNav_btnSearch"]').click()
    else:
        driver.find_element_by_xpath('//*[@id="ctl00_cpNav_ddltype"]/option[' + str(conf['option']) + ']').click()

courses = driver.find_elements_by_xpath('//*[@id="ctl00_cpContent_gvKecheng"]/tbody/tr/td[2]/a')

# 寻找课程
course_index = 2
course_button = ''
for i in range(0, len(courses)):
    print(courses[i].text)
    if courses[i].text == str(conf['courseID']):
        course_index = i + 2
        break
if len(str(course_index)) == 1:
    course_button = '0' + str(course_index)
else:
    course_button = str(course_index)

# 判断课程是否有空余
p_number = driver.find_element_by_xpath('//*[@id="ctl00_cpContent_gvKecheng"]/tbody/tr[' + str(course_index)
                                        + ']/td[7]').text
# print(p_number)
p_current = re.search('(.+)/(.+)', p_number).group(1)
p_max = re.search('(.+)/(.+)', p_number).group(2)
while int(p_current) == int(p_max):
    sleep(1)
    driver.refresh()
    p_number = driver.find_element_by_xpath('//*[@id="ctl00_cpContent_gvKecheng"]/tbody/tr[' + str(course_index)
                                            + ']/td[7]').text
    print(p_number)
    p_current = re.search('(.+)/(.+)', p_number).group(1)
    p_max = re.search('(.+)/(.+)', p_number).group(2)

# 点击选课
driver.find_element_by_xpath('//*[@id="ctl00_cpContent_gvKecheng_ctl' + course_button + '_ImageButton1"]').click()

# 获取窗口句柄
currents = driver.window_handles
while len(currents) == 1:
    currents = driver.window_handles

# 切换至弹窗
driver.switch_to.window(currents[1])

# 判断是否有验证码
try:
    msg = driver.find_element_by_xpath('//*[@id="ctl00_cpContent_lblMsg"]')
    print(msg.text)
    driver.find_element_by_xpath('//*[@id="ctl00_cpContent_btnOK"]').click()
except selenium.common.exceptions.NoSuchElementException:
    # 截图或验证码图片保存地址
    raw_screenImg = "./image/raw_screenImg.png"
    code_Img = './image/code_Img.png'

    # 浏览器页面截屏
    driver.get_screenshot_as_file(raw_screenImg)

    # 定位验证码位置及大小
    location = driver.find_element_by_xpath('//*[@id="aspnetForm"]/div[3]/div[1]/div/div[2]/center/div/img').location
    size = driver.find_element_by_xpath('//*[@id="aspnetForm"]/div[3]/div[1]/div/div[2]/center/div/img').size
    left = location['x'] + 25
    top = location['y'] + 30
    right = location['x'] + size['width'] + 80
    bottom = location['y'] + size['height'] + 40

    # 从文件读取截图，截取验证码位置再次保存
    img = Image.open(raw_screenImg).crop((left, top, right, bottom))
    img = ImageEnhance.Contrast(img)
    img = img.enhance(2.0)
    img.save(code_Img)

    # 对图片进行降噪处理
    img2 = Image.open("./image/code_Img.png")
    img2 = img2.convert("L")
    clear_noise(img2, 50, 4, 4)
    img2.save("./image/result.png")

    # 连接若快api进行验证码识别
    username = conf['rk_username']
    password = conf['rk_password']
    soft_id = conf['soft_id']
    soft_key = conf['soft_key']
    rc = RClient(username, password, soft_id, soft_key)
    im = open('./image/result.png', 'rb').read()
    json = rc.rk_create(im, 3050)
    result = json["Result"]

    # 发送验证码
    driver.find_element_by_xpath('//*[@id="ctl00_cpContent_txtCapcha"]').send_keys(result)
    driver.find_element_by_xpath('//*[@id="ctl00_cpContent_btnContinue"]').click()
