#!/usr/bin/env python
import StringIO
import cv2
import angus
import numpy as np
import time
from multiprocessing import Process, Queue

def angus_process(q_in, q_out):
    frame = q_in.get()
    while frame is not None:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret, buff = cv2.imencode(".jpg", gray)

        buff = StringIO.StringIO(np.array(buff).tostring())
        job = service.process({"image": buff})
        res = job.result
        q_out.put(res)
        frame = q_in.get()
        for k in range(q_in.qsize()):
            frame = q_in.get()

if __name__ == '__main__':    
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print "Cannot open stream of index " + str(stream_index)
        exit(1)

    #cap.set(3, 1280)
    #cap.set(4, 720)
    print "Video stream is of resolution " + str(cap.get(3)) + " x " + str(cap.get(4))

    conn = angus.connect()
    service = conn.services.get_service("age_and_gender_estimation", version=1)
    service.enable_session()
    
    q_in = Queue()
    q_out = Queue()
    process = Process(target=angus_process, args=(q_in, q_out))
    process.start()

    while(cap.isOpened()):
        ret, frame = cap.read()
        if not ret:
            continue

        q_in.put(frame)
        res = q_out.get()

        for face in res['faces']:
            roi = face['roi']
            gender = face['gender']
            age = face['age']

            cv2.rectangle(frame, (int(roi[0]), int(roi[1])), 
                          (int(roi[0] + roi[2]), int(roi[1] + roi[3])), 
                          (0,255,0))

            cv2.putText(frame, "(age, gender) = (" + '%.1f'%age + ", " + str(gender) + ")", 
                        (int(roi[0]), int(roi[1])), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.8, (255, 255, 255))
        
        cv2.imshow('original', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    service.disable_session()

    q_in.put(None)
    process.join()

    cap.release()
    cv2.destroyAllWindows()
