import click
import hashlib
from flask.cli import with_appcontext
from pwp_api import db
from pwp_api.models import ApiKey, Group


@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()

@click.command("testgen")
@with_appcontext
def generate_test_data():
    testgroup = Group(
        handle="test-ex",
        name="Test Group",
        salt="456"
    )
    key = ApiKey(
        key=ApiKey.key_hash("not-very-safe-key"),
        group=testgroup
    )
    db.session.add(key)
    db.session.commit()

@click.command("clear-groups")
@with_appcontext
def clear_groups():
    Group.query.delete()
    ApiKey.query.filter_by(admin=False).delete()
    db.session.commit()


@click.command("masterkey")
@with_appcontext
def generate_master_key():
    import secrets
    token = secrets.token_urlsafe()
    db_key = ApiKey(
        key=ApiKey.key_hash(token),
        admin=True
    )
    db.session.add(db_key)
    db.session.commit()
    print(token)


