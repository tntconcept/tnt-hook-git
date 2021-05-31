import unittest
from TNTGitHook.hook import parse_activities
from TNTGitHook.utils import DateTimeEncoder, OrganizationListDecoder, to_class
from datetime import datetime
from typing import List
from TNTGitHook.entities import ActivitiesResponse, Activity


class UtilsTestCase(unittest.TestCase):

    encoder = DateTimeEncoder()

    def test_date_time_encoder_datetime_object(self):
        dt = datetime.strptime("2021-05-24T14:12:21.292495", "%Y-%m-%dT%H:%M:%S.%f")
        result = self.encoder.default(dt)
        self.assertEqual("2021-05-24T14:12:21.292495", result)

    def test_parse_full_activities_data(self):
        activities_response: List[ActivitiesResponse]
        with open('example_activities') as example_activities:
            data = example_activities.read()
        parsed_activities = parse_activities(data)
        expected_id = [250112, 250199, 250113, 250262, 250263]
        for activity in parsed_activities:
            self.assertEqual(expected_id.pop(0), activity.id)
            self.assertIsNotNone(activity.startDate)
            self.assertIsNotNone(activity.duration)
            self.assertIsNotNone(activity.description)
            self.assertIsNotNone(activity.project)
            self.assertIsNotNone(activity.organization)
            self.assertIsNotNone(activity.projectRole)


if __name__ == '__main__':
    unittest.main()
