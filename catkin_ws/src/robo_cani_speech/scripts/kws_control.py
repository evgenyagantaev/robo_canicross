#!/usr/bin/env python
# coding: utf-8

import rospy
from std_msgs.msg import String
from audio_common_msgs.msg import AudioData
from pocketsphinx import Decoder

class KWSDetection(object):
	def __init__(self):
		rospy.init_node('kws_control')
		rospy.on_shutdown(self.shutdown)
		self._kws_data_pub = rospy.Publisher('/abot/stt/kws_data', String, queue_size=10)
		self._hmm = rospy.get_param('~hmm')
		self._dict = rospy.get_param('~dict')
		self._kws = rospy.get_param('~kws')
		self._buffer_index = 0
		self._buffer = bytearray()
		self.startRecognizer()

	def startRecognizer(self):
		config = Decoder.default_config()
		config.set_string('-hmm', self._hmm)
		config.set_string('-dict', self._dict)
		config.set_string('-kws', self._kws)
		self._decoder = Decoder(config)
		self._decoder.start_utt()
		rospy.loginfo("KWS control node: Decoder started successfully")
		rospy.Subscriber('/audio', AudioData, self.makeBuffer)
		rospy.spin()

	def makeBuffer(self, audio_msg):
		self._buffer += audio_msg.data
		self._buffer_index = self._buffer_index + 1
		if self._buffer_index == 3:
			self.processAudio(self._buffer)
			self._buffer = bytearray()
			self._buffer_index = 0

	def processAudio(self, audio_buffer):
		self._decoder.process_raw(audio_buffer, False, False)
		if self._decoder.hyp() is not None:
			for seg in self._decoder.seg():
				rospy.logwarn("Detected key words: %s ", seg.word)
				self._decoder.end_utt()
				msg = seg.word
				self._kws_pub.publish(msg)
				self._decoder.start_utt()

	@staticmethod
	def shutdown():
		rospy.loginfo("KWS control node: Stop KWSDetection")
		rospy.sleep(1)

if __name__ == "__main__":
	KWSDetection()