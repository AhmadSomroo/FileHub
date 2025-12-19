"""
Usage: python scripts/create_dummy_users.py
Make sure FLASK app can import app package (run from repo root)
"""


import sys
import os

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app import create_app, db
from app.models import User

from app import create_app, db
from app.models import User, RoleEnum
import random
import string

def randpass(n=10):
    return ''.join(random.choices(string.ascii_letters+string.digits, k=n))

app = create_app()
with app.app_context():
    db.create_all()
    created = []
    # admin
    if not User.query.filter_by(username="admin").first():
        u = User(username="admin", role=RoleEnum.admin)
        p = "AdminTempPass123!"
        u.set_password(p)
        u.first_login = True
        db.session.add(u)
        created.append(("admin", p, "admin"))

    # staff
    if not User.query.filter_by(username="staff1").first():
        u = User(username="staff1", role=RoleEnum.staff)
        p = randpass()
        u.set_password(p)
        u.first_login = True
        db.session.add(u)
        created.append(("staff1", p, "staff"))

    # teachers
    for i in range(1,4):
        uname = "teacher{}".format(i)
        if not User.query.filter_by(username=uname).first():
            u = User(username=uname, role=RoleEnum.teacher)
            p = randpass()
            u.set_password(p)
            u.first_login = True
            db.session.add(u)
            created.append((uname, p, "teacher"))

    # students 15
    for i in range(1,16):
        uname = "student{}".format(i)
        if not User.query.filter_by(username=uname).first():
            u = User(username=uname, role=RoleEnum.student)
            p = randpass()
            u.set_password(p)
            u.first_login = True
            db.session.add(u)
            created.append((uname, p, "student"))

    db.session.commit()
    print("Created users (username, password, role):")
    for c in created:
        print(c)
