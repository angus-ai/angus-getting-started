#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Queue
import StringIO
import wave
import time
import angus
import numpy as np
import pyaudio
import os
import json

CHUNK = 8192*2
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100


### Index will differ depending on your system
INDEX = 4   # USB Cam
WAVE_OUTPUT_FILENAME = "output.wav"

p = pyaudio.PyAudio()

devinfo = p.get_device_info_by_index(INDEX)
print devinfo


def convert(buff_in, rate_in, rate_out):
    # Resample buffer with numpy linear interpolation
    buff_in = np.frombuffer(buff_in, dtype=np.int16)
    srcx = np.arange(0, buff_in.size, 1)
    tgtx = np.arange(0, buff_in.size, float(rate_in) / float(rate_out))
    buff_out = np.interp(tgtx, srcx, buff_in).astype(np.int16)
    return buff_out.tostring()

for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    print (i, dev['name'], dev['maxInputChannels'])

conn = angus.connect()
service = conn.services.get_service('word_spotting', version=1)

PATH = os.path.dirname(__file__)

w1_s1 = conn.blobs.create(open(PATH + "sounds/allumelesalon.wav"))
w1_s2 = conn.blobs.create(open(PATH + "sounds/allumelesalon2.wav"))
w1_s3 = conn.blobs.create(open(PATH + "sounds/allumelesalon3.wav"))
w1_s4 = conn.blobs.create(open(PATH + "sounds/allumelesalon4.wav"))

w2_s1 = conn.blobs.create(open(PATH + "sounds/eteintlewifi.wav"))
w2_s2 = conn.blobs.create(open(PATH + "sounds/eteintlewifi2.wav"))
w2_s3 = conn.blobs.create(open(PATH + "sounds/eteintlewifi3.wav"))
w2_s4 = conn.blobs.create(open(PATH + "sounds/eteintlewifi4.wav"))

vocabulary = {'allume le salon': [w1_s1, w1_s2, w1_s3, w1_s4], 'eteint le wifi': [w2_s1, w2_s2, w2_s3, w2_s4]}

service.enable_session({"vocabulary" : vocabulary})

stream_queue = Queue.Queue()

def callback(in_data, frame_count, time_info, status):
    stream_queue.put(in_data)
    return (in_data, pyaudio.paContinue)

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
                input_device_index=INDEX,
                stream_callback=callback)


stream.start_stream()

while True:

    nb_buffer_available = stream_queue.qsize()
#    if nb_buffer_available > 0:
#        print "nb buffer available" + str(nb_buffer_available)

    if nb_buffer_available == 0:
        time.sleep(0.01)
        continue

    if nb_buffer_available > 5:
        stream_queue.queue.clear()

    data = stream_queue.get()
    data = convert(data, RATE, 16000)

    buff = StringIO.StringIO()

    wf = wave.open(buff, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(16000)
    wf.writeframes(data)
    wf.close()

    job = service.process(
        {'sound': StringIO.StringIO(buff.getvalue()), 'sensitivity': 0.7, "lang": "fr-FR"})

    if "nbests" in job.result:
        print json.dumps(job.result, indent=4)


stream.stop_stream()
stream.close()
p.terminate()
