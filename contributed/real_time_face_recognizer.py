import tkinter as tk
import cv2
import PIL.Image, PIL.ImageTk
from tkinter.font import Font
import os
import align.align_dataset_mtcnn as mtcnn
import classifier as train
import threading
import face
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
        self.window = window
        self.window.title(window_title)

        self.origin_folder = "face_data/origin"
        self.align_folder = "face_data/align"

        self.frame_interval = 3  # Number of frames after which to run face detection
        self.fps_display_interval = 5  # seconds
        self.frame_count = 0
        self.face_recognition = face.Recognition()

        self.video = MyVideoCapture()

        self.canvas = tk.Canvas(window, width = 800, height = 480)
        self.canvas.grid(row = 0, column = 0)

        myFont = Font(family="Times New Roman", size=24, weight="bold")

        self.frame = tk.Frame(window, width = 800, height = 100)
        self.frame.grid(row = 1, column = 0)

        self.medium_frame = tk.Frame(self.frame, width = 400, height = 100)
        self.medium_frame.grid(row = 0, column = 0, padx = [0, 70])

        self.small_frame = tk.Frame(self.medium_frame)
        self.small_frame.grid(row = 0, column = 0)

        self.label_name = tk.Label(self.small_frame, text = "Name:")
        self.label_name.configure(font = myFont)
        self.label_name.grid(row = 0, column = 0, padx = 2)

        self.text_name = tk.Entry(self.small_frame, width = 25)
        self.text_name.configure(font = myFont)
        self.text_name.grid(row = 0, column = 1)

        self.btn_snapshot_text = tk.StringVar()
        self.btn_snapshot_text.set("Snapshot")
        self.btn_snapshot = tk.Button(self.medium_frame, fg = "#0000CD", textvariable = self.btn_snapshot_text, width = 35, command = self.snapshot)
        self.btn_snapshot.configure(font = myFont)
        self.btn_snapshot.grid(row = 1, column = 0, pady = 5)

        self.btn_training_text = tk.StringVar()
        self.btn_training_text.set("Training")
        self.btn_training = tk.Button(self.frame, width = 10, height = 2, fg = "#0022CD", textvariable = self.btn_training_text, command = self.training)
        self.btn_training.configure(font = myFont)
        self.btn_training.grid(row = 0, column = 1)

        self.delay = 30
        self.update()
        
        self.window.mainloop()

    def update(self):
        ret, frame = self.video.get_frame()

        if ret:
    	    if (self.frame_count % self.frame_interval) == 0:
                millis = int(round(time.time() * 1000))

                self.faces = self.face_recognition.identify(frame)
                print(int(round(time.time() * 1000)) - millis)

    	    self.add_overlays(frame, self.faces)

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




App(tk.Tk(), "Real time face recognizer")


