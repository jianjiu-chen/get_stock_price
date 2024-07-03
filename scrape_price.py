from selenium import webdriver
from selenium.webdriver.common.by import By

import pandas as pd


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

stock_list = stock_list.iloc[0:10]

# loop through the list
## check if page exists
## download file in a folder
## read the downloaded file
## put the imported data in a db
### check for duplicates for date
## delete the downloaded file

# Not sure how to set download directory
# chrome_options = webdriver.ChromeOptions()
# # chrome_options.add_argument('--download-default-directory=/Users/Chen')
# chrome_options.add_experimental_option("prefs", {"download.default_directory": "/Users/Chen"})
#
# driver = webdriver.Chrome(chrome_options=chrome_options)

driver = webdriver.Chrome()
for i in stock_list.index:
    driver.get('https://www.hkex.com.hk/Market-Data/Securities-Prices/' +
               f'Equities/Equities-Quote?sym={stock_list.iloc[i]["Stock Code"]}&sc_lang=en')

    # wait?

    print(f'Loading page for {stock_list.iloc[i]["Name"]}.')

    # find the correct element for showing data & click
    elements_ = driver.find_elements(By.TAG_NAME, 'li')
    [i for i in elements_ if i.text == '2 Y'][0].click()

    # find the correct element for data download & click
    elements_ = driver.find_elements(By.TAG_NAME, 'a')
    [i for i in elements_ if i.text == 'Export to Excel'][0].click()

    stock_price = pd.read_excel(f'/Users/Chen/Downloads/Equities_{stock_list.iloc[i]["Stock Code"]}.xlsx')

    stock_price.rename(columns={'Time': 'date', 'Closed Price': 'close', 'Volume': 'volume'}, inplace=True)

    stock_price['date'] = stock_price['date'].astype('string')

    stock_price['date'] = stock_price.date.str.replace('/', '')

    stock_price.info()

    




# note
## allow this file to be run in multiple batches, because there are too many stocks