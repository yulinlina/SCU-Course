from crawlscu import Spider
import argparse



if __name__ =="__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-m", "--manual",action="store_true", default=False, help="开启手动输入验证码")
    parser.add_argument("-p", "--path", default="results", help="指定保存路径")
    spider = Spider()
    args = parser.parse_args()
    path = args.path
    if args.manual:
        print("开启手动识别验证码")
        spider.crawl(manul=True,path=path)
    else:
        spider.crawl(manul=False,path=path)
