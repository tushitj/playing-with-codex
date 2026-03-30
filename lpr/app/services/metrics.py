from collections import defaultdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import DriveThruVisit, Stage, StageEvent
from ..schemas import MetricsOut


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


class MetricsService:
    def __init__(self, db: Session):
        self.db = db

    def summary(self, start: datetime | None, end: datetime | None) -> MetricsOut:
        query = select(DriveThruVisit)
        if start:
            query = query.where(DriveThruVisit.started_at >= start)
        if end:
            query = query.where(DriveThruVisit.started_at <= end)

        visits = self.db.scalars(query).all()
        visit_ids = [v.id for v in visits]

        if not visit_ids:
            return MetricsOut(
                total_visits=0,
                completed_visits=0,
                avg_total_seconds=None,
                avg_entry_to_menu_seconds=None,
                avg_menu_to_pickup_seconds=None,
                avg_pickup_to_exit_seconds=None,
            )

        events = self.db.scalars(select(StageEvent).where(StageEvent.visit_id.in_(visit_ids))).all()
        by_visit: dict[int, dict[Stage, datetime]] = defaultdict(dict)
        for event in events:
            by_visit[event.visit_id][event.stage] = event.event_time

        completed = 0
        total_times: list[float] = []
        entry_to_menu: list[float] = []
        menu_to_pickup: list[float] = []
        pickup_to_exit: list[float] = []

        for visit in visits:
            stages = by_visit.get(visit.id, {})
            if visit.exited_at is not None:
                completed += 1
                total_times.append((visit.exited_at - visit.started_at).total_seconds())

            if Stage.entry in stages and Stage.menu in stages:
                entry_to_menu.append((stages[Stage.menu] - stages[Stage.entry]).total_seconds())
            if Stage.menu in stages and Stage.pickup in stages:
                menu_to_pickup.append((stages[Stage.pickup] - stages[Stage.menu]).total_seconds())
            if Stage.pickup in stages and Stage.exit in stages:
                pickup_to_exit.append((stages[Stage.exit] - stages[Stage.pickup]).total_seconds())

        return MetricsOut(
            total_visits=len(visits),
            completed_visits=completed,
            avg_total_seconds=_mean(total_times),
            avg_entry_to_menu_seconds=_mean(entry_to_menu),
            avg_menu_to_pickup_seconds=_mean(menu_to_pickup),
            avg_pickup_to_exit_seconds=_mean(pickup_to_exit),
        )
