# -*- coding: utf-8 -*-
"""
Created on Sun Sep  5 01:09:21 2021

@author: Admin
"""

from tkinter import filedialog
from tkinter import *
from selenium import webdriver
from selenium.common.exceptions import TimeoutException,SessionNotCreatedException,NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from msedge.selenium_tools import EdgeOptions
from msedge.selenium_tools import Edge
from urllib.parse import quote
import json,pickle,re,time,random,threading,queue,traceback
from bs4 import BeautifulSoup

from tklog.tklog import *
import logging
from common import *


class tb_spider(object):
    status_list=['待机','运行中']
    lg_status_list=['未登录','已登录']
    path={
        '爬取结果':r'./爬取结果/',
        '缓存路径':r'./爬取结果/缓存文件/',
        '二筛结果':r'./二筛结果/'
    }
        
    def __init__(self):
        self.root=Tk()
        self.run_status=StringVar()
        self.filepath = StringVar()
        self.filename = ''
        self.run_status.set('待机')
        self.login_status=StringVar()
        self.login_status.set('未登录')
        self.key_status=StringVar()
        self.key_status.set('')
        self.input_word=StringVar()
        self.input_word.set('')
        self.key_word=''
        self.log_queue=queue.Queue()
        self.tb_rank_list=[]
        self.tm_rank_list=[]
        self.second_list=[]
        self.second_res_list=[]
        self.setting=spider_setting()

        try:
            self.log_job=self.root.after(100,self.listen_for_result)
            self.init_ui()
            #self.dr=webdriver.Edge('./msedgedriver.exe')
            options = EdgeOptions()
            options.use_chromium = True
            options.add_argument("--disable-blink-features=AutomationControlled")
            self.dr=Edge('./msedgedriver.exe',options=options)
            #self.dr.maximize_window()
            self.wait=WebDriverWait(self.dr, 4, 0.5)
            #self.root.mainloop()
        except SessionNotCreatedException as e:
            print(e)
            self.logger.debug('浏览器驱动版本需要更新，请联系管理员！')
            self.quit0()
        except FileNotFoundError as e:
            print(e)
            self.logger.debug(e)
            self.quit0()
        except Exception as e:
            print(e)
            self.logger.debug(e)
            self.quit0()
    
    def init_ui(self):
        self.root.geometry('1200x300')
        self.root.title('爬取程序')            
        self.root.protocol("WM_DELETE_WINDOW", self.quit0)
        
        panel_1=LabelFrame(self.root,padx=1,pady=1)
        
        #第一层
        #登录按钮
        Button(self.root,text='登录',command=self.login, width = 8).grid(row=0, column=0)
        #开始按钮
        self.run_button=Button(self.root,text='刷新',command=self.refresh, width = 8)
        self.run_button.grid(row=0, column=1)           
        Frame(self.root,width=20).grid(row=0, column=2,columnspan=1)
        # status_frame = LabelFrame(self.root)
        
        #状态栏
        status_frame1 = LabelFrame(self.root)
        status_frame2 = LabelFrame(self.root)
        status_frame3 = LabelFrame(self.root)
        Label(status_frame1,text='运行状态:').pack(side=LEFT)             
        Label(status_frame1,textvariable=self.run_status).pack(side=RIGHT)            
        Label(status_frame2,text='登录状态:').pack(side=LEFT)                       
        Label(status_frame2,textvariable=self.login_status).pack(side=RIGHT)
        Label(status_frame3,text='当前关键词:').pack(side=LEFT)                       
        Label(status_frame3,textvariable=self.key_status).pack(side=RIGHT)
        status_frame1.grid(row=0, column=3)
        status_frame2.grid(row=0, column=4)
        status_frame3.grid(row=0, column=5)
        
        #参数栏
        self.short_time=StringVar()
        self.short_time.set(self.setting.short_time)
        self.long_time=StringVar()
        self.long_time.set(self.setting.long_time)
        self.low_lv=StringVar()
        self.low_lv.set(self.setting.low_lv)
        self.stop_page=StringVar()
        self.stop_page.set(self.setting.stop_page)
        setting_frame1 = LabelFrame(self.root)
        setting_frame2 = LabelFrame(self.root)
        setting_frame3 = LabelFrame(self.root)
        setting_frame4 = LabelFrame(self.root)
        Label(setting_frame1,text='短停时间（每查一页停一次）:').pack(side=LEFT)             
        Entry(setting_frame1,textvariable=self.short_time).pack(side=RIGHT) 
        Label(setting_frame2,text='长停时间（每查十页停一次）:').pack(side=LEFT)             
        Entry(setting_frame2,textvariable=self.long_time).pack(side=RIGHT)
        Label(setting_frame3,text='店铺最低等级:').pack(side=LEFT)             
        Entry(setting_frame3,textvariable=self.low_lv).pack(side=RIGHT) 
        Label(setting_frame4,text='中断页数:').pack(side=LEFT)             
        Entry(setting_frame4,textvariable=self.stop_page).pack(side=RIGHT) 
        setting_frame1.grid(row=0, column=7)
        setting_frame2.grid(row=1, column=7)
        setting_frame3.grid(row=2, column=7)
        setting_frame4.grid(row=3, column=7)
        Button(self.root,text='修改参数',command=self.update_setting, width = 8).grid(row=4, column=7)
        
        #日志插件初始化
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        fmt = logging.Formatter('%(asctime)s: %(message)s')
        tkhandler = tklogHandler(master=self.root,width = 60,height=14)
        tkhandler.grid(row=1, column=3,columnspan=4,rowspan=4)
        tkhandler.setFormatter(fmt)
        self.logger.addHandler(tkhandler)
        
        #第二层
        #关键词设置框
        Label(self.root,text='关键词设置:',width=8).grid(row=1, column=0,columnspan=1)   
        Entry(self.root,width=24,textvariable=self.input_word).grid(row=1, column=1,columnspan=2)
        #第三层
        Button(self.root,text='确认',command=self.change_key_word, width = 8).grid(row=2, column=0,columnspan=1)
        Button(self.root,text='清空',command=self.clear_key_word, width = 8).grid(row=2, column=1,columnspan=1)
        Button(self.root,text='开始',command=self.start_all_spider, width = 8).grid(row=2, column=2,columnspan=1)

        #第四层
        Button(self.root,text='一筛',command=self.start_spider, width = 8).grid(row=3, column=0,columnspan=1)
        Button(self.root,text='保存',command=self.save_result, width = 8).grid(row=3, column=1,columnspan=1)
        Button(self.root,text='暂停',command=self.save_result, width = 8).grid(row=3, column=2,columnspan=1)
        
        #第五层
        #文件选择框
        fileFrame=LabelFrame(self.root)
        Label(fileFrame, text='选择文件：').grid(row=1, column=0, padx=5, pady=5)
        Entry(fileFrame, textvariable=self.filepath).grid(row=1, column=1, padx=5, pady=5)
        Button(fileFrame, text='打开文件', command=self.selectFile).grid(row=1, column=2, padx=5, pady=5)
        fileFrame.grid(row=4,column=0,columnspan=3)
        
        #第六层
        Button(self.root, text='开始二筛', command=self.start_second,width = 8).grid(row=5, column=0, columnspan=1)
        
        
        
    def quit0(self):
        print('系统退出')
        # if self.dr is not None:
        #     self.dr.quit()
        self.root.after_cancel(self.log_job)
        self.root.destroy()      

    def run(self):
        try:
            # th=threading.Thread(target=self.root.mainloop())
            # th.start()
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
        flag=bs.find_all('a',class_='site-nav-login-info-nick')
        
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
        self.key_status.set(self.key_word)
        self.add_log("关键词已变为："+self.key_word)
        
    def clear_key_word(self):
        self.input_word.set('')
        self.key_word=self.input_word.get()
        self.key_status.set(self.key_word)
        self.add_log("关键词已清空")
     
    def update_setting(self):
        try:
            self.setting.short_time=float(self.short_time.get())
            self.setting.long_time=float(self.long_time.get())
            self.setting.low_lv=int(self.low_lv.get())
            self.setting.stop_page=int(self.stop_page.get())
        except Exception as e:  
            print(e)
            self.add_log('参数格式错误，请检查','warning')
        else:
            self.add_log('修改参数成功')
            
            
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
    

        return False
    
    def check_wait(self,method):
        def check_find(driver):
                con1 = EC.presence_of_element_located((By.XPATH, '//span[contains(string(), "Taobao.com")]'))
                con2 = EC.presence_of_element_located((By.XPATH, '//em[contains(string(), "Taobao.com")]'))
                if con1 or con2:
                    return True
                else:
                    return False
        try:
            res=self.wait.until(method)
        except TimeoutException as e:
            e_check =self.wait.until(check_find)
            if e_check:
                do_sleep(self.setting.short_time)
                self.handle_vertify()
            
        finally:
            return self.wait.until(method)        
    
    #爬虫核心代码    
    def spider_core(self):
        aa=0
        self.tb_rank_list=[]
        self.tm_rank_list=[]
        all_list=[]
        try:
            self.add_log('开始本次爬虫')
            key_url=shop_search_url.format(key_word=self.key_word)
            self.dr.get(key_url)
            
            e_input =self.check_wait(EC.presence_of_element_located((By.CSS_SELECTOR, "input.input.J_Input")))
            e_button = self.check_wait(EC.presence_of_element_located((By.CSS_SELECTOR, "span.btn.J_Submit")))
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
                do_sleep(self.setting.short_time)
                e_input = self.check_wait(EC.presence_of_element_located((By.CSS_SELECTOR, "input.input.J_Input")))
                e_button = self.check_wait(EC.presence_of_element_located((By.CSS_SELECTOR, "span.btn.J_Submit")))
                e_input.clear()
                e_input.send_keys(i)
                #e_button.click()
                self.dr.get(self.get_url(i))
                self.check_wait(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'span.current'),str(i)))
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
                    rank_res=check_rank(shopItem,self.setting.low_lv)
                    rank_res['key_word']=self.key_word
                    all_list.append(rank_res)
                    if rank_res['rank']>0:
                        self.tb_rank_list.append(rank_res)
                        rank_count+=1
                if rank_count==0:
                    key_count+=1
                else:
                    key_count=0
                    
                page_count+=1
                self.add_log('已抓取{}页'.format(page_count))
                if page_count%10==0:
                    long_sleep(self.setting.long_time)
                if key_count>=self.setting.stop_page:
                    self.add_log('连续三页未抓取到有用信息，自动退出本次爬虫')
                    break
        except TimeoutException as e:
            traceback.print_exc()
            self.add_log("连接超时，请检查网络",'warning')
        finally:
            self.add_log('爬取完成')
            self.save_result()
            cookies=self.dr.get_cookies()
            with open('cookies.txt','wb') as f:
                pickle.dump(cookies,f)
            self.input_word.set('')
            self.run_status.set('待机')
    
    def handle_vertify(self):
        i=0
        while True:
            i=i+1
            check=self.dr.find_elements(By.XPATH, '//div[contains(string(), "验证失败")]')
            if len(check)>0:
                btn=self.dr.find_element_by_id("nc_1_wrapper")
                action = ActionChains(self.dr)
                action.click(btn)
                action.perform()
                #time.sleep(0.3)
            sf=self.dr.find_elements_by_id("J_sufei")
            sp=self.dr.find_elements_by_id("nc_1_n1z")
            if len(sf)>0:
                iframe=sf[0].find_element_by_tag_name("iframe")
                self.dr.switch_to_frame(iframe)
                span=self.dr.find_element_by_id("nc_1_n1z")
            elif len(sp)>0:
                span=self.dr.find_element_by_id("nc_1_n1z")   
            else:
                return
            self.add_log('验证解锁中')
            print(len(sf),len(sp))
            action = ActionChains(self.dr)
            action.click_and_hold(span)
            for item in [30]*10:
                action.move_by_offset(item,0)
            action.release()
            action.perform()
            if i>3:
                break
    
    
    def save_result(self):
        file_name=self.key_word.replace(' ', '_')+'.xls'
        file_path='./爬取结果/'+file_name
        tmp_path='./爬取结果/缓存文件/'+self.key_word.replace(' ', '_')+'.txt'
        with open(tmp_path,'wb') as f:
            pickle.dump(self.tb_rank_list,f)
        res=wt_excel(file_path,self.tb_rank_list)
        if res['code']=='0':
            self.add_log('本次结果保存在:'+res['road'])
        else:
            self.add_log(res['msg'])
            
    def save_second(self):
        file_name=self.filename+'.xls'
        file_path=tb_spider.path['二筛结果']+file_name
        res=wt_excel(file_path,self.second_res_list,head_2,2)
        if res['code']=='0':
            self.add_log('本次结果保存在:'+res['road'])
        else:
            self.add_log(res['msg'])  
            
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
        self.print_log()
        self.log_job=self.root.after(100,self.listen_for_result)    

    def selectFile(self):
        filepath = filedialog.askopenfilename(defaultextension='.xls')
        if filepath:
            self.filepath.set(filepath)
            self.filename=filepath.split('/')[-1].split('.')[0]
            self.add_log('已选择文件：'+self.filepath.get())
            print(self.filename)
            
    def load_tmp(self):
        tmp_path=tb_spider.path['缓存路径']+self.filename+'.txt'
        try:
            f=open(tmp_path,'rb')
            self.second_list=pickle.load(f)
        except FileNotFoundError as e:
            self.add_log('未找到对应缓存文件，请检查！','warning')
        except Exception as e:
            self.add_log('选择的文件可能存在问题，请检查！','warning')

    def start_second(self):
        if self.login_status.get() == '已登录':
            if self.run_status.get() == '待机':
                if self.filename.strip()=='':
                    self.add_log('请先选择需要二筛的文件','warning')
                else:
                    self.run_status.set('运行中')
                    self.th_spider_second()
            else:
                self.add_log('未处于待机状态，不允许重新开始','warning')
        else:
            self.add_log('请先登录后，刷新，再点击开始','warning')  

    
    def spider_second(self):
        self.add_log('二筛开始')
        self.second_res_list=[]        
        self.load_tmp()
        try:
            n=0
            for item in self.second_list:
                shop_url=item['shop_url']
                if 'https:' not in shop_url:
                    shop_url='https:'+shop_url
                self.dr.get(shop_url)
                tmp_wait =self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.shop-summary.J_TShopSummary")))
                do_sleep(self.setting.short_time)
                money=check_second(self.dr.page_source)
                if money>0:
                    item['money']=money
                    self.second_res_list.append(item)
                n+=1
                self.add_log('已完成第{}个店铺的筛选'.format(n))
        except TimeoutException:
            self.add_log("连接超时，请检查网络",'warning')
        except Exception as e:
            print(e)
        finally:
            self.add_log('二筛完成')
            self.save_second()
            cookies=self.dr.get_cookies()
            with open('cookies.txt','wb') as f:
                pickle.dump(cookies,f)
            self.run_status.set('待机')
            
    def th_spider_second(self):
        spider_th=threading.Thread(target=self.spider_second)
        spider_th.start()
    
    def all_spider(self):
        self.spider_core()
        self.filename=self.key_word.replace(' ', '_')
        self.spider_second()
        
    def th_all_spider(self):
        spider_th=threading.Thread(target=self.all_spider)
        spider_th.start()
        
    def start_all_spider(self):
        if self.login_status.get() == '已登录':
            if self.run_status.get() == '待机':
                if self.key_word.strip() == '':
                    self.add_log('关键词为空，请设置关键词','warning')
                else:
                    self.run_status.set('运行中')
                    self.th_all_spider()
            else:
                self.add_log('未处于待机状态，不允许重新开始','warning')
        else:
            self.add_log('请先登录后，刷新，再点击开始','warning')      
    
    
#%%
if __name__=='__main__':
    tb=tb_spider()
    tb.run()
    # tb.root.destroy()
    # tb.dr.get(login_url)
    # #%%
    # tb.filename='123'
    # tb.load_tmp()
    # #%%
    # for item in tb.second_list:
    #     tb.dr.get('http:'+item['shop_url'])
    #     print('http:'+item['shop_url'])
    #     tmp_wait =tb.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.shop-summary.J_TShopSummary")))
    #     page_source=tb.dr.page_source
    #     print(check_second(tb.dr.page_source))
    # #t.dr.get()
    # #%%
    # tb.dr.get(r'https://shop260170049.taobao.com/?spm=a230r.7195193.1997079397.2.7deb5366iPLvVY')
    # tmp_wait =tb.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.shop-summary.J_TShopSummary")))
    # page_source=tb.dr.page_source
    # print(check_second(tb.dr.page_source))
    # # #%%
#%%
