# -*- coding: utf-8 -*-
"""
Created on Sun Sep  5 02:28:57 2021

@author: Admin
"""
import re,json,pickle,time,random


class message(object):
    def __init__(self,msg='',tp='info'):
        self.type=tp
        self.msg=msg

def to_cookies():
    with open('cookies.txt','rb') as f:
        cookies=pickle.load(f)
    return cookies   

def get_page(pager,num=0):
    pageSize=pager['pageSize']
    totalPage=pager['totalPage']
    if(num<=0):
        return (totalPage-1)*pageSize
    else:
        return (num-1)*pageSize

def get_json(text):
    pattern=re.compile(r'g_page_config = {.*?};', re.S|re.M|re.I)
    web_content = re.search(pattern,text).group(0)
    pattern=re.compile(r'{.*}', re.S|re.M|re.I)
    web_content=re.search(pattern,web_content).group(0)
    data=json.loads(web_content,strict=False)
    return data

def check_rank(shopItem):
    res={}
    reason=[]
    rank=0
    try:
        res['seller']=shopItem['nick']
        res['shop_id']=shopItem['nid']
        res['shop_url']=shopItem['shopUrl']
        if 'title' in shopItem['shopIcon'] and shopItem['shopIcon']['title']=='天猫':
            res['type']='天猫'
        else:
            res['type']='淘宝'
        if 'icons' not in shopItem or len(shopItem['icons'])==0:
            res['xiaobao']='无'
        else:
            res['xiaobao']='无'
            for i in shopItem['icons']:
                if i['title']=='卖家承诺消费者保障服务':
                    res['xiaobao']='有'
        if res['type']=='淘宝' and res['xiaobao']=='有':
            iconClass=shopItem['shopIcon']['iconClass']
            seller_rank=re.search(r'seller-rank-\d*',iconClass)
            if seller_rank is not None:
                seller_rank_num=int(seller_rank.group(0)[12:])
                if seller_rank_num<3:
                    reason.append('信誉评分过低')
                    rank+=1
                
            if 'mainAuction' not in shopItem.keys() or len(shopItem['mainAuction'].strip())==0 or shopItem['mainAuction'].strip()=='...':
                reason.append('店铺主营描述为空')
                rank+=1
                
            rank_msg=json.loads(shopItem['dsrInfo']['dsrStr'])
            grade=float(rank_msg['mas'])+float(rank_msg['sas'])+float(rank_msg['cas'])
            if grade<1.0:
                reason.append('动态评分过低')
                rank+=1
    except Exception as e:
        print(e)
        rank+=1
        reason.append('数据缺失')
    finally:
        res['rank']=rank
        res['reason']=reason
        return res
    
def pj_url(url,params):
    for i in params:
        url+=''+str(i)+'='+str(params[i])+'&'
    if url[-1]=='&':
        url=url[0:-1]
    return url

def do_sleep():
    t=random.randint(5,10)*0.1+0.5
    time.sleep(t)

def long_sleep():
    t=random.randint(5,10)*0.3+5
    time.sleep(t)      