# -*- coding: utf-8 -*-
import cv2
import numpy as np
import StringIO
from math import sin,cos
import datetime
import pytz
import angus


def f(stream_index):

    camera = cv2.VideoCapture(stream_index)
    camera.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.cv.CV_CAP_PROP_FPS, 10)

    if not camera.isOpened():
        print("Cannot open stream of index {}".format(stream_index))
        exit(1)

    print("Video stream is of resolution {} x {}".format(camera.get(3), camera.get(4)))

    conn = angus.connect()
    service = conn.services.get_service("scene_analysis", version=1)
    service.enable_session()

    while camera.isOpened():
        ret, frame = camera.read()

        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret, buff = cv2.imencode(".jpg", gray,  [cv2.IMWRITE_JPEG_QUALITY, 80])
        buff = StringIO.StringIO(np.array(buff).tostring())

        t = datetime.datetime.now(pytz.utc)
        job = service.process({"image": buff,
                               "timestamp" : t.isoformat(),
                               "camera_position": "facing",
                               "sensitivity": {
                                   "appearance": 0.7,
                                   "disappearance": 0.7,
                                   "age_estimated": 0.4,
                                   "gender_estimated": 0.5,
                                   "focus_locked": 0.9,
                                   "emotion_detected": 0.4,
                                   "direction_estimated": 0.8
                               }
        })

        res = job.result

        for idx, entity in res['entities'].iteritems():
            x, y, dx, dy = entity['face_roi']
            age = entity['age']
            gender = entity['gender']

            ### face detection
            cv2.rectangle(frame, (x, y), (x+dx, y+dy), (0,255,0))

            ### age/gender detection
            cv2.putText(frame, "(age, gender) = ({:.1f}, {})".format(age, gender),
                        (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (255, 255, 255))

            nose = entity['face_nose']
            nose = (nose[0], nose[1])
            eyel = entity['face_eye'][0]
            eyel = (eyel[0], eyel[1])
            eyer = entity['face_eye'][1]
            eyer = (eyer[0], eyer[1])

            psi = entity['head'][2]
            theta = - entity['head'][0]
            phi = entity['head'][1]

            ### head orientation
            length = 150
            xvec = int(length*(sin(phi)*sin(psi) - cos(phi)*sin(theta)*cos(psi)))
            yvec = int(- length*(sin(phi)*cos(psi) - cos(phi)*sin(theta)*sin(psi)))
            cv2.line(frame, nose, (nose[0]+xvec, nose[1]+yvec), (0, 140, 255), 3)

            psi = 0
            theta = - entity['gaze'][0]
            phi = entity['gaze'][1]

            ### gaze orientation
            length = 150
            xvec = int(length*(sin(phi)*sin(psi) - cos(phi)*sin(theta)*cos(psi)))
            yvec = int(- length*(sin(phi)*cos(psi) - cos(phi)*sin(theta)*sin(psi)))
            cv2.line(frame, eyel, (eyel[0]+xvec, eyel[1]+yvec), (0, 140, 0), 3)

            xvec = int(length*(sin(phi)*sin(psi) - cos(phi)*sin(theta)*cos(psi)))
            yvec = int(- length*(sin(phi)*cos(psi) - cos(phi)*sin(theta)*sin(psi)))
            cv2.line(frame, eyer, (eyer[0]+xvec, eyer[1]+yvec), (0, 140, 0), 3)


        cv2.imshow('window', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    service.disable_session()

    camera.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    ### Web cam index might be different from 0 on your setup.
    ### To grab a given video file instead of the host computer cam, try:
    ### main("/path/to/myvideo.avi")
    f(0)
