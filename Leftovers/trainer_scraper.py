from seleniumwire import webdriver
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
import pymysql
import re
import time
import concurrent.futures


options = webdriver.ChromeOptions()
options.add_argument('headless')

conn = pymysql.connect(host='127.0.0.1', user='root', passwd='210909', db='mysql', charset='utf8')
cur = conn.cursor()
cur.execute("USE trainingdb")

class Page:    
    def __init__(self, url):      
        self.url = url
        self.domain = urlparse(url).netloc
        
    def get_page_info(self,search_keyword=''):        
        driver = webdriver.Chrome(options=options)
        driver.header_overrides = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'}
        try:
            driver.get(self.url)
            bs = BeautifulSoup(driver.page_source, 'html5lib')
            # self.url = driver.current_url
            self.has_cookies = True if len(driver.get_cookies()) > 0 else False
            self.status_code = [request.response.status_code for request in driver.requests if request.response][0]
        finally:
            driver.close()   
        
        self.last_access = datetime.now()
        self.lang = self.get_tag_attr_text(bs, 'html', 'lang')
        self.title = self.get_tag_text(bs, 'title')
        self.h1 = self.get_tag_text(bs, 'h1')
        self.description = self.get_tag_attr_text(bs, 'meta', 'name', 'description', target='content')
        self.keywords = self.get_tag_attr_text(bs, 'meta', 'name', 'keywords', target='content')
        self.has_viewport = True if self.get_tag_attr_text(bs, 'meta', 'name', 'viewport') is not None else False
        
        if search_keyword != '':
            self.search_results =  self.get_search_results(bs, search_keyword)    
    
    def get_search_results(self, bs_obj, keyword):
        macthes = {'in_h1':False,'in_title':False,'in_description':False ,'body':0}
        for word in set(keyword.split(' ')):
            if not macthes['in_h1'] and self.h1 is not None:
                macthes['in_h1'] = len(re.findall(f'(?i){word}', self.h1)) > 0
            if not macthes['in_title'] and self.title is not None:
                macthes['in_title'] = len(re.findall(f'(?i){word}', self.title)) > 0
            if not macthes['in_description'] and self.description is not None:
                macthes['in_description'] = len(re.findall(f'(?i){word}', self.description)) > 0
            if bs_obj.find('body') is not None:
                macthes['body'] += len(re.findall(f'(?i){word}', bs_obj.find('body').get_text()))        
        macthes['body'] = int(macthes['body']/len(set(keyword.split(' '))))        
        return macthes
    
    def print_info(self):
        for key, item in self.__dict__.items():
            print(str(key) + ":" + str(item))
    
    @staticmethod
    def get_tag_text(bs_obj, tag):
        if bs_obj.find(tag) is not None:
            return bs_obj.find(tag).get_text().strip()
        return None
    
    @staticmethod
    def get_tag_attr_text(bs_obj, tag, attr, attr_value='.*', target=''):
        result = bs_obj.find(tag, {f"{attr}":re.compile(f'(?i){attr_value}')})
        if result is not None:            
            if target != '':
                return result[target]
            return result[attr]
        return None

class TrainerScraper:    
    class FoundPage(Page):
        def __init__(self, url, score):
            super().__init__(url)
            self.score = score
    
    def __init__(self,*, ignored_domains=[]):   
        self.visited_pages = set()
        self.visited_urls = set()
        self.ignored_domains = ignored_domains
        
    def get_google_results(self, keyword, amount=10):
        start = time.perf_counter()
        loops = 0
        self.update_domains(cursor=cur)
        self.save_config(keyword, amount)
        driver = webdriver.Chrome(options=options)
        driver.header_overrides = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'}
        total_ranks = 0
        while len(self.visited_urls) + 1 < amount and loops < 6:            
            query_keyword = "+".join(keyword.split(" "))            
            print(f'[{keyword}] Getting response from google.com: ' + str(len(self.visited_urls)))
            if len(self.visited_urls) == 0:
                driver.get(f'https://www.google.com/search?client=ubuntu&channel=fs&q={query_keyword}&ie=utf-8&oe=utf-8')
            else:
                driver.get(f'https://www.google.com/search?client=ubuntu&channel=fs&q={query_keyword}&ie=utf-8&oe=utf-8&start={len(self.visited_urls)+1}')
                
            bs = BeautifulSoup(driver.page_source, 'html5lib')
            
            try:
                with concurrent.futures.ProcessPoolExecutor() as executor:                            
                    processes = []
                    for rank, url in enumerate(self.get_urls(bs)):
                        cur.execute("USE trainingdb")
                        if url not in self.visited_urls and not self.is_already_searched(url, keyword):
                            self.visited_urls.add(url)
                            processes.append(executor.submit(self.get_page_results, url, keyword, (rank+1)+total_ranks))
                    total_ranks = max(total_ranks, len(self.visited_urls))   

                    for result in concurrent.futures.as_completed(processes):
                        result = result.result()
                        if result is not None:                            
                            self.visited_pages.add(result)
                            self.save_search(keyword, result.score, result)
            finally:
                conn.commit()
            loops += 1

        driver.close()
        print(f"Searching for {keyword} done in {round(time.perf_counter() - start, 2)} second(s)")
        
    def get_page_results(self, url, keyword, score):
        #Nova conexão, pois este método não é thread safe  
        connection = pymysql.connect(host='127.0.0.1', user='root', passwd='210909', db='mysql', charset='utf8')
        cursor = connection.cursor()
        cursor.execute("USE trainingdb")

        found_page = self.FoundPage(url, score)

        if found_page.domain in self.ignored_domains:
            return None
        
        print("Looking at: " + url)        
        try:
            found_page.get_page_info(keyword)
            self.save_domain(found_page.domain, cursor=cursor)            
            self.save_page(found_page, cursor=cursor)            
            connection.commit()
            found_page.print_info()
            print()
            return found_page
        except Exception as e:
            print(e)
            self.save_domain(found_page.domain, ignore=True, cursor=cursor)
            conn.commit()
            self.update_domains(cursor=cursor)
            print(f"Error in: {url}\n")
            return None
        finally:
            conn.commit()
            connection.commit()
            cursor.close()
            connection.close()          
        return None
    
    def get_urls(self, bs_obj):        
        for div in bs_obj.find_all('div', class_='srg'):    
            for a in div.find_all('a'):
                if not a.find('span') and 'webcache' not in a['href'] and 'class' not in a.attrs:
                    yield a['href']
    
    def update_domains(self, *, cursor=None):
        cursor.execute(f"SELECT * FROM domain where blackListed = 1")
        for bad_domain in cursor.fetchall():
            self.ignored_domains.append(bad_domain[1])
    
    @staticmethod
    def is_already_searched(url, keyword):
        cur.execute("USE trainingdb")
        cur.execute(f"SELECT idPage FROM page WHERE url like '{url}'")
        q = cur.fetchone()
        if q is None:
            return False
        id_page = q[0]
        cur.execute(f"SELECT idConfig FROM config WHERE keyword like '{keyword}'")
        q = cur.fetchone()
        if q is None:
            return False
        id_config = q[0]
        cur.execute(f"SELECT * FROM search WHERE idPage = {id_page} and idConfig = {id_config}")
        if cur.fetchone():
            print(url + " already visited.")
            return True
        return False
    
    @staticmethod
    def save_domain(netloc, ignore=False, *, cursor=None):
        cursor.execute(f"SELECT netloc FROM domain where netloc like '{netloc}'")
        if not cursor.fetchone():
            cursor.execute(f"INSERT INTO domain (netloc, blackListed) values ('{netloc}', {1 if ignore else 0})")
        
    @staticmethod
    def save_config(keyword, amount):
        cur.execute("USE trainingdb")
        cur.execute(f"SELECT keyword FROM config where keyword like '{keyword}'")
        if not cur.fetchone():
            cur.execute(f"INSERT INTO config (keyword, maxPages) values ('{keyword}', {amount})")
        
    @staticmethod
    def save_page(found_page, *, cursor=None):
        print("save page: " + found_page.url) 
        cursor.execute(f"SELECT idDomain FROM domain where netloc like '{found_page.domain}'")
        domain_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO page (url, idDomain, hasTitle, hasH1, hasDescription, hasKeywords, hasViewport) values " \
                    f"('{found_page.url}', {domain_id}," \
                    f"{1 if found_page.title else 0},{1 if found_page.h1 else 0}, {1 if found_page.description else 0}, " \
                    f"{1 if found_page.keywords else 0}, {1 if found_page.has_viewport else 0})")
        
    @staticmethod
    def save_search(keyword, score, found_page):
        print("save search from: " + found_page.url)
        cur.execute(f"SELECT idConfig FROM config where keyword like '{keyword}'")
        config_id = cur.fetchone()[0]
        cur.execute(f"SELECT idPage FROM page where url like '{found_page.url}'")
        page_id = cur.fetchone()[0]
        cur.execute(f"INSERT INTO search (idConfig, idPage, score) values ({config_id}, {page_id}, {score})")        
        cur.execute(f"SELECT max(idSearch) FROM search")
        search_id = cur.fetchone()[0]
        results = found_page.search_results
        cur.execute("INSERT INTO result (idSearch, matchesInBody, keywordInTitle, keywordInDescription, keywordInH1) values " \
                    f"({search_id}, {results['body']}, {1 if results['in_title'] else 0}, {1 if results['in_description'] else 0}, {1 if results['in_h1'] else 0})")


try:
    names = [
        'vaporwave', 'tree', 'flower', 'pizza', 'bolo', 'coconut',
         'bolsa', 'glass', 'water', 'coffee', 'machine', 'galileu', 'socrates', 'power', 'futebol', 'bola', 'soccer', 
         'japan', 'pope', 'jesus', 'lucifer', 'demon', 'ocean', 'joy', 'metroid']

    for name in names:
        trainer = TrainerScraper(ignored_domains=['www.youtube.com', 'www.instagram.com', 'twitter.com', 'www.facebook.com'])
        trainer.get_google_results(name)
finally:
    cur.close()
    conn.close()