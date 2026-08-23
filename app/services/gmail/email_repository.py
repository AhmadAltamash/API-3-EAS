from app.extensions import db
from app.models import EmailLog


class EmailRepository:

    def save(
        self,
        buyer,
        subject,
        body,
        status
    ):

        log = EmailLog(
            buyer_id=buyer.id,
            company=buyer.company,
            receiver=buyer.email,
            website=buyer.website,   # <- this line needs to be here
            subject=subject,
            body=body,
            status=status
        )

        db.session.add(log)

        db.session.commit()


    def all(self):

        return EmailLog.query.order_by(
            EmailLog.sent_at.desc()
        ).all()

    def sent_paginated(self, page=1, per_page=15):
        """
        Returns a Flask-SQLAlchemy Pagination object of successfully
        sent emails, most recent first - used by the Sent Companies page.
        """

        return EmailLog.query.filter_by(
            status="Sent"
        ).order_by(
            EmailLog.sent_at.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )