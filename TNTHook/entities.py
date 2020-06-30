from datetime import datetime


class Organization:
    id: int
    name: str


class Project:
    id: int
    name: str
    open: bool
    billable: bool


class Role:
    id: int
    name: str


class Activity:
    id: int
    startDate: datetime
    duration: int
    description: str
    billable: bool
    organization: Organization
    project: Project
    role: Role


class ActivitiesResponse:
    date: datetime
    activities: [Activity]


class CreateActivityRequest:
    id: int
    startDate: datetime
    duration: int
    description: str
    billable: bool
    projectRoleId: int
