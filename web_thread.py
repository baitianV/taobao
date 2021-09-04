# -*- coding: utf-8 -*-
"""
Created on Sun Sep  5 03:02:01 2021

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

class web_thread(Thread):
    
    def __init__(self,log_queue):
        try:
            self.log_queue=log_queue
            self.dr=webdriver.Edge('./msedgedriver.exe')
            self.wait=WebDriverWait(self.dr, 5, 0.5)
            Thread.__init__(self)
        except FileNotFoundError as e:
            print(e)
        except Exception as e:
            print(e)
        
    def run():
        self.add_log('浏览器线程已启动')
        
    #插入日志    
    def add_log(self,msg='',tp='info'):
        self.log_queue.put(message(msg,tp))
        
    def spider_core(self,key_word):
        aa=0
        tb_rank_list=[]
        tm_rank_list=[]
        all_list=[]
        try:
            self.add_log('开始本次爬虫')
            key_url=shop_search_url.format(key_word=key_word)
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
            file_name='淘宝_'+key_word.replace(' ', '_')+'.txt'
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
    