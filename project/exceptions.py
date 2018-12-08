from flask import jsonify
from marshmallow.exceptions import ValidationError

class InvalidRequest(Exception):
    status_code = 400
    type = 'InvalidRequest'

    def __init__(self, message, status_code = None, type = None, payload = None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if type is not None:
            self.type = type
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

class ValidationApiError(InvalidRequest):
    def __init__(self, message, status_code = None, type = None, payload = None):
        super().__init__(message, status_code, type, payload)
        if len(payload) > 0 :
            self.payload = {'errors': []}
            errors = list()
            for k, v in payload.items():
                errors.append({'field': k, 'message': v})
            self.payload['errors'].extend(errors)
