# -*- coding: utf-8 -*-
# @File  : shancheng.py
# @Author: LaoJu
# @Date  : 2019/3/1
# @Desc  :

import requests
import re
import smtplib
import time
from email.mime.text import MIMEText
from urllib import parse
from scrapy.selector import Selector

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
}


def crawl_activities():
    # 1.获取网页（第一页）
    response = requests.get("http://www.sczyz.org/hd/", headers=headers)
    response.encoding = 'gbk'
    re_str = Selector(text=response.text)

    # 查看页码
    page_str = re_str.css("#home_dh1 .disabled::text").extract_first()
    page_result = re.match("\d+\/?(\d+)", page_str)
    page = int(page_result.group(1))

    # 爬取所有页码的页面
    for i in range(page):

        response = requests.get("http://www.sczyz.org/hd/?page={0}".format(i + 1), headers=headers)
        response.encoding = 'gbk'
        re_str = Selector(text=response.text)

        # 2.查找需要的活动 献血/少儿图书馆/科技馆/
        all_activities = re_str.css(".jcarousel-skin-cp a")
        for item in all_activities:
            name = item.css(".hd::text").extract()[0]
            # TODO
            result = re.match("(.*献血.*)|(.*少儿图书馆.*)|(.*科技馆.*)|(.*办公室义工.*)", name)
            # result = re.match("(.*植树.*)", name)
            if result:
                # 获取活动url
                print("活动名: " + name)
                item_url = item.css("a::attr(href)").extract()[0]
                item_url = parse.urljoin(response.url, item_url)
                print("活动url: " + item_url)
                crawl_detail(item_url)


def crawl_detail(item_url):
    # 获取网页
    item_response = requests.get(item_url, headers=headers)
    item_response.encoding = 'gbk'
    re_str = Selector(text=item_response.text)

    # 获取报名信息
    lingxi_url = re_str.css("#js-lingxi-activity-iframe::attr(src)").extract_first()
    print("报名信息url: " + lingxi_url)
    lingxi_response = requests.get(lingxi_url, headers=headers)
    lingxi_text = Selector(text=lingxi_response.text)

    # 3.分析是否已报名/报名人数是否有空缺
    count = lingxi_text.css("span#signupsCount::text").extract()

    # 获取总名额数
    count_all = int(re_str.css(".n_18::text").extract()[1])

    # 如果没有signupsCount 则已报名人数为0
    if not count:
        count_num = 0
    else:
        result = re.match(".*?(\d+)\s{1}\/\s{1}?(\d+)", count[1].split("\n")[1])
        count_num = int(result.group(1))  # 已报名人数

    # TODO 待修改
    if count_num < count_all:  # 若还有名额 查看是否已经报名

        if count_num > 0: #报名人数大于0 查看是否已经报名
            # TODO list的str格式 需要去\n和空格
            sign_list = lingxi_text.css(".signups .signups-name::text").extract()
            new_sign_list = []
            for i in sign_list:
                i=i.replace(" ", "")  # 去除空格
                i=i.replace("\n","")  # 去除换行
                new_sign_list.append(i)

            if '陈红橘' not in new_sign_list:

                # 4.如果还没报名，发送邮件通知
                # 完善需要发送的信息
                msg = get_msg(re_str)
                # 剩余名额
                remain_nums = str(count_all - count_num)
                msg=msg+ "剩余名额: " + remain_nums + "\n" + "报名地址: " + item_url
                send_email(msg)

        elif count_num == 0:#如果报名人数等于0 则直接发送邮件通知报名
            msg = get_msg(re_str)
            # 剩余名额
            remain_nums = str(count_all - count_num)
            msg = msg + "剩余名额: " + remain_nums + "\n" + "报名地址: " + item_url
            send_email(msg)

def get_msg(re_str):

    # 活动名称
    activity_name = re_str.css("#n_17::text").extract_first()
    # 服务期间
    server_long = re_str.css("#n_12::text").extract()[0]
    # 服务日期
    server_date = re_str.css("#n_12::text").extract()[1]
    # 服务时间
    server_time = re_str.css("#n_12::text").extract()[2]
    # 服务地点
    server_address = re_str.css("#n_12::text").extract()[3]
    # 服务目的
    server_purpose = re_str.css("#n_12::text").extract()[4]
    # 服务职责
    server_duty = re_str.css("#n_12::text").extract()[5]

    # 拼接msg信息
    msg = "活动名称:" + activity_name + "\n" + server_long + "\n" + server_date + "\n" + server_time + "\n" + server_address + "\n" + server_purpose + "\n" + server_duty + "\n"
    return msg


def send_email(msg):
    # 设置服务器所需信息
    # 163邮箱服务器地址
    mail_host = 'smtp.163.com'
    # 163用户名
    mail_user = '150xxxx8104'
    # 密码(部分邮箱为授权码)
    mail_pass = 'xxxx'
    # 邮件发送方邮箱地址
    sender = '150xxxx8104@163.com'
    # 邮件接受方邮箱地址，注意需要[]包裹，这意味着你可以写多个邮件地址群发
    receivers = ['xxxxxx@qq.com']

    # 设置email信息
    # 邮件内容设置
    message = MIMEText(msg, 'plain', 'utf-8')
    # 邮件主题
    message['Subject'] = '[山城志愿活动名额更新]'
    # 发送方信息
    message['From'] = sender
    # 接受方信息
    message['To'] = receivers[0]

    # 登录并发送邮件
    try:
        smtpObj = smtplib.SMTP_SSL(mail_host, 465)
        # 连接到服务器

        # # 假如不是阿里的话
        # # server = smtplib.SMTP(smtp_server, 25)
        # server.login(from_addr, password)
        # server.sendmail(from_addr, [to_addr], msg.as_string())
        # server.quit()

        # 登录到服务器
        smtpObj.login(mail_user, mail_pass)
        # 发送
        # 避免多个活动有名额一起发送时被认为是垃圾邮件
        time.sleep(15)
        smtpObj.sendmail(
            sender, receivers, message.as_string())
        # 退出
        smtpObj.quit()
        print('success')
    except smtplib.SMTPException as e:
        print('error', e)  # 打印错误


if __name__ == '__main__':
    crawl_activities()
