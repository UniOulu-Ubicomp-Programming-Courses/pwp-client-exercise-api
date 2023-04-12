from flask import Blueprint
from flask_restful import Api
import pwp_api.views as views

from .resources.group import GroupCollection, GroupItem
from .resources.certificate import CertificateCollection, CertificateItem
from .resources.salt import SaltCollection

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

api_bp.add_url_rule("/", "entry", views.entry)
api.add_resource(GroupCollection, "/groups/")
api.add_resource(GroupItem, "/groups/<group:group>/")
api.add_resource(CertificateCollection, "/groups/<group:group>/certificates/")
api.add_resource(CertificateItem, "/groups/<group:group>/certificates/<token>/")
api.add_resource(SaltCollection, "/salts/")
