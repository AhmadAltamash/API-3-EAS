from datetime import datetime

from app.extensions import db
from app.models import Intern


class InternRepository:

    def all(self):

        return Intern.query.order_by(
            Intern.date_joined.desc()
        ).all()

    def get(self, intern_id):

        return Intern.query.get(intern_id)

    def create(self, name, date_joined, status="Active"):

        intern = Intern(
            name=name,
            date_joined=date_joined,
            status=status,
            emails_sent=0,
            automated_responses=0,
            positive_responses=0
        )

        db.session.add(intern)
        db.session.commit()

        return intern

    def append_stats(self, intern_id, emails=0, automated=0, positive=0):
        """
        ADDS today's numbers on top of the running totals - e.g. if
        emails_sent is already 40 and this is called with emails=8,
        it becomes 48, never replaced with 8. This is the whole point
        of this method versus a plain update - a lead re-entering
        today's numbers should never be able to accidentally erase
        yesterday's.
        """

        intern = self.get(intern_id)

        if not intern:
            return None

        intern.emails_sent = (intern.emails_sent or 0) + emails
        intern.automated_responses = (intern.automated_responses or 0) + automated
        intern.positive_responses = (intern.positive_responses or 0) + positive

        db.session.commit()

        return intern

    def set_status(self, intern_id, status):

        intern = self.get(intern_id)

        if not intern:
            return None

        intern.status = status

        db.session.commit()

        return intern

    def delete(self, intern_id):

        intern = self.get(intern_id)

        if intern:
            db.session.delete(intern)
            db.session.commit()

    def totals(self):
        """
        Aggregate numbers across the whole team - used by the
        dashboard chart.
        """

        interns = self.all()

        return {
            "emails_sent": sum(i.emails_sent or 0 for i in interns),
            "automated_responses": sum(i.automated_responses or 0 for i in interns),
            "positive_responses": sum(i.positive_responses or 0 for i in interns),
            "active_count": sum(1 for i in interns if i.status == "Active"),
            "inactive_count": sum(1 for i in interns if i.status != "Active"),
        }
