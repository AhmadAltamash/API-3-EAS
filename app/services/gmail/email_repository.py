from app.extensions import db
from app.models import EmailLog


class EmailRepository:

    def save(
        self,
        buyer
        ,
        subject,
        body,
        status
    ):

        log = EmailLog(

            buyer_id=buyer.id,

            company=buyer.company,

            receiver=buyer.email,

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