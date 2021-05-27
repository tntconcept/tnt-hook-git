from datetime import datetime


class Organization:
    id: int
    name: str

    def with_id(self, id: int):
        self.id = id
        return self

    def with_name(self, name: str):
        self.name = name
        return self


class Project:
    id: int
    name: str
    open: bool
    billable: bool

    def with_id(self, id: int):
        self.id = id
        return self

    def with_name(self, name: str):
        self.name = name
        return self

    def with_open(self, open: bool):
        self.open = open
        return self

    def with_billable(self, billable):
        self.billable = billable
        return self


class Role:
    id: int
    name: str

    def with_id(self, id: int):
        self.id = id
        return self

    def with_name(self, name: str):
        self.name = name
        return self


class Activity:
    id: int
    startDate: datetime
    duration: int
    description: str
    billable: bool
    organization: Organization
    project: Project
    projectRole: Role

    def with_id(self, id):
        self.id = id
        return self

    def with_startDate(self, start_date):
        self.startDate = start_date
        return self

    def with_duration(self, duration):
        self.duration = duration
        return self

    def with_description(self, description):
        self.description = description
        return self

    def with_billable(self, billable):
        self.billable = billable
        return self

    def with_organization(self, organization):
        self.organization = organization
        return self

    def with_project(self, project):
        self.project = project
        return self

    def with_projectRole(self, projectRole):
        self.projectRole = projectRole
        return self


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
