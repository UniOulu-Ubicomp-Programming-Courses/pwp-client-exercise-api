import json
import os
import uuid
import pika
from jsonschema import validate, ValidationError, Draft7Validator
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import BadRequest, Conflict, NotFound, UnsupportedMediaType
from pwp_api import db, redis, rabbit
from pwp_api.constants import JSON, MASON
from pwp_api.models import cert_schema
from pwp_api.utils import require_admin, require_owner, MasonBuilder

class CertificateCollection(Resource):

    @require_owner
    def get(self, group):
        body = MasonBuilder(
            exchange="notifications",
        )
        body.add_namespace("pwpex", url_for("namespace"))
        body.add_control(
            "profile",
            url_for("profiles")
        )
        body.add_control(
            "pwpex:notify-listen",
            rabbit.uri_template,
            schema={
                "type": "object",
                "required": ["username", "password"],
                "properties": {
                    "username": {
                        "description": "RabbitMQ username given to your group by course staff",
                        "type": "string",
                    },
                    "password": {
                        "description": "RabbitMQ password given to your group by course staff",
                        "type": "string",
                    },
                    "vhost": {
                        "description": "Virtual host to connect to. Username + '-vhost'",
                        "type": "string",
                    },
                },
            },
            template=rabbit.conn_template,
            isHrefTemplate=True,
        )
        body.add_control(
            "pwpex:request-certificate",
            url_for("api.certificatecollection", group=group),
            method="POST",
        )
        body.add_control(
            "up",
            url_for("api.groupitem", group=group)
        )
        return Response(json.dumps(body), 200, mimetype=MASON)

    @require_owner
    def post(self, group):
        task = MasonBuilder(
            group=group.handle,
            salt=group.salt,
            vhost=f"{group.handle}-vhost",
        )
        token = str(uuid.uuid4())
        result_url = url_for(
            "api.certificateitem",
            group=group,
            token=token,
        )
        task.add_namespace("pwpex", url_for("namespace"))
        task.add_control(
            "pwpex:create-certificate",
            result_url,
            method="PUT",
            schema=cert_schema,
        )
        task.add_control(
            "pwpex:get-certificate",
            result_url,
        )
        rabbit.send_task(task, token)
        return Response(status=202)


class CertificateItem(Resource):

    @require_owner
    def get(self, group, token):
        try:
            value = redis.load(token)
        except Exception:
            raise NotFound
        else:
            return Response(json.dumps(value), 200, mimetype=JSON)

    @require_admin
    def put(self, group, token):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, cert_schema, cls=Draft7Validator)
        except ValidationError:
            raise BadRequest(description=str(e))

        redis.save(token, request.json, timeout=5)
        return Response(status=201)



