from orm.models import PublishPlan


def upgrade_plan_finish(session, plan_id):
    plan = session.query(PublishPlan).filter_by(id=plan_id).one()

    plan_status = plan.status
    if plan_status < 10:
        plan.status = 4
    elif plan_status > 20 and plan_status < 30:
        plan.status = 22
    session.flush()
