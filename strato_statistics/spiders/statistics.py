# -*- coding: utf-8 -*-
import scrapy
import json
import sys
import pandas as pd

sys.path.append('/opt/settings')
import strato_config

class StatisticsSpider(scrapy.Spider):
    DATES = ['2017-11-01', '2017-12-01', '2018-01-01', '2018-02-01', '2018-03-01', '2018-04-01']
    name = 'statistics'
    allowed_domains = ['www.strato.de']
    start_urls = ['https://www.strato.de/apps/CustomerService']

    def parse(self, response):
        return [scrapy.FormRequest.from_response(response,
                    formdata={'identifier': strato_config.USERNAME, 'passwd': strato_config.PASSWORD},
                    callback=self.after_login)]

    def after_login(self, response):
        # check login succeed before going on
        if b'authentication failed' in response.body:
            self.log('Login failed', level=log.ERROR)
            return
        else:
            self.log('Logged in')
            for date in self.DATES:
                query_parameters = 'node=kds_Statistic&amp;action_top_urls_json.x=1&amp;nother=1&amp;off=0&amp;cnt=5000000&amp;date={}'.format(date)
                statistic_url = response.url.replace('node=kds_Vertragsbetreuung_2', query_parameters)
                yield scrapy.Request(url=statistic_url, callback=self.parse_statistic)

    def parse_statistic(self, response):
        data = json.loads(response.body)
        data = data['toplist']
        values = data['values']
        urls = data['list']
        df = pd.DataFrame(list(zip(urls, values)))
        condition = df[0].str.startswith('http://www.transform-social.org') & ~df[0].str.startswith('http://www.transform-social.org/stylesheets') & ~df[0].str.startswith('http://www.transform-social.org/javascript') & ~df[0].str.startswith('http://www.transform-social.org/favicon.ico')
        transform = df[condition]
        self.log(transform.head(200))
        filename = 'data/%s.txt' % response.url.split("=")[-1]
        tm = transform.as_matrix()
        with open(filename, 'w') as f:
            for i in range(0, len(tm)):
                line = '{: 5} {}\n'.format(tm[i][1], tm[i][0])
                f.write(line)
