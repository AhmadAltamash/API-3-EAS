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

    def update_details(
        self,
        intern_id,
        name=None,
        date_joined=None,
        emails_sent=None,
        automated_responses=None,
        positive_responses=None
    ):
        """
        Direct correction of a mistake, unlike append_stats() - this
        REPLACES a field's value outright rather than adding to it.
        Only touches fields that were actually passed in (None means
        "leave this one alone"), so a partial correction (e.g. just
        fixing the name) can't accidentally zero out the others.
        """

        intern = self.get(intern_id)

        if not intern:
            return None

        if name is not None:
            intern.name = name

        if date_joined is not None:
            intern.date_joined = date_joined

        if emails_sent is not None:
            intern.emails_sent = emails_sent

        if automated_responses is not None:
            intern.automated_responses = automated_responses

        if positive_responses is not None:
            intern.positive_responses = positive_responses

        db.session.commit()

        return intern

    def discontinue(self, intern_id, date_discontinued):
        """
        Marks a team member as no longer active AS OF a specific date
        (which may be in the past, e.g. backfilling someone who left
        last week - not necessarily today). From this point on,
        Intern.total_working_days freezes as of that date instead of
        continuing to grow with today's date.
        """

        intern = self.get(intern_id)

        if not intern:
            return None

        intern.status = "Discontinued"
        intern.date_discontinued = date_discontinued

        db.session.commit()

        return intern

    def reactivate(self, intern_id):
        """
        Undoes discontinue() - back to Active, working days resume
        counting from today onward (date_discontinued cleared).
        """

        intern = self.get(intern_id)

        if not intern:
            return None

        intern.status = "Active"
        intern.date_discontinued = None

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
