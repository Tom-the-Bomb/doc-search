from io import BytesIO
from typing import List, Optional, Tuple, Callable
from asyncio import get_event_loop, AbstractEventLoop
from aiohttp import ClientSession

from .utils import executor, RequestError
from .sync_docs import SyncScraper

class AsyncScraper(SyncScraper):

    def __init__(self,
        loop : Optional[AbstractEventLoop] = None, 
        session: Optional[ClientSession]   = None,
    ):
        super().__init__()

        if loop:
            self.loop = loop
        else:
            self.loop = get_event_loop()

        if session:
            self.session = session
        
    @executor()
    def _fuzzy_finder(self, *args, **kwargs):
        return super()._fuzzy_finder(*args, **kwargs)

    @executor()
    def _parse_bytes(self, data: bytes):
        yield from super()._parse_bytes(data)

    @executor()
    def _split_line(self, url: str, data: str) -> None:
        return super()._split_line(url, data)

    async def search(self, query: str, *, page: str):

        if not hasattr(self, "session"):
            self.session = ClientSession()

        if not self.cache.get(page):
            async with self.session.get(page + "objects.inv") as r:

                if r.ok:
                    data = BytesIO(await r.read())

                    for _ in range(4):
                        data.readline()

                    data = "".join(await self._parse_bytes(data))
                    await self._split_line(page, data)

                elif r.status == 404:
                    raise RuntimeError("Invalid documentation url, url provided does not have an objects.inv")
                else:
                    raise RequestError(f"{r.status} {r.reason}")

        data = await self._fuzzy_finder(
            query = query, 
            collection = list(self.cache[page].items()), 
        )
        return data