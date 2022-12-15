import requests
import hashlib
import random
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



    def detect_vercode(self,manul):
        """识别验证码"""
        image = self.session.get(self.login_captcha).content
        if manul:
            print("启动手动识别验证码")
            with open("ver_code.jpg", 'wb') as f:
                f.write(image)
            img = Image.open("ver_code.jpg")
            img.save('ver_code.jpg')
            res = input("请输入验证码：")

        else:
            ocr = DdddOcr()
            res = ocr.classification(image)
        return res


    def login(self,manul:bool):
        """
        :param manul:  如果manul =True 则开启手动识别验证码
        """
        try:
            username, passwd= user_config["username"], user_config["password"]
        except:
            print("读取学号和密码失败")
        else:
            print("读取学号和密码成功")
        ver_code = self.detect_vercode(manul)
        passwd =  hashlib.md5(passwd.encode(encoding='utf-8')).hexdigest()
        status_code = self.post_data(username,passwd,ver_code)

        if status_code==200:
            response = self.session.get(self.get_user_url)
            data = BeautifulSoup(response.content, 'lxml')
            user = data.find('span', attrs={"class": "user-info"}).text.split()[-1]

            self.user = user
            print("成功登录SCU教务系统")
            print(f"欢迎你:  {user}")
        else:
            raise RuntimeError("账号或密码错误")

    def post_data(self,username, passwd, ver_code):
        login_response = self.session.get(self.login_url)
        data = BeautifulSoup(login_response.content, 'lxml')
        token_value = data.find('input',attrs={'id':"tokenValue"})['value']
        data = {
            "tokenValue": token_value,
            'j_username': username,
            'j_password': passwd,
            'j_captcha': ver_code,
            '_spring_security_remember_me': 'on'
        }
        response = self.session.post(self.post_url, data=data, headers=self.headers)

        if response.text.find('忘记密码') != -1:
           return 404
        elif response.text.find('验证码错误') != -1:
            print("验证码自动识别错误，正在进行重试")
            ver_code = self.detect_vercode(manul=False)
            self.post_data(ver_code)
        if response.text.find('忘记密码') == -1:
            print("验证码识别成功")
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
        df.to_excel(path+"/original.xls",sheet_name="courses")
        df = df [["kcm","zcsm","xqm","jxlm","jash","kkxsh","jsm","xf","kslxmc","kkxsm","id.kxh","id.kch","id.skxq","id.skjc"]] # 只保留 课程名 教学周数 校区名 教学楼名 教室号 开课学院代码 任课老师名 学分 考察方式 开课学院名 课程号 课序号 上课星期 起始小节
        df.columns= ["课程名","教学周数"," 校区名" ,"教学楼名","教室号","开课学院代码","任课老师名"," 学分","考察方式 ","开课学院名"," 课程号","课序号","上课星期","起始小节"]
        df.to_excel(path+"/final.xls",sheet_name="course")
        print("数据处理成功")
        print(df)

    def crawl(self,path,manul=False):
        self.login(manul)
        self.save_file(data=self.crawl_course(),path=path)






