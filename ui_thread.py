# -*- coding: utf-8 -*-
"""
Created on Sun Sep  5 03:00:02 2021

@author: Admin
"""

# -*- coding: utf-8 -*-
"""
Created on Sun Sep  5 01:09:21 2021

@author: Admin
"""

from tkinter import *
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from urllib.parse import quote
import json,pickle,re,time,random,queue
from bs4 import BeautifulSoup
from threading import Thread
from tklog.tklog import *
import logging
from common import *
from web_thread import web_thread


class ui_thread(threading.Thread):
    def __init__(self,log_queue):
        self.log_queue=log_queue
        self.root=Tk()
        self.run_status=StringVar()
        self.run_status.set('待机')
        self.login_status=StringVar()
        self.login_status.set('未登录')
        self.input_word=StringVar()
        self.input_word.set('')
        self.key_word=''
        try:
            self.web=web_thread(self.log_queue)
            self.root.geometry('700x300')
            self.root.title('爬取程序')            
            self.root.protocol("WM_DELETE_WINDOW", self.quit0)
            
            panel_1=LabelFrame(self.root,padx=1,pady=1)
            
            #登录按钮
            Button(self.root,text='登录',command=self.login, width = 8).grid(row=0, column=0)
            #开始按钮
            self.run_button=Button(self.root,text='刷新',command=self.refresh, width = 8)
            self.run_button.grid(row=0, column=1)           
            Frame(self.root,width=20).grid(row=0, column=2,columnspan=1)
            # status_frame = LabelFrame(self.root)
            status_frame1 = LabelFrame(self.root)
            status_frame2 = LabelFrame(self.root)
            
            Label(status_frame1,text='运行状态:').pack(side=LEFT)             
            Label(status_frame1,textvariable=self.run_status).pack(side=RIGHT)            
            Label(status_frame2,text='登录状态:').pack(side=LEFT)                       
            Label(status_frame2,textvariable=self.login_status).pack(side=RIGHT)
            
            status_frame1.grid(row=0, column=3)
            status_frame2.grid(row=0, column=4)
            
            #日志插件初始化
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.DEBUG)
            fmt = logging.Formatter('%(asctime)s: %(message)s')
            tkhandler = tklogHandler(master=self.root,width = 60,height=14)
            tkhandler.grid(row=1, column=3,columnspan=4,rowspan=4)
            tkhandler.setFormatter(fmt)
            self.logger.addHandler(tkhandler)
            
            Label(self.root,text='关键词设置:').grid(row=1, column=0,columnspan=2)   
            Entry(self.root,width=20,textvariable=self.input_word).grid(row=2, column=0,columnspan=2)
            Button(self.root,text='确认',command=self.change_key_word, width = 8).grid(row=3, column=0,columnspan=1)
            Button(self.root,text='清空',command=self.clear_key_word, width = 8).grid(row=3, column=1,columnspan=1)
            Button(self.root,text='开始',command=self.start_spider, width = 8).grid(row=4, column=0,columnspan=1)
            # status_frame.pack(padx=1,pady=1,side=TOP)
            # status_frame1.pack(padx=1,pady=1,side=LEFT)
            # status_frame2.pack(padx=1,pady=1,side=LEFT)
            Thread.__init__(self)
        except FileNotFoundError as e:
            print(e)
            self.logger.debug(e)
            self.quit0()
        except Exception as e:
            print(e)
            self.logger.debug(e)
            self.quit0()

    def quit0(self):
        print('系统退出')
        if self.web is not None:
            self.web.quit0()
        self.root.destroy()      

    def run(self):
        try:
            self.root.mainloop()
        except FileNotFoundError as e:
            print(e)
            self.logger.debug(e)
            self.quit0()
        except Exception as e:
            print(e)
            self.logger.debug(e)
            self.quit0()
        
    def login(self):
        #self.dr.delete_all_cookies()
        self.dr.get(login_url)
        self.add_log('请手动登录，登录成功后在进行其他操作')
        
    #检查是否登录
    def check_login(self):
        page_source=self.dr.page_source
        bs = BeautifulSoup(page_source,"html.parser")
        flag=bs.find_all('div',class_='s-name')
        
        if len(flag) != 0:
            return True
        else:
            return False
        
    def refresh(self):        
        if self.check_login():
            self.add_log('登录成功')
            self.login_status.set('已登录')
        else:
            self.add_log('未登录，请先登录','warning')
            self.login_status.set('未登录')
        
    def change_key_word(self):
        self.key_word=self.input_word.get()
        self.add_log("关键词已变为："+self.key_word)
        
    def clear_key_word(self):
        self.input_word.set('')
     
    def get_url(self,num):
        url=shop_search_url.format(key_word=self.key_word)+'&s='+str((num-1)*20)
        return url
    
    def start_spider(self):
        if self.login_status.get() == '已登录':
            if self.run_status.get() == '待机':
                if self.key_word.strip() == '':
                    self.add_log('关键词为空，请设置关键词','warning')
                else:
                    self.run_status.set('运行中')
                    self.th_spider_core()
            else:
                self.add_log('未处于待机状态，不允许重新开始','warning')
        else:
            self.add_log('请先登录后，刷新，再点击开始','warning')
            


    #插入日志
    def add_log(self,msg='',tp='info'):
        self.log_queue.put(message(msg,tp))
    
    #打印日志
    def print_log(self):
        try:
            data=self.log_queue.get(block=False)
            msg=data.msg
            tp=data.type
            if tp=='info':
                self.logger.info(msg)
            elif tp=='debug':
                self.logger.debug(msg)
            elif tp=='warning':
                self.logger.warning(msg)
            else:
                self.logger.info(msg)
        except queue.Empty:
            pass
        
    def job_print_log(self):
        while True:
            self.print_log()
    
    def th_log(self):
        log_th=threading.Thread(target=self.job_print_log)
        log_th.start()

