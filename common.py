# -*- coding: utf-8 -*-
"""
Created on Sun Sep  5 02:28:57 2021

@author: Admin
"""
import re,json,pickle,time,random,xlwt,xlrd,os

login_url="https://login.taobao.com/"
shop_search_url=r'https://shopsearch.taobao.com/search?q={key_word}&sort=sale-desc'
head_1=[
    {'title':'卖家','width':15},
    {'title':'店铺ID','width':15},
    {'title':'店铺链接','width':30},
    {'title':'店铺类型','width':10},
    {'title':'是否有消保','width':10},
    {'title':'不合规等级','width':10},
    {'title':'不合规理由','width':50}
]
head_2=[
    {'title':'卖家','width':15},
    {'title':'店铺ID','width':15},
    {'title':'店铺链接','width':30},
    {'title':'店铺类型','width':10},
    {'title':'是否有消保','width':10},
    {'title':'不合规等级','width':10},
    {'title':'不合规理由','width':50}
]
def wt_excel(road,content_list,head=head_1):
    res={}
    workbook = xlwt.Workbook(encoding= 'utf-8')
    worksheet = workbook.add_sheet("淘宝")
    i=0
    j=0
    for item in head_1:
        worksheet.write(i,j,item['title'])
        worksheet.col(j).width = item['width']*256
        j+=1

    for item in content_list:
        i+=1
        j=0
        for key,value in item.items():
            if j==6:
                tmp=''
                for it in value:
                    tmp+=it+';'
                worksheet.write(i,j,tmp) 
            else:
                worksheet.write(i,j,value)
            j+=1
    try:
        if os.path.exists(road):
            os.remove(road)
        workbook.save(road)
    except WindowsError as e:
        print(e)
        print('请先关闭此文件')
        res={'code':'1','msg':'文件被占用，请先关闭此文件，再点击保存'}
    except Exception as e:
        print(e)
        print('文件路径出错')
        res={'code':'2','msg':'文件路径出错，请确认文件路径'}
    else:
        res={'code':'0','msg':'保存成功'}
    finally:
        return res
        

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
    
