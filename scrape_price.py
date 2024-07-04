# arrange these
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import sqlite3
import pandas as pd
import time
import datetime
import pytz

parser = argparse.ArgumentParser()
parser.add_argument('--seqstart', type=int, required=True,
                    help='The stock sequence number, from which I scrape data (starting from 1 not 0).')
parser.add_argument('--seqend', type=int, required=True,
                    help='The stock sequence number, up to which I scrape data (starting from 1 not 0).')

args = parser.parse_args()

i_start = args.seqstart - 1
i_end = args.seqend

scroll_y = 30  # need to scroll down for clicking
today = datetime.datetime.now(pytz.timezone('Asia/Hong_Kong')).date()

# get stock list (filter out delisted ones)
stock_df = (
    pd.read_excel('stock_list.xlsx', sheet_name='processed1')
    .dropna(how='all').reset_index(drop=True)
)

stock_list = (
    stock_df[stock_df['Stock Code'].apply(lambda x: not isinstance(x, str))]
    .loc[:, ['Stock Code', 'Name']]
    .reset_index(drop=True)
)

stock_list = stock_list.iloc[i_start:i_end]

# start scraping price data (loop through stocks)
print('==================================')
print('Log for', today, '.')
driver = webdriver.Chrome()
for i in stock_list.index:
    stock_code_i = stock_list.iloc[i]["Stock Code"]
    stock_name_i = stock_list.iloc[i]["Name"]
    stock_seq_i = i + 1
    print(f'Started for {stock_name_i} (stock code: {stock_code_i}; stock sequence number: {stock_seq_i}).')

    driver.get('https://www.hkex.com.hk/Market-Data/Securities-Prices/' +
               f'Equities/Equities-Quote?sym={stock_code_i}&sc_lang=en')
    print('Loaded page.')

    # find the correct element for showing data & click
    ActionChains(driver).scroll_by_amount(delta_x=0, delta_y=scroll_y).perform()
    # if no scroll, can't see/click the tab
    elements_ = driver.find_elements(By.TAG_NAME, 'li')
    [i for i in elements_ if i.text == '2 Y'][0].click()

    # find the correct element for data download & click
    elements_ = driver.find_elements(By.TAG_NAME, 'a')
    [i for i in elements_ if i.text == 'Export to Excel'][0].click()
    print('Downloaded data.')

    # read the downloaded file
    time.sleep(5)
    stock_price = pd.read_excel(f'/Users/Chen/Downloads/Equities_{stock_list.iloc[i]["Stock Code"]}.xlsx')
    stock_price.rename(columns={'Time': 'date', 'Closed Price': 'close', 'Volume': 'volume'}, inplace=True)
    stock_price['date'] = pd.to_datetime(stock_price['date'], format='%Y/%m/%d')
    # stock_price['date'] = stock_price.date.str.replace('/', '')
    print('Read data.')

    # put the imported data in a db
    with sqlite3.connect("/Users/Chen/project/get_stock_price/stock_price.db") as con:
        cur = con.cursor()
        equity_name = f'equities_{stock_list.iloc[i]["Stock Code"]}'

        existing_equities = cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        existing_equities = [i[0] for i in existing_equities]
        if equity_name in existing_equities:  # if table exist, avoid duplicates
            # find that latest date
            latest_date_available = \
                cur.execute('SELECT date FROM equities_1 ORDER BY date DESC LIMIT 1').fetchone()[0]
            # subset stock_price
            stock_price = stock_price[stock_price['date'] > latest_date_available]
            # append
            stock_price.to_sql(equity_name, con, if_exists='append', index=False)
        else:  # create new table
            stock_price.to_sql(equity_name, con, index=False)

    print('Stored data.')

driver.quit()


