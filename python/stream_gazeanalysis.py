#!/usr/bin/env python
import StringIO
import pprint
from math import sin, cos
import cv2
import numpy as np
import angus

LINETH = 3

if __name__ == '__main__':

    ### To grab the host computer web cam instead of a given file, try:
    cap = cv2.VideoCapture(0)
    cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 480)

    print "Input stream is of resolution: " + str(cap.get(3)) + " x " + str(cap.get(4))
    conn = angus.connect()
    service = conn.services.get_service('gaze_analysis', 1)
    service.enable_session()

    while cap.isOpened():
        ret, frame = cap.read()
        if frame != None:
            ### angus.ai computer vision services require gray images right now.
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            ret, buff = cv2.imencode(".png", gray)
            buff = StringIO.StringIO(np.array(buff).tostring())

            job = service.process({"image": buff})
            res = job.result

            print "---------- Raw answer from Angus.ai -----------"
            pprint.pprint(res)
            print "-----------------------------------------------"


            if res['nb_faces'] > 0:
                for h in res['faces']:
                    nose = h['nose']
                    nose = (nose[0], nose[1])
                    eyel = h['eye_left']
                    eyel = (eyel[0], eyel[1])
                    eyer = h['eye_right']
                    eyer = (eyer[0], eyer[1])

                    psi = h['head_roll']
                    theta = - h['head_yaw']
                    phi = h['head_pitch']

                    length = 150
                    xvec = int(length*(sin(phi)*sin(psi) - cos(phi)*sin(theta)*cos(psi)))
                    yvec = int(- length*(sin(phi)*cos(psi) - cos(phi)*sin(theta)*sin(psi)))
                    cv2.line(frame, nose, (nose[0]+xvec, nose[1]+yvec), (0, 140, 255), LINETH)

                    psi = 0
                    theta = - h['gaze_yaw']
                    phi = h['gaze_pitch']

                    length = 150
                    xvec = int(length*(sin(phi)*sin(psi) - cos(phi)*sin(theta)*cos(psi)))
                    yvec = int(- length*(sin(phi)*cos(psi) - cos(phi)*sin(theta)*sin(psi)))
                    cv2.line(frame, eyel, (eyel[0]+xvec, eyel[1]+yvec), (0, 140, 0), LINETH)

                    xvec = int(length*(sin(phi)*sin(psi) - cos(phi)*sin(theta)*cos(psi)))
                    yvec = int(- length*(sin(phi)*cos(psi) - cos(phi)*sin(theta)*sin(psi)))
                    cv2.line(frame, eyer, (eyer[0]+xvec, eyer[1]+yvec), (0, 140, 0), LINETH)


            cv2.imshow('Gaze Analysis', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            print "None image read"


    ### Disabling session on the server
    service.disable_session()

    cap.release()
    cv2.destroyAllWindows()
