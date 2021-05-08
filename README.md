# Doc-search
A simple package for searching documentation

**Features**
- Both async and sync support
- utilizes a cache to limit the number of requests being made
- works for any documentation that is built with sphinx

### Example

**asyncio**
```py
import asyncio
from doc_search import AsyncScraper

scraper = AsyncScraper()

async def main(query):
    results = await scraper.search(query, page="https://docs.python.org/3/")
    #returns a list of tuples in the format of [(item, url), (item, url)...]
    if not results:
        print("no results were found")
    else:
        for item, url in results:    #loop through the list of results
            print(f"{item} | {url}") #print out each result

asyncio.run(main("str.split"))

# to view the cache
# print(scraper.cache)
```

**sync**
```py
from doc_search import SyncScraper

scraper = SyncScraper()
results = scraper.search("resize", page="https://pillow.readthedocs.io/en/stable/")
if not results:
    print("no results were found")
else:
    for item, url in results:    #loop through the list of results
        print(f"{item} | {url}") #print out each result
```

### Beta

- Offers searches for **C** and **C++** docs using the `scraper.search_c` and `scraper.search_cpp` methods
    **EX:** 
    ```py
    scraper = SyncScraper()
    results = scraper.search_c("printf")
    ```