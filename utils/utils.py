import uuid
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import BoundFilter
from typing import List, Union
import hashlib, re
import asyncio

P_R_HTML = re.compile("<[p].*?>")
REMOVE_HTML = re.compile("<[^>]*>")

class MimeTypeFilter(BoundFilter):
    """
    Check document mime_type
    """

    key = "mime_type"

    def __init__(self, mime_type: Union[str, List[str]]):
        if isinstance(mime_type, str):
            self.mime_types = [mime_type]

        elif isinstance(mime_type, list):
            self.mime_types = mime_type

        else:
            raise ValueError(
                f"filter mime_types must be a str or list of str, not {type(mime_type).__name__}"
            )

    async def check(self, obj: types.Message):
        if not obj.document:
            return False

        if obj.document.mime_type in self.mime_types:
            return True

        return False




async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


def string_to_uuid(content: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, content))


def get_hash(content: str) -> str:
    return hashlib.md5(content.lower().encode()).hexdigest()


def remove_html_p(content: str) -> str:
    return re.sub(P_R_HTML, "", content).replace("</p>", "")

def remove_html(content: str) -> str:
    return re.sub(REMOVE_HTML, "", content)




class ConcurrentLocker:
    _instance = None
    lock = None
    
    def __new__(cls, *args, **kwargs):
        if not ConcurrentLocker._instance:
            ConcurrentLocker.lock = asyncio.Lock()
            ConcurrentLocker._instance = super(ConcurrentLocker, \
               cls).__new__(cls, *args, **kwargs)
        return ConcurrentLocker._instance

    def is_locked(self) -> bool:
        return ConcurrentLocker.lock.locked()

async def locker() -> ConcurrentLocker:
    try:
        c = ConcurrentLocker()
        while c.is_locked():
            await asyncio.sleep(0)
        yield c
    except Exception as e:
        pass