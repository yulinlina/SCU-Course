import requests
import hashlib
import random
import  os
from pandas.io.json import json_normalize
from bs4 import BeautifulSoup


from PIL import Image
from ddddocr import DdddOcr
from setting import user_config,user_agent_list

class Spider(object):
    def __init__(self):
        self.headers = {
            'User-Agent': random.choice(user_agent_list),
            'Host': '202.115.47.141'
        }
        self.session = requests.Session()

        self.login_captcha = 'http://202.115.47.141/img/captcha.jpg'                         # 验证码url
        self.login_url = 'http://202.115.47.141/login'                                       # 登录界面url
        self.post_url ='http://202.115.47.141/j_spring_security_check'                       # 登录检查url

        self.get_user_url = 'http://202.115.47.141/index.jsp'                                # 主界面
        self.course_url = "http://202.115.47.141/student/teachingResources/classCurriculum/searchCurriculumInfo/callback?planCode=2022-2023-1-1&classCode=203040701"            # 班级课表界面

    def detect_vercode(self, manul):
        """识别验证码"""
        image = self.session.get(self.login_captcha).content  # 向验证码页面发送请求
        if manul:  # 如果manul =True 手动识别
            print("启动手动识别验证码")
            with open("ver_code.jpg", 'wb') as f:  # 将拿到的image保存在本地
                f.write(image)
                img = Image.open("ver_code.jpg")
                img.save('ver_code.jpg')
                res = input("请输入验证码：")  # 手动输入验证码
        else:       # 如果manul=False 自动识别
            ocr = DdddOcr()
            res = ocr.classification(image)
        return res


    def login(self,manul:bool):
            """
              :param manul:  如果manul =True 则开启手动识别验证码
            """
            username, passwd = user_config["username"], user_config["password"]  # 从配置文件读取账号和密码
            ver_code = self.detect_vercode(manul)                                  # 自动识别验证码
            passwd = hashlib.md5(passwd.encode(encoding='utf-8')).hexdigest()       # 加密密码传输
            status_code = self.post_data(username, passwd, ver_code)                # 发送post请求

            if status_code == 200:
                """如果成功登录，则向首页发送get拿到账户信息"""
                response = self.session.get(self.get_user_url)
                data = BeautifulSoup(response.content, 'lxml')
                user = data.find('span', attrs={"class": "user-info"}).text.split()[-1]

                self.user = user
                print("成功登录SCU教务系统")
                print(f"欢迎你:  {user}")
            else:
                raise RuntimeError("账号或密码错误")

    def post_data(self,username, passwd, ver_code):
        login_response = self.session.get(self.login_url)                     # 向login页发送get请求
        data = BeautifulSoup(login_response.content, 'lxml')                  # 解析页面
        token_value = data.find('input',attrs={'id':"tokenValue"})['value']  # 找到对应的tokenvalue
        data = {
            "tokenValue": token_value,
            'j_username': username,
            'j_password': passwd,
            'j_captcha': ver_code,
            '_spring_security_remember_me': 'on'
        }
        response = self.session.post(self.post_url, data=data, headers=self.headers) # 向对应网址发送post请求
        if response.text.find('忘记密码') != -1:                           # 如果仍然在登录页则密码错误
             return 404
        elif response.text.find('验证码错误') != -1:						# 如果验证码自动识别错误则自动进行重试
            print("验证码自动识别错误，正在进行重试")
            ver_code = self.detect_vercode(manul=False)
            self.post_data(ver_code)
        if response.text.find('忘记密码') == -1:                      # 登录成功
            print("自动验证码识别成功")
            return 200  # OK

    def crawl_course(self):

        response = self.session.get(self.course_url)
        if response.status_code==200:
            print("爬取成功，正在处理数据")

        return response.json()[0] # 返回值外面套了个列表所以把它们取出来

    def save_file(self,data,path):
        """保存到给定路径
        data 是一个json 数据格式
        保存为xls文件
        """
        df=json_normalize(data)
        if not os.path.isdir(path):
            os.mkdir(path)
        df.to_excel(path+"/original.xls",sheet_name="courses")
        df = df [["kcm","zcsm","xqm","jxlm","jash","kkxsh","jsm","xf","kslxmc","kkxsm","id.kxh","id.kch","id.skxq","id.skjc"]] # 只保留 课程名 教学周数 校区名 教学楼名 教室号 开课学院代码 任课老师名 学分 考察方式 开课学院名 课程号 课序号 上课星期 起始小节
        df.columns= ["课程名","教学周数"," 校区名" ,"教学楼名","教室号","开课学院代码","任课老师名"," 学分","考察方式 ","开课学院名"," 课程号","课序号","上课星期","起始小节"]
        df.to_excel(path+"/final.xls",sheet_name="course")
        print("数据处理成功")
        print(df)

    def crawl(self,path,manul=False):
        self.login(manul)
        self.save_file(data=self.crawl_course(),path=path)






