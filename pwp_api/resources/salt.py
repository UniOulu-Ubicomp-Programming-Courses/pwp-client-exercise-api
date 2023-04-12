import json
from jsonschema import validate, ValidationError, Draft7Validator
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, UnsupportedMediaType
from pwp_api import db
from pwp_api.constants import JSON, MASON
from pwp_api.models import Group, ApiKey
from pwp_api.utils import require_admin, require_owner, MasonBuilder

class SaltCollection(Resource):

    @require_admin
    def get(self):
        body = {}
        groups = Group.query.all()
        for group in groups:
            body[group.handle] = group.salt

        return Response(json.dumps(body), 200, mimetype=JSON)

