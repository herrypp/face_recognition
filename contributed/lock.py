import time

class Lock:
	def __init__(self, unlock_finish_callback):
		self.id = None
		self.password = None
		self.password_length = None
		self.progress = None
		self.is_start_recognition = False
		self.is_start_unlock = False
		self.unlock_finish_callback = unlock_finish_callback
		self.start_unlock_time = None
		self.finish_process_time = None
		self.pre_pose = None


	def process(self, id):
		if self.is_unlock_timeout():
			print('unlock time out')
			self.finish_process_time = time.time()
			self.reset(Result.TIMEOUT)

		pose = self.get_pose(id)
		print('pose = ', self.get_string_by_pose(pose))
		if pose == self.pre_pose or pose == Pose.ERROR:
			return
		else:
			self.pre_pose = pose
			if pose == Pose.NORMAL:
				return
			elif pose == self.password[self.progress]:
				print('pass ', self.progress + 1, ' step : ', self.get_string_by_pose(pose))
				self.progress = self.progress + 1

				if self.progress == self.password_length:
					print('unlock success')
					self.finish_process_time = time.time()
					self.reset(Result.SUCCESS)
			else:
				print('unlock fail')
				self.finish_process_time = time.time()
				self.reset(Result.FAIL)


	def set_and_start_unlock(self, id):
		self.id = id
		self.password = self.get_password(id)
		self.password_length = len(self.password)
		self.show_password()
		self.progress = 0
		self.start_unlock_time = time.time()
		self.pre_pose = Pose.NORMAL
		if self.password_length == 0:
			print("Do not exist this ID in password table:", id)
			self.finish_process_time = time.time()
			self.reset(Result.NO_DATA)

	def get_password(self, id):
		password = []
		switcher = {
	        'Herry': [Pose.LEFT, Pose.RIGHT, Pose.OTHER, Pose.UP],
	        'victor': [Pose.LEFT, Pose.RIGHT, Pose.OTHER, Pose.CLOSE_LEFT]
	        # TODO: add more id's password
	        # TODO: create document to record password
		}

		return switcher.get(id, [])

	def get_pose(self, id):
		if id == self.id:
			return Pose.NORMAL
		else:
			prefix = self.id + '_'
			pose_str = id.split(prefix)
			if len(pose_str) == 0:
				return Pose.ERROR
			else:
				return self.get_pose_by_string(pose_str[len(pose_str)-1])
				

	def get_pose_by_string(self, str):
		switcher = {
	        'Left': Pose.LEFT,
	        'Right': Pose.RIGHT,
	        'Up': Pose.UP,
	        'Down': Pose.DOWN,
	        'CloseLeft': Pose.CLOSE_LEFT,
	        'CloseRight': Pose.CLOSE_RIGHT,
	        'Smile': Pose.SMILE,
	        'Other': Pose.OTHER
	        # TODO: add more pose
		}

		return switcher.get(str, Pose.ERROR)

	def get_string_by_pose(self, pose):
		switcher = {
			Pose.ERROR: 'Error pose',
			Pose.NORMAL: 'Normal',
	        Pose.LEFT: 'Left',
	        Pose.RIGHT: 'Right',
	        Pose.UP: 'Up',
	        Pose.DOWN: 'Down',
	        Pose.CLOSE_LEFT: 'CloseLeft',
	        Pose.CLOSE_RIGHT: 'CloseRight',
	        Pose.SMILE: 'Smile',
	        Pose.OTHER: 'Other'
	        # TODO: add more pose
		}

		return switcher.get(pose, 'Error pose')

	def get_pose_list(self):
		return ['Normal','Left','Right','Up','Down', 'CloseLeft', 'CloseRight', 'Smile', 'Other']

	def is_unlock_timeout(self):
		now_time = time.time()
		diff = now_time - self.start_unlock_time 
		return diff > 20

	def reset(self, result):
		self.is_start_recognition = False
		self.is_start_unlock = False
		self.unlock_finish_callback(result)

	def show_password(self):
		password_list = []
		for i in range(0, self.password_length):
			password_list.append(self.get_string_by_pose(self.password[i]))

		print('your password is ', password_list)

class Pose:
	ERROR = -1
	NORMAL = 0
	LEFT = 1
	RIGHT = 2
	UP = 3
	DOWN = 4
	CLOSE_LEFT = 5
	CLOSE_RIGHT = 6
	SMILE = 7
	OTHER = 8

class Result:
	SUCCESS = 0,
	FAIL = 1,
	TIMEOUT = 2,
	NO_DATA = 3
