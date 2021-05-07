import requests
from io import BytesIO
from typing import List, Optional, Tuple, Callable, Coroutine, Any

import zlib
import re

from .utils import RequestError

class SyncScraper:

    def __init__(self):
        self._line_regex = re.compile(r'(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)')
        self.cache = {}

    def _fuzzy_finder(self, query: str, collection: List[Tuple[str, str]]):
        suggestions = []
        pat   = '.*?'.join(map(re.escape, query))
        regex = re.compile(pat, flags = re.IGNORECASE)

        for k, _ in collection:
            out = regex.search(k)
            if out:
                suggestions.append((len(out.group()), out.start(), k))

        def sort_key(tup):
            return tup[0], tup[1], tup[2][0]

        return [z for _, _, z in sorted(suggestions, key=sort_key)]

    def _parse_bytes(self, data: bytes):
        decompressor = zlib.decompressobj()
        while True:
            chunk = data.read(16384)
            if len(chunk) == 0:
                break
            line = decompressor.decompress(chunk)
            yield line.decode("utf-8")

    def _split_line(self, url: str, data: str) -> None:
        
        self.cache[url] = {}
        for line in data.split("\n"):
            match = self._line_regex.match(line.rstrip())
            if not match:
                continue

            name, __, __, location, __ = match.groups()
            location = location.strip("$")

            self.cache[url][name] = url + location + name

        return self.cache[url]

    def search(self, query: str, *, page: str):

        if not self.cache.get(page):
            resp = requests.get(page + "objects.inv")
            
            if resp.ok:
                data = BytesIO(resp.content)

                for _ in range(4):
                    data.readline()

                data = "".join(self._parse_bytes(data))
                self._split_line(page, data)

                data = self._fuzzy_finder(
                    query = query, 
                    collection = list(self.cache[page].items()), 
                )
                return data

            elif resp.status_code == 404:
                raise RuntimeError("Invalid documentation url, url provided does not have an objects.inv")
            else:
                raise RequestError(f"{resp.status} {resp.reason}")
        return