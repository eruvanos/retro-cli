import dataclasses
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from itertools import count
from json.encoder import JSONEncoder
from pathlib import Path
from typing import Dict, List, Optional, Union

from atomicwrites import atomic_write


class EnhancedJSONEncoder(JSONEncoder):
    """
    json.dumps(datetime.today(), cls=EnhancedJSONEncoder)
    """

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        elif isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


class Category:
    GOOD = "GOOD"
    NEUTRAL = "NEUTRAL"
    BAD = "BAD"


@dataclass
class Item:
    key: int
    text: str
    category: str
    done: bool = False


class RetroStore(ABC):
    @abstractmethod
    def list(self, category: Optional[str] = None) -> List[Item]:
        pass

    @abstractmethod
    def add_item(self, text: str, category: str) -> None:
        pass

    @abstractmethod
    def move_item(self, key: int, category: str) -> None:
        pass

    @abstractmethod
    def remove(self, key: int) -> None:
        pass

    @abstractmethod
    def toggle(self, key: int) -> None:
        """Changes status of item"""
        pass


class InMemoryStore(RetroStore):
    def __init__(self):
        self._items: Dict[int, Item] = {}
        self.__key_generator = count()

    # write access
    def _next_id(self) -> int:
        return next(self.__key_generator)

    def add_item(self, text: str, category: str) -> None:
        next_id = self._next_id()
        self._items[next_id] = Item(next_id, text, category)

    def move_item(self, key: int, category: str) -> None:
        if key in self._items:
            self._items[key].category = category

    def remove(self, key: int) -> None:
        if key in self._items:
            del self._items[key]

    def list(self, category: Optional[str] = None) -> List[Item]:
        if category:
            return [
                item
                for item in sorted(self._items.values(), key=lambda i: i.key)
                if item.category == category
            ]
        else:
            return [item for item in sorted(self._items.values(), key=lambda i: i.key)]

    def toggle(self, key: int) -> None:
        if key in self._items:
            self._items[key].done = not self._items[key].done


class FileStore(RetroStore):

    def __init__(self, path: Union[str, Path]):
        self._path = Path(path)

        self._path.parent.mkdir(parents=True, exist_ok=True)

        self.__key_generator = count()
        self._items: Dict[int, Item] = {}

        if self._path.exists():
            self._items = {int(k): Item(**v) for k, v in json.loads(self._path.read_text()).items()}
            while self._next_id() in self._items:
                pass

    def _next_id(self) -> int:
        return next(self.__key_generator)

    def add_item(self, text: str, category: str) -> None:
        next_id = self._next_id()
        self._items[next_id] = Item(next_id, text, category)

        self._save()

    def move_item(self, key: int, category: str) -> None:
        if key in self._items:
            self._items[key].category = category

            self._save()

    def remove(self, key: int) -> None:
        if key in self._items:
            del self._items[key]

        self._save()

    def list(self, category: Optional[str] = None) -> List[Item]:
        if category:
            return [
                item
                for item in sorted(self._items.values(), key=lambda i: i.key)
                if item.category == category
            ]
        else:
            return [item for item in sorted(self._items.values(), key=lambda i: i.key)]

    def toggle(self, key: int) -> None:
        if key in self._items:
            self._items[key].done = not self._items[key].done

            self._save()

    def _save(self):
        # TODO FIXME Item not serializable
        with atomic_write(self._path, overwrite=True) as f:
            json.dump(self._items, f, cls=EnhancedJSONEncoder)
