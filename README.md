# eksi_scraper

<img src='src/logo.png' alt='Best Logo'>

<p align='center'>
eksi_scraper asynchronously scrapes all entries in the topic or user profile given as arguments and then chronologically saves them to a `downloads` directory.
<p>

# 📌 Example Usage
<img src='src/main.gif'>
  
```py
  eksi_scraper.py -u URL -o FILE_NAME
```

## ❗ Arguments
* -u, --url [required] <pre>URL of the topic or user profile you want to scrape</pre>
* -o, --output [optional] <pre>name of the output file <br>Default Name: Auto-generated from topic name or username</pre>
* --format [optional] <pre>Output format (json, csv, or txt) <br>Default: json</pre>
* --sort [optional] <pre>Sort topic entries by (date or sukela) <br>Default: date</pre>

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
- [x] Supports .json and .txt output file extensions natively
- [x] Scrape users entries and auto-generate filenames
