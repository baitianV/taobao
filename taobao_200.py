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


def web_thread(object):
    def __init__(self):
        self.dr=webdriver.Edge('./msedgedriver.exe')
        self.wait=WebDriverWait(self.dr, 5, 0.5)

        
def log_job(ut):
    while True:
        ut.print_log()
        


class tb_spider(object):
    status_list=['待机','运行中']
    lg_status_list=['未登录','已登录']
    
    
            

