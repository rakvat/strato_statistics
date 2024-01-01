# -*- coding: utf-8 -*-
import scrapy
import json
import sys
import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

sys.path.append('/opt/settings')
import strato_config

class StatisticsSpider(scrapy.Spider):
    START_DATE = '2023-01-01'
    END_DATE = '2024-01-31'
    name = 'statistics'
    allowed_domains = ['www.strato.de']
    start_urls = ['https://www.strato.de/apps/CustomerService']

    def parse(self, response):
        password = input('Enter Strato Master Password\n')
        return [scrapy.FormRequest.from_response(response,
                    formdata={'identifier': strato_config.USERNAME, 'passwd': password},
                    callback=self.after_login)]

    def after_login(self, response):
        # check login succeed before going on
        if b'authentication failed' in response.body:
            self.log('Login failed', level=self.log.ERROR)
            return
        else:
            self.log('Logged in')
            # find session id
            search = "apps/CustomerService?sessionID="
            s = str(response.body)
            session_id = s[s.find(search) + len(search):s.find('"', s.find(search) + len(search) + 1)]
            self.log(session_id)

            date = datetime.datetime.strptime(self.START_DATE, '%Y-%m-%d')
            while date.strftime('%Y-%m-%d') <= self.END_DATE:
                query_parameters = f"sessionID={session_id}&node=kds_Statistic&amp;action_top_urls_json.x=1&amp;nother=1&amp;off=0&amp;cnt=5000000&amp;date={date.strftime('%Y-%m-%d')}"
                self.log(query_parameters)
                statistic_url = response.url.replace('node=kds_Vertragsbetreuung_2', query_parameters)
                self.log(statistic_url)
                yield scrapy.Request(url=statistic_url, callback=self.parse_statistic)
                date = date + relativedelta(months=1)

    def parse_statistic(self, response):
        self.log('parse')
        data = json.loads(response.body)
        data = data['toplist']
        values = data['values']
        urls = data['list']
        df = pd.DataFrame(list(zip(urls, values)))
        condition = df[0].str.startswith('http://www.transform-social.org') & ~df[0].str.startswith('http://www.transform-social.org/stylesheets') & ~df[0].str.startswith('http://www.transform-social.org/javascript') & ~df[0].str.startswith('http://www.transform-social.org/favicon.ico')
        transform = df[condition]
        date_from_url = response.url.split("=")[-3].split("&")[0]
        filename = f'data/{date_from_url}.txt'
        self.log(filename)
        values = transform.values
        with open(filename, 'w') as f:
            for tuple in values:
                line = f'{tuple[1]:5} {tuple[0]}\n'
                f.write(line)
