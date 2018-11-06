import tkinter as tk
from tkinter import ttk
import cv2
import PIL.Image, PIL.ImageTk
from tkinter.font import Font
import os
import align.align_dataset_mtcnn as mtcnn
import classifier as train
import threading
import face
import lock
import time

class MyVideoCapture:
	def __init__(self):
		self.video = cv2.VideoCapture(0)
		if not self.video.isOpened():
			raiseError("Unable to open video source")

		self.width = self.video.get(cv2.CAP_PROP_FRAME_WIDTH)
		self.height = self.video.get(cv2.CAP_PROP_FRAME_HEIGHT)
		print("frame size :", self.width, self.height)

	def __del__(self):
		if self.video.isOpened():
			self.video.release()
		# self.window.mainloop()

	def get_frame(self):
		if self.video.isOpened():
			ret, frame = self.video.read()
			if ret:
				return (ret, cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
			else:
				return (ret, None)

class App:
    def __init__(self, window, window_title):
        self.origin_folder = "face_data/origin"
        self.align_folder = "face_data/align"
        self.frame_interval = 3  # Number of frames after which to run face detection
        self.delay = 30

        self.window = window
        self.window.title(window_title)
        self.frame_count = 0
        self.faces = None
        self.face_recognition = face.Recognition()
        self.lock = lock.Lock(self.finish_unlock_callback)
        self.start_recognition_time = None
        self.is_show_result = None
        self.unlock_result = None
        self.pose_string = ""

        self.video = MyVideoCapture()
        self.init_layout()

        self.update()
        self.window.mainloop()

    def init_layout(self):
        self.canvas = tk.Canvas(self.window, width = 800, height = 480)
        self.canvas.grid(row = 0, column = 0)

        myFont = Font(family="Times New Roman", size=24, weight="bold")

        self.frame = tk.Frame(self.window, width = 800, height = 100)
        self.frame.grid(row = 1, column = 0)

        self.medium_frame = tk.Frame(self.frame, width = 320, height = 100)
        self.medium_frame.grid(row = 0, column = 0, padx = [0, 40])

        self.small_frame = tk.Frame(self.medium_frame)
        self.small_frame.grid(row = 0, column = 0)

        self.label_name = tk.Label(self.small_frame, text = "Name:")
        self.label_name.configure(font = myFont)
        self.label_name.grid(row = 0, column = 0, padx = 2)

        self.text_name = tk.Entry(self.small_frame, width = 18)
        self.text_name.configure(font = myFont)
        self.text_name.grid(row = 0, column = 1)

        self.label_name = tk.Label(self.small_frame, text = "Pose")
        self.label_name.configure(font = myFont)
        self.label_name.grid(row = 0, column = 2)

        comvalue = tk.StringVar()
        self.combobox_pose = ttk.Combobox(self.small_frame, width = 12, textvariable=comvalue, state='readonly')
        self.combobox_pose["values"] = (self.lock.get_pose_list())
        self.combobox_pose.current(0)
        self.combobox_pose.set("select pose")
        self.combobox_pose.bind("<<ComboboxSelected>>", self.select_pose)
        self.combobox_pose.grid(row = 0, column = 3)
        # self.combobox_pose.pack()


        self.btn_snapshot_text = tk.StringVar()
        self.btn_snapshot_text.set("Snapshot")
        self.btn_snapshot = tk.Button(self.medium_frame, fg = "#0000CD", textvariable = self.btn_snapshot_text, width = 32, command = self.snapshot)
        self.btn_snapshot.configure(font = myFont)
        self.btn_snapshot.grid(row = 1, column = 0, pady = 5)

        self.btn_training_text = tk.StringVar()
        self.btn_training_text.set("Training")
        self.btn_training = tk.Button(self.frame, width = 8, height = 2, fg = "#0022CD", textvariable = self.btn_training_text, command = self.training)
        self.btn_training.configure(font = myFont)
        self.btn_training.grid(row = 0, column = 1)

        self.btn_unlock_text = tk.StringVar()
        self.btn_unlock_text.set("Unlock")
        self.btn_unlock = tk.Button(self.frame, width = 8, height = 2, fg = "#0022CD", textvariable = self.btn_unlock_text, command = self.unlock)
        self.btn_unlock.configure(font = myFont)
        self.btn_unlock.grid(row = 0, column = 2)

    def update(self):
    	ret, frame = self.video.get_frame()

    	if ret:
            is_awake = self.lock.is_start_recognition or self.lock.is_start_unlock
            if (self.frame_count % self.frame_interval) == 0 and is_awake:
                self.faces = self.face_recognition.identify(frame)

                # first step: id confirm
                if self.lock.is_start_recognition:
                    has_face, id = self.get_face_id(self.faces)
                    if has_face and id != 'unknown':
                        self.welcome(id)

                    elif self.is_recognition_timeout():
                        # time out
                        self.finish_unlock_callback()
                        self.lock.is_start_recognition = False

                # second step: password confirm
                elif self.lock.is_start_unlock:
                    has_face, id = self.get_face_id(self.faces)
                    if has_face and id != 'unknown':
                        self.lock.process(self.id_with_pose(id))

            if self.faces is not None and is_awake:
                if self.lock.is_start_unlock and not self.is_welcome_countdown():
                    self.add_welcome_message(frame, self.lock.id)
                self.add_overlays(frame, self.faces)

            if self.is_show_result:
                if not self.is_show_result_countdown():
                    self.add_unlock_result(frame, self.unlock_result)
                else:
                    self.is_show_result = False



            self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame).resize((800,480)))
            self.canvas.create_image(0, 0, image = self.photo, anchor = tk.NW)
            self.window.after(self.delay, self.update)
            self.frame_count += 1



    def align_image(self):
        argString = [self.origin_folder, self.align_folder, "--random_order"]
        mtcnn.process(argString)
        self.btn_snapshot.config(state = "normal")
        self.btn_snapshot_text.set("Snapshot")

    def snapshot(self):
        self.btn_snapshot_text.set("processing...")
        self.btn_snapshot.config(state = "disable")

        if len(self.pose_string) > 0:
            name = self.text_name.get() + '_' + self.pose_string
        else:
            name = self.text_name.get()

        save_path = os.path.join(self.origin_folder, name)
        if not os.path.exists(save_path):
           os.makedirs(save_path)

        for i in range(1, 31):
            ret, frame = self.video.get_frame()
            if ret:
               file_name = name + "_" + str(i).zfill(4) + ".jpg"

            cv2.imwrite(os.path.join(save_path, file_name), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

        thread = threading.Thread(target = self.align_image, args = ())
        thread.daemon = True
        thread.start()

    def start_training(self):
    	argString = ["TRAIN", self.align_folder, "20180402-114759/20180402-114759.pb", "my_classifier.pkl"]
    	train.process(argString)
    	self.btn_training.config(state = "normal")
    	self.btn_training_text.set("Training")

    def training(self):
    	self.btn_training_text.set("processing...")
    	self.btn_training.config(state = "disable")

    	thread = threading.Thread(target = self.start_training, args = ())
    	thread.daemon = True
    	thread.start()

    def unlock(self):
        self.start_recognition_time = time.time()
        self.btn_unlock_text.set("processing...")
        self.btn_unlock.config(state = "disable")
        self.lock.is_start_recognition = True

    def finish_unlock_callback(self, result):
        self.btn_unlock.config(state = "normal")
        self.btn_unlock_text.set("Unlock")
        self.is_show_result = True
        self.unlock_result = result

    def get_face_id(self, faces):
        if len(faces) > 0:
            return True, faces[0].name
        else:
            return False, None

    def welcome(self, id):
        print('hi, ', self.clean_id(id))
        print('start unlock')
        # id confirm, enter the next step
        self.lock.is_start_recognition = False
        self.lock.is_start_unlock = True
        self.lock.set_and_start_unlock(self.clean_id(id))

    def add_welcome_message(self, frame, id):
        message = 'Hi, ' + id + ', please enter your password'
        cv2.putText(frame, message, (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (200, 0, 160), thickness=3, lineType=2)

    def add_unlock_result(self, frame, result):
        message = 'Unlock '
        if result == lock.Result.SUCCESS:
            message = message + 'success!'
        elif result == lock.Result.FAIL:
            message = message + 'fail...'
        elif result == lock.Result.TIMEOUT:
            message = message + 'time out!'
        else:
            message = 'No password in dataset'
            
        cv2.putText(frame, message, (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (200, 10, 10), thickness=3, lineType=2)

    def is_recognition_timeout(self):
        now_time = time.time()
        return now_time - self.start_recognition_time > 10

    def is_welcome_countdown(self):
        now_time = time.time()
        return now_time - self.lock.start_unlock_time > 3

    def is_show_result_countdown(self):
        now_time = time.time()
        return now_time - self.lock.finish_process_time > 3

    def clean_id(self, id):
        id_with_pose = self.id_with_pose(id)
        if '_' in id_with_pose:
            return id_with_pose.split('_')[0]
        else:
            return id_with_pose
    def id_with_pose(self, id):
        split_id = id.split(" ")
        if len(split_id) == 3:
            return split_id[0] + '_' + split_id[1]
        elif len(split_id) == 2:
            return split_id[0]

    def select_pose(self, *args):
        pose_select_index = self.combobox_pose.current()
        print(pose_select_index)
        if pose_select_index == 0:
            self.pose_string = ''
        else:
            self.pose_string = self.lock.get_string_by_pose(pose_select_index)
        print(self.pose_string)

    def add_overlays(self, frame, faces):
	    if faces is not None:
	        for face in faces:
	            face_bb = face.bounding_box.astype(int)
	            if face.name is not None:
	            	text_x = face_bb[0] if (face_bb[0] > self.video.width - 6) else face_bb[0] + 6
	            	text_y = face_bb[3] if (face_bb[3] < 6) else face_bb[3] - 6
	            	if face.name == 'unknown':
	                    cv2.rectangle(frame,
	                          (face_bb[0], face_bb[1]), (face_bb[2], face_bb[3]),
	                          (0, 127, 127), 2)
	                    cv2.putText(frame, face.name, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 127, 127), thickness=2, lineType=1)
	            	else:
	                	cv2.rectangle(frame,
	                          (face_bb[0], face_bb[1]), (face_bb[2], face_bb[3]),
	                          (0, 255, 0), 2)
	                	cv2.putText(frame, face.name, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), thickness=2, lineType=2)




App(tk.Tk(), "Real time face recognizer - lock version")


