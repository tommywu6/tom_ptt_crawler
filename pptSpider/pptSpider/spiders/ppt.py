# -*- coding: utf-8 -*-
import scrapy
import uuid
import requests
import csv
from bs4 import BeautifulSoup
from ..items import PptspiderItem
# from pptSpider.pptSpider.items import PptspiderItem


class PptSpider(scrapy.Spider):
    name = 'ppt'
    allowed_domains = ['www.ptt.cc']
    start_url = ['https://www.ptt.cc/bbs/hotboards.html']
    # start url to crawling

    def __init__(self):
        self.h_number = 0
        self.c_number = 0

    # define title and create csv file
    def start_requests(self):
        header = ['authorId', 'a_author', 'a_title', 'username', 'a_date', 'note', 'note_url', 'classname', 'category_pages', 'category_title', 'category_url']
        # with open ('ptt_result.csv','a',encoding='utf-8') as f:
        #     csv_write = csv.DictWriter(f, fieldnames=header ,delimiter = ';')
        #     csv_write.writeheader()
        #     f.close()
        for url in self.start_url:
            yield scrapy.Request(url, callback=self.home_page)
    # def parse(self, response):
    #     pass
    def note(self, response):
        item = PptspiderItem()
        item['authorId'] = response.meta['authorId']
        # item['username'] = meta['username']
        # item['classname'] = meta['classname']
        # item['category_pages'] = meta['category_pages']
        # item['category_title'] = meta['category_title']
        # item['category_url'] = meta['category_url']
        # item['a_title'] = meta['a_title']
        # item['a_author'] = meta['a_author']
        # item['a_date'] = meta['a_date']
        # item['note_url'] = meta['note_url']
        # item['note'] = meta['note']
        return item
    # def start_requests(self):
    #     header = ['authorId', 'a_author', 'a_title', 'username', 'a_date', 'note', 'note_url', 'classname', 'category_pages', 'category_title', 'category_url']
    #     with open ('ptt_result.csv','a',encoding='utf-8') as f:
    #         csv_write = csv.DictWriter(f, fieldnames=header ,delimiter = ';')
    #         csv_write.writeheader()
    #         f.close()
    #     for url in self.start_url:
    #         request_url = requests.get(url)
    #         self.home_page(request_url)
    # To fetch context data in category page
    def home_page(self, response):
        soup = BeautifulSoup(response.text,'lxml')
        posts1 = soup.find_all('a', class_= 'board')
        for p in posts1:
            self.h_number = self.h_number + 1
            authorId = uuid.uuid4()
            username = p.find('div', class_= 'board-name').text
            # print(username)
            category_pages = p.select('span')[0].text
            # print(category_pages)
            classname = p.select('div.board-class')[0].text
            # print(classname)
            category_title = p.select('div.board-title')[0].text
            # print(category_title)
            category_url = 'https://www.ptt.cc' + p['href']
            # print(self.h_number, ' : ' , category_url)
            request_url = requests.get(
                url = category_url,
                cookies = {'over18': 'yes'}  # age over 18
            )
            meta1 = {
                # "firstpage" : str(response.url),
                "authorId" : str(authorId),
                "username" : str(username),
                "classname" : str(classname),
                "category_pages" : str(category_pages),
                "category_title" : str(category_title),
                "category_url" : str(category_url)
            }
            self.category_page(request_url, meta1)
    # To get detail in category page
    def category_page(self, response, meta1):
            self.c_number = self.c_number + 1
            soup = BeautifulSoup(response.text,'lxml')
            r_ent = soup.select('div.r-ent')[0].text
            a_url = soup.select('div.title > a')[0]['href']
            a_title = soup.select('div.title')[0].text.replace('\n','').replace('\t','')
            if '刪除' in a_title:
                a_url = a_title
                note = a_title
            else :
                note = ''

            a_author = soup.select('div.author')[0].text
            # print(a_author)
            a_date = soup.select('div.date')[0].text
            # print(a_date)
            note_url = 'https://www.ptt.cc/' + a_url

            # print(a_title)
            # print(self.c_number , ' : ' ,'https://www.ptt.cc/' + a_url)
            meta2 = {
                "a_title" : str(a_title),
                "a_author" : str(a_author),
                "a_date" : str(a_date),
                "note_url" : str(note_url),
                "note" : str(note)
            }
            # To combine two metadata in dictionary
            all_metadata = dict(meta2.items() | meta1.items())
            request_url = requests.get(
                url = note_url,
                cookies = {'over18': 'yes'}  # age over 18
            )
            self.insert_data(request_url, all_metadata)
    # To process the data and insert to csv file
    def insert_data(self, response, all_metadata):
        soup = BeautifulSoup(response.text,'lxml')
        checkpage = soup.title.text
        # Error handeling
        if '404 Not Found' in checkpage:
            pass
        else: 
            all_metadata["note"] = soup.select('#main-content')[0].text.split('※ 發信站')[0].replace('\n',' ')
        # print(all_metadata)
        header = ['authorId', 'a_author', 'a_title', 'username', 'a_date', 'note', 'note_url', 'classname', 'category_pages', 'category_title', 'category_url']
        with open ('ptt_result.csv','a',encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header, delimiter = ';')
            all_metadata = {key: value for key, value in all_metadata.items()if key in header}
            writer.writerow(all_metadata)


# a = PptSpider()
# a.start_requests()