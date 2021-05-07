from io import BytesIO
from typing import List, Optional, Tuple, Callable, Coroutine, Any
from asyncio import get_event_loop, AbstractEventLoop
from aiohttp import ClientSession

import zlib
import re
import functools

def executor(loop = None, executor = None):

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            partial = functools.partial(func, *args, **kwargs)
            loop = asyncio.get_running_loop()
            return loop.run_in_executor(executor, partial)

        return wrapper
    return decorator

class AsyncScraper:

    def __init__(self,
        pages: Optional[List[str]] = [],
        loop : Optional[AbstractEventLoop] = None, 
        session: Optional[ClientSession] = None
    ):
        self._line_regex = re.compile(r'(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)')
        self.cache = {}

        if loop:
            self.loop = loop
        else:
            self.loop = get_event_loop()

        if session:
            self.session = session
        
    @executor()
    def _fuzzy_finder(self, query: str, collection: List[Tuple[str, str]], *, key: Callable = None):
        suggestions = []
        pat   = '.*?'.join(map(re.escape, query))
        regex = re.compile(pat, flags = re.IGNORECASE)

        for item in collection:
            to_search = key(item) if key else item
            out = regex.search(to_search)
            if out:
                suggestions.append((len(out.group()), out.start(), item))

        def sort_key(tup):
            if key:
                return tup[0], tup[1], key(tup[2])
            return tup

        return [z for _, _, z in sorted(suggestions, key=sort_key)]

    @executor()
    def _parse_bytes(self, data: bytes):
        decompressor = zlib.decompressobj()
        while True:
            chunk = data.read(16 * 1024)
            if len(chunk) == 0:
                break
            line = decompressor.decompress(chunk)
            yield line.decode("utf-8")

    @executor()
    def _split_line(self, url: str, data: str) -> None:
        
        self.cache[url] = {}
        for line in data.split("\n"):
            match = self._line_regex.match(line.rstrip())
            if not match:
                continue

            name, __, __, location, __ = match.groups()
            location = location.strip("$")

            self.cache[url][name] = url + location + name

    async def search(self, query: str, *, page: str):

        if not hasattr(self, "session"):
            self.session = ClientSession()

        if not self.cache.get(page):
            async with self.session.get(page + "objects.inv") as r:
                data = BytesIO(await r.read())

            for _ in range(4):
                data.readline()

            data = "".join(await self._parse_bytes(data))
            await self._split_line(page, data)

        data = await self._fuzzy_finder(
            query = query, 
            collection = list(self.cache[page].items()), 
            key   = lambda t: t[0]
        )

        return data