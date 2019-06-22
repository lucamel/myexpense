from .. import db
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from ..exceptions import InvalidRequest, ValidationApiError
from marshmallow.exceptions import ValidationError

class ModelMixin(object):
    filters = []

    @classmethod
    def create(cls, **kw):
        obj = cls(**kw)
        db.session.add(obj)
        db.session.flush()
        db.session.commit()
        return obj
    
    @classmethod
    def save(cls, data, schema):
        try:
            schema(strict=True).validate(data)
        except ValidationError as err:
            raise ValidationApiError('Invalid data', 422, type = err.__class__.__name__ , payload = err.messages)
        except TypeError as err:
            raise InvalidRequest('Invalid data', 422, type = err.__class__.__name__ , payload = {"error":"Invalid type error."})
        return cls.create(**data)

    @classmethod
    def delete(cls, data):
        db.session.delete(data)
        db.session.commit()

    def update(self, data):
        for k, v in data.items():
            setattr(self, k, v)
        db.session.commit()

    @classmethod
    def filter(cls, args, query = None):
        if query is None:
            query = cls.query
        for filter in cls.filters:
            if(args.get(filter) is not None):
                values = args.get(filter).split(',')
                f = []
                if len(values) > 1:
                    for v in values:
                        f.append(cls.__dict__[filter] == v)
                    query = query.filter(or_(*f))
                else:
                    query = query.filter_by(**{filter:values[0]})
        return query