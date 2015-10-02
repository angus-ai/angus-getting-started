#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Queue
import StringIO
import wave
import time
import angus
import pyaudio
import os
import operator
import json

CHUNK = 8192*2
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

def convert(filename, filename2):
        os.system("sox %s -r 16000 %s" % (filename, filename2))

### Index will differ depending on your system
INDEX = 4   # USB Cam
WAVE_OUTPUT_FILENAME = "output.wav"

p = pyaudio.PyAudio()

devinfo = p.get_device_info_by_index(INDEX)
print devinfo

for i in range(p.get_device_count()):
  dev = p.get_device_info_by_index(i)
  print((i,dev['name'],dev['maxInputChannels']))

conn = angus.connect()
service = conn.services.get_service('word_spotting', version=2)

vocabulary = [{"words" : "hello"},
              {"words" : "music"},
              {"words" : "whisky"}]

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

while(True):

    nb_buffer_available = stream_queue.qsize()
#    if nb_buffer_available > 0:
#        print "nb buffer available" + str(nb_buffer_available)

    if nb_buffer_available == 0:
        time.sleep(0.01)
        continue

    if nb_buffer_available > 5:
        stream_queue.queue.clear()

    data = stream_queue.get()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(data)
    wf.close()

    convert(WAVE_OUTPUT_FILENAME, "test.wav")

    job = service.process({'sound': open("test.wav"), 'sensitivity':0.7, "lang": "en-US"})
    if "nbests" in job.result:
        print json.dumps(job.result, indent=4)


stream.stop_stream()
stream.close()
p.terminate()
