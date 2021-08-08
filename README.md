# eksi_scraper

<img src='src/logo.png' alt='Best Logo'>

<p align='center'>
eksi_scraper scrapes asynchronous all entries in the title which given as arguments and then save them to a csv file.
<p>

# 📌 Example Usage
<img src='src/main.gif'>
  
```py
  eksi_scraper.py -u URL -o FILE_NAME
```

## ❗ Arguments
* -u, --url [reguired] <pre>URL of the title you want to scrape</pre>
* -o, --output [optional] <pre>name of the csv output file <br>Default Name: eksi_scraper</pre>

## ❗❗ Requirements
* aiohttp
* asyncio
* requests
* BeautifulSoup
* time
* sys
* colorama
* argparse
* datetime
* csv


## 📞 Contact
* <a href="mailto:uysalibov@gmail.com">
    📧 e-mail
   </a>

## ✍️ To-Do
- [ ] Supports .txt and .json output file extensions
- [ ] Scrape users entries
