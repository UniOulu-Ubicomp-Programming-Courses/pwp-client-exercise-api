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


class GroupCollection(Resource):

    def get(self):
        items = []
        groups = Group.query.all()
        for group in groups:
            item = MasonBuilder(
                name=group.name,
                handle=group.handle
            )
            item.add_control(
                "self",
                url_for("api.groupitem", group=group)
            )
            item.add_control(
                "profile",
                url_for("profiles")
            )
            items.append(item)

        body = MasonBuilder(
            items=items
        )
        body.add_namespace("pwpex", url_for("namespace"))
        return Response(json.dumps(body), mimetype=JSON)

    @require_admin
    def post(self):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, Group.json_schema(), cls=Draft7Validator)
        except ValidationError as e:
            raise BadRequest(description=str(e))

        group = Group()
        group.deserialize(request.json)
        key = ApiKey.generate()
        group.api_key = ApiKey(
            key=ApiKey.key_hash(key),
        )
        try:
            db.session.add(group)
            db.session.commit()
        except IntegrityError:
            raise Conflict(
                description=f"Group with handle {group.handle} already exists"
            )

        return Response(status=201, headers={
            "Location": url_for("api.groupitem", group=group),
            "Pwp-Api-Key": key
        })


class GroupItem(Resource):

    @require_owner
    def get(self, group):
        body = MasonBuilder(
            name=group.name,
            handle=group.handle
        )
        body.add_namespace("pwpex", url_for("namespace"))
        body.add_control(
            "profile",
            url_for("profiles")
        )
        body.add_control(
            "pwpex:certificates",
            url_for("api.groupitem", group=group)
        )
        body.add_control(
            "collection",
            url_for("api.groupcollection")
        )
        return Response(json.dumps(body), 200, mimetype=JSON)

    @require_admin
    def delete(self, group):
        db.session.delete(group)
        db.session.commit()
        return Response(status=204)






