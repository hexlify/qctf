import base64
import json
import os
from dataclasses import dataclass, field, asdict
from json import JSONDecodeError
from pathlib import Path
from traceback import print_exc
from typing import List


class DbModel:
    def __init__(self):
        self._db = None

    def connect(self, db):
        self._db = db

    def disconnect(self):
        self._db = None

    def save(self):
        if self._db:
            self._db.save()
        else:
            raise Exception('Not connected to db.')


@dataclass
class User(DbModel):
    username: str
    password_hash: str
    id: int = None


@dataclass
class Note(DbModel):
    owner_id: int
    title: str = ''
    text: str = ''
    tags: List[str] = field(default_factory=list)
    id: int = None


class DbQuery:
    def __init__(self, models):
        self._models = models

    def first(self):
        return self._models[0] if self._models else None

    def all(self):
        return self._models

    def filter(self, **fields):
        return DbQuery([
            model for model in self._models
            if all(
                getattr(model, field) == value
                for field, value in fields.items()
            )
        ])


class DB:
    def __init__(self):
        self._models = {}
        os.makedirs(self._base_path, exist_ok=True)

    def load(self):
        for model_type in DbModel.__subclasses__():
            try:
                self._load_models(model_type)
            except (FileNotFoundError, JSONDecodeError):
                pass
            except Exception:
                print_exc()

    def add(self, model):
        if not model.id:
            model.id = self._max_id(type(model)) + 1
        self._models.setdefault(type(model), [])
        self._models[type(model)].append(model)
        model.connect(self)
        self.save()

    def query(self, model_type):
        return DbQuery(self._models.get(model_type, []))

    def remove(self, model):
        self._models[type(model)].remove(model)
        model.disconnect()
        self.save()

    def save(self):
        for model_type, models in self._models.items():
            filename = self._get_models_path(model_type)
            serialized_models = [
                base64.b64encode(json.dumps(asdict(model)).encode())
                for model in models
            ]
            Path(filename).write_bytes(b'\n'.join(serialized_models))

    def _load_models(self, model_type):
        file_content = Path(self._get_models_path(model_type)).read_bytes()
        serialized_models = file_content.split(b'\n')

        self._models[model_type] = []

        for serialized_model in serialized_models:
            if not serialized_model.strip():
                continue
            model = model_type(**json.loads(base64.b64decode(serialized_model)))
            self._models[model_type].append(model)

        for model in self._models[model_type]:
            model.connect(self)

    def _get_models_path(self, model_type):
        return os.path.join(self._base_path, model_type.__name__)

    @property
    def _base_path(self):
        return os.path.join('.', 'data')

    def _max_id(self, model_type):
        if model_type in self._models:
            return max(model.id for model in self._models[model_type])
        return 0


db = DB()
