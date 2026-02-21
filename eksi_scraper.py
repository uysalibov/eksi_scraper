import aiohttp
import asyncio
import requests
from bs4 import BeautifulSoup
import time
import sys
from colorama import init, Fore
from constant import *
import argparse
from datetime import datetime
import csv
import json
import urllib.parse
import os

init()

parser = argparse.ArgumentParser()
parser.add_argument('-u', '--url', type=str, required=True, help='URL of the topic or user profile you want to scrape')
parser.add_argument('-o', '--output', type=str, required=False, default='', help='Name of the output file (without extension). Auto-determined if left blank.')
parser.add_argument('--format', type=str, choices=['json', 'csv', 'txt'], default='json', help='Output format: json (default), csv, or txt')
parser.add_argument('--sort', type=str, choices=['date', 'sukela'], default='date', help='Sort topic entries by date or sukela (topic only)')

args = parser.parse_args()

all_data = []
total_entries = 0

def extract_text_with_links(content_div):
    # Mutates the soup in-place to append URLs to anchor tag texts
    for a in content_div.find_all('a'):
        if a.has_attr('href'):
            href = a['href']
            if href.startswith('/'):
                href = f"https://eksisozluk.com{href}"
            a.replace_with(f"{a.text} ({href})")
    return content_div.text.replace('\n',' ').replace('\r', '').replace('\t', ' ').strip()

async def fetch_topic_page(session, url, semaphore):
    global total_entries
    async with semaphore:
        async with session.get(url, headers={'User-Agent':USER_AGENT}) as resp: 
            text_resp = await resp.text()
            soup = BeautifulSoup(text_resp, 'html.parser')

            page_data = []
            entry = soup.find('div', {'class':'content'})
            entry_date = soup.find('a', {'class':'entry-date permalink'})
            entry_author = soup.find('a', {'class':'entry-author'})
            while entry is not None:
                data = {
                    'Entry': extract_text_with_links(entry),
                    'Date': entry_date.text.strip(),
                    'Author': entry_author.text.strip()
                }
                page_data.append(data)
                total_entries += 1
                
                entry = entry.find_next('div', {'class':'content'})
                entry_date = entry_date.find_next('a', {'class':'entry-date permalink'})
                entry_author = entry_author.find_next('a', {'class':'entry-author'})
            return page_data

async def fetch_user_page(session, url, semaphore, max_retries=3):
    global total_entries
    for attempt in range(max_retries):
        try:
            async with semaphore:
                async with session.get(url, headers={'User-Agent':USER_AGENT, 'X-Requested-With': 'XMLHttpRequest'}, timeout=15) as resp:
                    if resp.status != 200:
                        await asyncio.sleep(2)
                        continue
                    
                    text_resp = await resp.text()
                    soup = BeautifulSoup(text_resp, 'html.parser')
                    
                    topics = soup.find_all('div', {'class': 'topic-item'})
                    page_data = []
                    
                    entries_found = 0
                    for topic in topics:
                        title_elem = topic.find('h1', id='title')
                        topic_title = title_elem.text.strip() if title_elem else "Unknown Topic"
                        
                        entry_item = topic.find('li')
                        entry_content = entry_item.find('div', {'class': 'content'})
                        entry_date_elem = entry_item.find('a', {'class': 'entry-date permalink'})
                        
                        if entry_content and entry_date_elem:
                            data = {
                                'Topic': topic_title,
                                'Entry': extract_text_with_links(entry_content),
                                'Date': entry_date_elem.text.strip()
                            }
                            page_data.append(data)
                            total_entries += 1
                            entries_found += 1
                    
                    return page_data
        except Exception as e:
            await asyncio.sleep(2)
    return []


async def main(args, last_page, is_user_profile):
    semaphore = asyncio.Semaphore(3) # Limit concurrency to 3
    async with aiohttp.ClientSession() as session:
        if is_user_profile:
            parsed_url = urllib.parse.urlparse(args.url)
            path_parts = parsed_url.path.strip('/').split('/')
            username = path_parts[-1]
            base_api_url = f"https://eksisozluk.com/son-entryleri?nick={username}"
            tasks = [fetch_user_page(session, f'{base_api_url}&p={i}', semaphore) for i in range(1, last_page + 1)]
        else:
            base_topic_url = args.url.split("?")[0]
            if args.sort == 'sukela':
                tasks = [fetch_topic_page(session, f'{base_topic_url}?a=nice&p={i}', semaphore) for i in range(1, last_page + 1)]
            else:
                tasks = [fetch_topic_page(session, f'{base_topic_url}?p={i}', semaphore) for i in range(1, last_page + 1)]
            
        results = await asyncio.gather(*tasks)
        for page_data in results:
            if page_data:
                all_data.extend(page_data)

def parse_url_info(url, sort_pref):
    """
    Determines if URL is a topic or user profile, gets page counts and auto-filename.
    """
    parsed_url = urllib.parse.urlparse(url)
    path_parts = parsed_url.path.strip('/').split('/')
    is_user_profile = 'biri' in path_parts

    if not is_user_profile and sort_pref == 'sukela':
        fetch_url = f'{url.split("?")[0]}?a=nice'
    else:
        fetch_url = url
        
    r = requests.get(fetch_url, headers={'User-Agent':USER_AGENT})
    soup = BeautifulSoup(r.content, 'html.parser')
    
    last_page = 1
    filename = "eksi_scraper"

    if is_user_profile:
        username = path_parts[-1]
        filename = username
        
        # User profiles do not use a standard pager on their son-entryleri API response.
        # Instead, we get the total entry count from the profile page.
        entry_count_span = soup.find(id='entry-count-total')
        if entry_count_span:
            import math
            total_user_entries = int(entry_count_span.text.strip().replace('.','').replace(',',''))
            last_page = math.ceil(total_user_entries / 10)
    else:
        title_elem = soup.find('h1', id='title')
        if title_elem:
            filename = title_elem['data-slug'] if title_elem.has_attr('data-slug') else title_elem.text.strip()
            # Clean filename
            filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c=='-'][-100:]).strip('-')
            
        pager = soup.find('div', {'class':'pager'})
        if pager and pager.has_attr('data-pagecount'):
            last_page = int(pager['data-pagecount'])
            
    return is_user_profile, last_page, filename

if __name__ == '__main__':
    print(Fore.MAGENTA + LOGO) # print logo

    is_user_profile, last_page, auto_filename = parse_url_info(args.url, args.sort)
    
    if args.output == '':
        output_name = auto_filename
    else:
        output_name = args.output
        
    if args.sort == 'sukela' and not is_user_profile:
        output_name += '-sukela'
        
    start_time = time.time()

    if sys.platform == 'win32':
         asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main(args, last_page, is_user_profile))

    # Ensure downloads directory exists
    os.makedirs('downloads', exist_ok=True)
    
    # Sort all_data by creation date (newest to oldest)
    def parse_date(date_str):
        first_date_str = date_str.split('~')[0].strip()
        try:
            return datetime.strptime(first_date_str, "%d.%m.%Y %H:%M")
        except ValueError:
            try:
                return datetime.strptime(first_date_str, "%d.%m.%Y")
            except ValueError:
                return datetime.min

    if args.sort == 'date':
        all_data.sort(key=lambda x: parse_date(x['Date']), reverse=True)

    # Output Data
    output_file = os.path.join('downloads', f'{output_name}.{args.format}')
    if args.format == 'json':
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)
    elif args.format == 'txt':
        with open(output_file, 'w', encoding='utf-8') as f:
            for d in all_data:
                if is_user_profile:
                    f.write(f"Topic: {d['Topic']}\n")
                    f.write(f"Entry: {d['Entry']}\n")
                    f.write(f"Date: {d['Date']}\n")
                else:
                    f.write(f"Author: {d['Author']}\n")
                    f.write(f"Entry: {d['Entry']}\n")
                    f.write(f"Date: {d['Date']}\n")
                f.write("-" * 50 + "\n")
    else:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            if is_user_profile:
                writer.writerow(['Topic', 'Entry', 'Date'])
                for d in all_data:
                    writer.writerow([d['Topic'], d['Entry'], d['Date']])
            else:
                writer.writerow(['Entry', 'Date', 'Author'])
                for d in all_data:
                    writer.writerow([d['Entry'], d['Date'], d['Author']])
                    
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print(Fore.RED + f'[{dt_string}] ' + Fore.GREEN + 'COMPLETED ' + Fore.YELLOW + f'Scrape took {time.time() - start_time:.2f} seconds.', f'Scraped {total_entries} entries.')
    print(Fore.YELLOW + f'Saved to {output_file}' + Fore.RESET)