from .data import User, db
from datetime import datetime

def delete_expired_users(app):
    print("Running scheduled task: delete_expired_users")
    with app.app_context():
        expired_users = User.query.filter(User.expired_at <= datetime.now()).all()
        for user in expired_users:
            db.session.delete(user)
        db.session.commit()
