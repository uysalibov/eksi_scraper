import aiohttp
import asyncio
import requests
from bs4 import BeautifulSoup
import time
import sys
from colorama import init, Fore
from constant import * # import all constant variables from constant.py
import argparse
from datetime import datetime
import csv

init() #initialize colorama for windows

parser = argparse.ArgumentParser() # create argument parser
parser.add_argument('-u', '--url', type=str, required=True, help='URL of you want to scrape') # add url argument
parser.add_argument('-o', '--output', type=str, required=False, default='', help='Name of the output file. Default Name: eksi_scraper') # add output file argument

args = parser.parse_args() # parse all arguments

async def fetch(session, url, writer):
    async with session.get(url, headers={'User-Agent':USER_AGENT}) as resp: 
        text_resp = await resp.text() # source of page
        soup = BeautifulSoup(text_resp, 'html.parser') # convert string to soup object

        entry = soup.find('div', {'class':'content'}) # find entry content
        entry_date = soup.find('a', {'class':'entry-date permalink'}) # find date of the entry
        entry_author = soup.find('a', {'class':'entry-author'}) # find author of the entry
        while entry is not None: # iterate until entry object not None 
            data = {
                'Entry': entry.text.replace('\n','').replace('\r', '').replace('\t', '').replace('    ', ''), # clear the contents of the entry from unnecessary things
                'Date': entry_date.text,
                'Author': entry_author.text
            }
            output_entry(writer, args.output, data) # print message and write entry to file
            entry = entry.find_next('div', {'class':'content'}) # find next entry content
            entry_date = entry_date.find_next('a', {'class':'entry-date permalink'}) # find next date of the entry
            entry_author = entry_author.find_next('a', {'class':'entry-author'}) # find next author of the entry

        
        
async def main(args, last_page, writer):
    async with aiohttp.ClientSession() as session: # start request session for speed up
        tasks = [fetch(session, f'{args.url}?p={i}', writer) for i in range(1, last_page + 1)] # create tasks
        await asyncio.gather(*tasks) # wait coroutines until they complete

def page_counts(url):
    """
        Get page counts of the titles
    """
    r = requests.get(url, headers={'User-Agent':USER_AGENT})
    soup = BeautifulSoup(r.content, 'html.parser')
    try:
        last_page = soup.find('div', {'class':'pager'})['data-pagecount']
    except TypeError:
        last_page = 1
    return int(last_page)

i = 0
def output_entry(writer, output_file, data):
    """
        Prints entry data and then write it to csv file.
    """
    global i
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print(Fore.RED + f'[{dt_string}] ' + Fore.CYAN + 'INFO ' + Fore.WHITE + f'{data}' + Fore.RESET)
    i += 1
    if output_file != '':
        writer.writerow([data['Entry'], data['Date'], data['Author']])



if __name__ == '__main__':
    print(Fore.MAGENTA + LOGO) # print logo

    if args.output == '': # create file with default name if user didn't enter filename
        fp = open('eksi_scraper.csv', 'w', encoding='UTF-8', newline='')
    else:
        fp = open(f'{args.output}.csv', 'w', encoding='UTF-8', newline='')

    writer = csv.writer(fp) # create csv writer
    writer.writerow(['Entry', 'Date', 'Author']) # write csv column names

    last_page = page_counts(args.url) # get page counts of the entry
    start_time = time.time() # start time

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main(args, last_page, writer)) # run async fuction

    fp.close() # close file after finished scrape

    now = datetime.now() # current time
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S") # date and time format
    print(Fore.RED + f'[{dt_string}] ' + Fore.GREEN + 'COMPLETED ' + Fore.YELLOW + f'Scrape took {time.time() - start_time} seconds.', f'Scraped {i} entries.') # print finish message