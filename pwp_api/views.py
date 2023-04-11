import json
from flask import Response, url_for, send_from_directory
from pwp_api.utils import MasonBuilder
from pwp_api.constants import JSON, MASON

def link_relations():
    return send_from_directory("static", "linkrels.html")

def profiles():
    return send_from_directory("static", "profiles.html")

def entry():
    body = MasonBuilder()
    body.add_namespace("pwpex", url_for("namespace", _external=True))
    body.add_control(
        "pwpex:groups",
        url_for("api.groupcollection", _external=True)
    )
    return Response(json.dumps(body), 200, mimetype=MASON)
