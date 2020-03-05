#!/usr/bin/python3
import pymongo
import requests
import csv
import uuid
# 計時器相關套件
import time
import datetime as dt
import smtplib
from email.mime.text import MIMEText
from bs4 import BeautifulSoup

# To set up smtp service
GMAILUSER = 'XXXXX@gmail.com' 
GMAILPWD = 'XXXXX'
RECEIVE_EMAIL_USER = 'ANY_EMAIL'
SLEEPTIME = 60  # 每輪搜尋休眠時間
flog = False  # 判斷是否已尋找到目標用的
t = dt.datetime  # Display time

# create mongodb connection
conn = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = conn["IT_db"]
mycol = mydb["IT_coll"]
collection = conn.mydb
# test if connection success
collection.stats  # connection mongodb status


class ppt_spider():
    # start url to crawling
    start_url = ['https://www.ptt.cc/bbs/hotboards.html']

    def __init__(self):
        self.h_number = 0
        self.c_number = 0

    # define title and create csv file
    def start_requests(self):
        header = ['authorId', 'authorName', 'title', 'publishedTime', 'content', 'board_name',
                  'canonicalUrl', 'classname', 'category_pages', 'category_title', 'category_url']
        with open('ptt_result.csv', 'a', encoding='utf-8') as f:
            csv_write = csv.DictWriter(f, fieldnames=header, delimiter=';')
            csv_write.writeheader()
            f.close()
        print('Start crawling target Url', self.start_url)
        for url in self.start_url:
            request_url = requests.get(url)
            self.home_page(request_url)
        print('Crawling has finish')

    # To fetch context data in category page
    def home_page(self, response):
        soup = BeautifulSoup(response.text, 'lxml')
        posts1 = soup.find_all('a', class_='board')
        for p in posts1:
            self.h_number = self.h_number + 1
            authorId = uuid.uuid4()
            board_name = p.find('div', class_='board-name').text
            category_pages = p.select('span')[0].text
            classname = p.select('div.board-class')[0].text
            category_title = p.select('div.board-title')[0].text
            category_url = 'https://www.ptt.cc' + p['href']
            request_url = requests.get(
                url=category_url,
                cookies={'over18': 'yes'}  # age over 18
            )
            meta1 = {
                "authorId": str(authorId),
                "board_name": str(board_name),
                "classname": str(classname),
                "category_pages": str(category_pages),
                "category_title": str(category_title),
                "category_url": str(category_url)
            }
            self.category_page(request_url, meta1)

    # To get detail in category page
    def category_page(self, response, meta1):
        self.c_number = self.c_number + 1
        soup = BeautifulSoup(response.text, 'lxml')
        r_ent = soup.select('div.r-ent')[0].text
        a_url = soup.select('div.title > a')[0]['href']
        a_title = soup.select('div.title')[0].text.replace(
            '\n', '').replace('\t', '')
        if '刪除' in a_title:
            a_url = a_title
            note = a_title
        else:
            note = ''

        a_author = soup.select('div.author')[0].text
        a_date = soup.select('div.date')[0].text
        canonicalUrl = 'https://www.ptt.cc/' + a_url
        meta2 = {
            "title": str(a_title),
            "authorName": str(a_author),
            "publishedTime": str(a_date),
            "canonicalUrl": str(canonicalUrl),
            "content": str(note)
        }
        # To combine two metadata in dictionary
        all_metadata = dict(meta2.items() | meta1.items())
        request_url = requests.get(
            url=canonicalUrl,
            cookies={'over18': 'yes'}  # age over 18
        )
        self.insert_data(request_url, all_metadata)
    # To process the data and insert to csv file

    def insert_data(self, response, all_metadata):
        soup = BeautifulSoup(response.text, 'lxml')
        checkpage = soup.title.text
        # Error handeling
        if '404 Not Found' in checkpage:
            pass
        else:
            all_metadata["content"] = soup.select(
                '#main-content')[0].text.split('※ 發信站')[0].replace('\n', ' ')
        # print(all_metadata)
        header = ['authorId', 'authorName', 'title', 'publishedTime', 'content', 'board_name',
                  'canonicalUrl', 'classname', 'category_pages', 'category_title', 'category_url']
        with open('ptt_result.csv', 'a', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header, delimiter=';')
            all_metadata = {key: value for key,
                            value in all_metadata.items()if key in header}
            writer.writerow(all_metadata)
        # Store all metadata in mongodb
        try:
            if all_metadata:
                mydict = all_metadata
                mycol.insert_one(mydict)
        except Exception as e:
            # Sending email to notify user
            send_mail_for_me(e)
            print('[%s] Email has been sent!!' %t.now())
            print('[%s] Error insert to mongodb：%s' % (t.now(), e))

# SMTP Service 
# Send by Gmail
# Please fill you gmail user and password, also the receive user email.
def send_mail_for_me(meta):
    'Using Gmail to sent the email'
    send_gmail_user = GMAILUSER
    send_gmail_password = GMAILPWD
    rece_gmail_user = RECEIVE_EMAIL_USER

    msg = MIMEText('Error insert to mongodb：' + str(meta))
    msg['Subject'] = 'Crawler has issues, help ~~~'
    msg['From'] = send_gmail_user
    msg['To'] = rece_gmail_user

    # Using SSL encypt to connect to gmail smtp
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(send_gmail_user, send_gmail_password)
    server.send_message(msg)
    server.quit()

ppt_spider().start_requests()
