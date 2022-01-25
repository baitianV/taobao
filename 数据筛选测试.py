# -*- coding: utf-8 -*-
"""
Created on Thu Nov 25 22:36:50 2021

@author: Admin
"""
from common import *

with open('data.txt','r',encoding='utf-8') as f:
    txt=f.read()
data=get_json(txt)
shopItems=data['mods']['shoplist']['data']['shopItems']

