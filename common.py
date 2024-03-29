# -*- coding: utf-8 -*-
"""
Created on Sun Sep  5 02:28:57 2021

@author: Admin
"""
import re,json,pickle,time,random,xlwt,xlrd,os

login_url="https://login.taobao.com/"
shop_search_url=r'https://shopsearch.taobao.com/search?q={key_word}&sort=sale-desc'
head_1=[
    {'title':'卖家','width':15,'data':'seller'},
    {'title':'店铺ID','width':15,'data':'shop_id'},
    {'title':'店铺链接','width':30,'data':'shop_url'},
    {'title':'店铺类型','width':10,'data':'type'},
    {'title':'是否有消保','width':10,'data':'xiaobao'},
    {'title':'不合规等级','width':10,'data':'rank'},
    {'title':'不合规理由','width':50,'data':'reason'},
    {'title':'关键词','width':50,'data':'key_word'}
]
head_2=[
    {'title':'卖家','width':15,'data':'seller'},
    {'title':'店铺ID','width':15,'data':'shop_id'},
    {'title':'店铺链接','width':30,'data':'shop_url'},
    {'title':'店铺类型','width':10,'data':'type'},
    {'title':'是否有消保','width':10,'data':'xiaobao'},
    {'title':'不合规等级','width':10,'data':'rank'},
    {'title':'不合规理由','width':50,'data':'reason'},
    {'title':'关键词','width':50,'data':'key_word'},
    {'title':'保证金','width':50,'data':'money'},
]
def wt_excel(road,content_list,head=head_1,mode=1):
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
        for hd in head:
            data=hd['data']
            if hd['title']=='不合规理由':
                tmp=''
                for it in item[data]:
                    tmp+=it+';'
                worksheet.write(i,j,tmp) 
            else:
                worksheet.write(i,j,item[data])
            j+=1
    try:
        if mode==1:
            if os.path.exists(road):
                os.remove(road)
        elif mode==2:
            seq=0                
            while os.path.exists(road):
                seq+=1
                road=add_seq(road,seq)
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
        res={'code':'0','msg':'保存成功','road':road}
    finally:
        return res
        
def add_seq(road,n=1):
    last=road.split('.')[-1]
    l=len(last)
    road=road[0:-l-1]
    pattern=re.compile(r'\(\d+\)', re.S|re.M|re.I)
    res=re.findall(pattern,road)
    if len(res) != 0:
        tmp_str=res[-1]
        l=len(tmp_str)
        road=road[0:-l]
    road=road +'('+str(n)+')'+'.xls'
    return road
    
def rd_excel(road):
    res={}
    try:
        sheet = xlrd.open_workbook(road).sheet_by_index(0)
    except WindowsError as e:
        print(e)
        print('请先关闭此文件')
        res={'code':'1','msg':'文件被占用，请先关闭此文件，再开始筛选'}
    except Exception as e:
        print(e)
        print('文件路径出错')
        res={'code':'2','msg':'文件路径出错，请确认文件路径'}
    nrows = sheet.nrows
    ncols=sheet.row_len(0)
    if nrows<1:
        res={'code':'3','msg':'此文件内容为空'}
    i=1
    j=0
        

class message(object):
    def __init__(self,msg='',tp='info'):
        self.type=tp
        self.msg=msg
        
class spider_setting(object):
    def __init__(self):
        #短停时间，默认0.5秒
        self.short_time=0.1
        #长停时间，默认5秒
        self.long_time=0.2
        #店铺最低等级，默认6，即1钻
        self.low_lv=0
        #连续多少页为抓到数据则中断
        self.stop_page=15
                

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

def check_rank(shopItem,rank_lv=6):
    res={}
    reason=[]
    rank=0
    try:
        res['seller']=shopItem['nick']
        res['shop_id']=shopItem['nid']
        res['shop_url']='https:'+shopItem['shopUrl']
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
        if res['xiaobao']=='有' and res['type']=='淘宝':
            iconClass=shopItem['shopIcon']['iconClass']
            seller_rank=re.search(r'seller-rank-\d*',iconClass)
            seller_rank_num=0
            if seller_rank is not None:
                seller_rank_num=int(seller_rank.group(0)[12:])
            if seller_rank_num>=rank_lv:
                # if 'mainAuction' not in shopItem.keys() or len(shopItem['mainAuction'].strip())==0 or shopItem['mainAuction'].strip()=='...':
                #     reason.append('店铺主营描述为空')
                #     rank+=1
 
                rank_msg=json.loads(shopItem['dsrInfo']['dsrStr'])
                grade=float(rank_msg['mas'])+float(rank_msg['sas'])+float(rank_msg['cas'])
                if grade == 0.0:
                    reason.append('动态评分为0')
                    rank+=1
                if grade<1.0:
                    reason.append('动态评分过低')
                    rank+=1
                if 'auctionsInshop' not in shopItem or len(shopItem['auctionsInshop'])<4:
                    reason.append('商品数量少于4')
                    rank+=1
        else:
            # if 'mainAuction' not in shopItem.keys() or len(shopItem['mainAuction'].strip())==0 or shopItem['mainAuction'].strip()=='...':
            #     reason.append('店铺主营描述为空')
            #     rank+=1
            rank_msg=json.loads(shopItem['dsrInfo']['dsrStr'])
            grade=float(rank_msg['mas'])+float(rank_msg['sas'])+float(rank_msg['cas'])
            if grade == 0.0:
                reason.append('动态评分为0')
                rank+=1
            if grade<1.0:
                reason.append('动态评分过低')
                rank+=1
            if 'auctionsInshop' not in shopItem or len(shopItem['auctionsInshop'])<4:
                reason.append('商品数量少于4')
                rank+=1
    except Exception as e:
        print('207:',e)
        rank+=1
        reason.append('数据缺失')
    finally:
        res['rank']=rank
        res['reason']=reason
        return res
    
def check_second(text):
    flag_1=False
    flag_2=False
    pattern=re.compile(r'该店铺已签署消费者保障协议.*已缴纳.*\d+.*元', re.S|re.M|re.I)
    tmp_str=re.search(pattern,text)
    if tmp_str is not None:
        pattern=re.compile(r'\d+', re.S|re.M|re.I)
        tmp_str=tmp_str.group(0)
        num=float(re.search(pattern,tmp_str).group(0))
        if num>0:
            flag_1=True
    pattern=re.compile(r'该用户已通过企业卖家认证', re.S|re.M|re.I)
    corp=re.search(pattern,text)
    pattern=re.compile(r'该用户已通过个体工商户认证', re.S|re.M|re.I)
    person=re.search(pattern,text)
    if corp is None and person is None:
        flag_2=True
    if flag_1 and flag_2:
        return num
    print(flag_1,',',flag_2)
    return 0
    
    
def pj_url(url,params):
    for i in params:
        url+=''+str(i)+'='+str(params[i])+'&'
    if url[-1]=='&':
        url=url[0:-1]
    return url

def do_sleep(arg=0.5):
    #t=random.randint(1,3)*0.1+arg
    t=arg
    time.sleep(t)

def long_sleep(arg=5):
    #t=random.randint(1,3)*0.1+arg
    t=arg
    time.sleep(t)      
    
