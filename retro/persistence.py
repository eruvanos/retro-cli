from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import count
from typing import Dict, List, Optional


class Category:
    GOOD = 'GOOD'
    NEUTRAL = 'NEUTRAL'
    BAD = 'BAD'


@dataclass
class Item:
    key: int
    text: str
    category: str


class RetroStore(ABC):
    @abstractmethod
    def list(self, category: Optional[str] = None):
        pass

    @abstractmethod
    def add_item(self, text: str, category: str):
        pass

    @abstractmethod
    def move_item(self, key: int, category: str):
        pass

    @abstractmethod
    def remove(self, key: int):
        pass


class InMemoryStore(RetroStore):
    def __init__(self):
        self._items: Dict[int, Item] = {}
        self._listeners = []
        self.__key_generator = count()

    # write access
    def next_id(self):
        return next(self.__key_generator)

    def add_item(self, text: str, category: str):
        next_id = self.next_id()
        self._items[next_id] = Item(next_id, text, category)

    def move_item(self, key: int, category: str):
        self._items[key].category = category

    def remove(self, key: int):
        if key in self._items:
            del self._items[key]

    def list(self, category: Optional[str] = None) -> List[Item]:
        if category:
            return [item for item in sorted(self._items.values(), key=lambda i: i.key) if item.category == category]
        else:
            return [item for item in sorted(self._items.values(), key=lambda i: i.key)]
