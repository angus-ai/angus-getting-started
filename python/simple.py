#!/usr/bin/env python
import angus
import json

conn = angus.connect()
service = conn.services.get_service('age_and_gender_estimation', version=1)
job = service.process({'image': open("./images/macgyver.jpg")})
print json.dumps(job.result, indent=4)
