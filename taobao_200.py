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
import json,pickle,re,time,random,threading,queue
from bs4 import BeautifulSoup

from tklog.tklog import *
import logging
from common import *


class tb_spider(object):
    status_list=['待机','运行中']
    lg_status_list=['未登录','已登录']
        
    def __init__(self):
        self.root=Tk()
        self.run_status=StringVar()
        self.run_status.set('待机')
        self.login_status=StringVar()
        self.login_status.set('未登录')
        self.input_word=StringVar()
        self.input_word.set('')
        self.key_word=''
        self.log_queue=queue.Queue()
        
        try:
            self.root.after(100,self.listen_for_result)
            #self.th_print_log()
            self.init_ui()
            self.dr=webdriver.Edge('./msedgedriver.exe')
            self.wait=WebDriverWait(self.dr, 5, 0.5)
            #self.root.mainloop()
        except FileNotFoundError as e:
            print(e)
            self.logger.debug(e)
            self.quit0()
        except Exception as e:
            print(e)
            self.logger.debug(e)
            self.quit0()
    
    def init_ui(self):
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

    def quit0(self):
        print('系统退出')
        if self.dr is not None:
            self.dr.quit()
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
        
    def spider_core(self):
        aa=0
        tb_rank_list=[]
        tm_rank_list=[]
        all_list=[]
        try:
            self.add_log('开始本次爬虫')
            key_url=shop_search_url.format(key_word=self.key_word)
            self.dr.get(key_url)
            e_input =self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.input.J_Input")))
            e_button = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.btn.J_Submit")))
            #page_source = self.dr.find_element_by_xpath("//*").get_attribute("outerHTML")
            page_source=self.dr.page_source
            page_json=get_json(page_source)
            pager=page_json['mods']['pager']['data']
            totalPage=pager['totalPage']
            key_count=0
            page_count=0
            val=[500,4000,10000]
            for i in range(totalPage,0,-1):
                # if page_count>6:
                #     break
                do_sleep()
                e_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.input.J_Input")))
                e_button = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.btn.J_Submit")))
                e_input.clear()
                e_input.send_keys(i)
                #e_button.click()
                self.dr.get(self.get_url(i))
                self.wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'span.current'),str(i)))
                # for j in val:           
                #     js="var q=document.documentElement.scrollTop={}".format(j)
                #     st=random.randint(5,10)*0.1
                #     time.sleep(st)
                #     self.dr.execute_script(js)
                page_source=self.dr.page_source
                shop_data=get_json(page_source)
                shopItems=shop_data['mods']['shoplist']['data']['shopItems']
                rank_count=0
                for shopItem in shopItems:
                    rank_res=check_rank(shopItem)
                    all_list.append(rank_res)
                    if rank_res['rank']>0:
                        if rank_res['type']=='淘宝':
                            tb_rank_list.append(rank_res)
                        rank_count+=1
                if rank_count==0:
                    key_count+=1
                else:
                    key_count=0
                    
                page_count+=1
                self.add_log('已抓取{}页'.format(page_count))
                if page_count%10==0:
                    long_sleep()
                if key_count>=3:
                    self.add_log('连续三页未抓取到有用信息，自动退出本次爬虫')
                    break
        except TimeoutException:
            self.add_log("连接超时，请检查网络",'warning')
        finally:
            file_name='淘宝_'+self.key_word.replace(' ', '_')+'.txt'
            with open('./爬取结果/'+file_name,'w') as f:
                for it in tb_rank_list:
                    f.write(str(it)+'\n')      
            cookies=self.dr.get_cookies()
            with open('cookies.txt','wb') as f:
                pickle.dump(cookies,f)
            self.add_log('爬取完成')
            self.add_log('本次结果保存在:'+file_name)
            self.input_word.set('')
            self.run_status.set('待机')
            
    def th_spider_core(self):
        spider_th=threading.Thread(target=self.spider_core)
        spider_th.start()
    
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
     
    def listen_for_result(self):
        """ Check if there is something in the queue. """
        self.print_log()
        self.root.after(100,self.listen_for_result)    
        
        
if __name__=='__main__':
    tb=tb_spider()
    tb.run()        