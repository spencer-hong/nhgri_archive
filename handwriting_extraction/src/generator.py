from pathlib import Path
import cv2
from skimage import filters
from random import randint, getrandbits
import numpy as np
from PIL import Image
import pytesseract
from pytesseract import Output
import traceback


class generator(object):
	"""A generator to create new synthetic handwritten images on printed text.
    ...

    Attributes
    ----------
    config: dict
    	configuration file containing all of the handwritten image paths
    digits : list
        all digit-based images (opened) in a list
    word_foreground : list
        all word-based images (paths) in a list
    sentence_foreground : list
        all sentence-based images (paths) in a list
    arrow_foreground : list
    	all arrow-based images in a list
    circle : list
    	all circle-based images in a list
    line : list
    	all line-based images in a list
	foreground : Numpy array-like
		Numpy 2D image representing the current foreground

    Methods
    -------
    set_foreground(foreground):
    	Set the current foreground
	
	reset_foreground():
		Reset the current foreground

    gen_cell_ssn():
        Generates a random handwritten phone_number 
        in a format xxx[line]xxx[line]xxx

    gen_ssn():
    	Generates a random social security number
    	in a format xxx[line]xxx[line]xxxx

   	gen_credit_card():
   		Generates a random credit card number
   		in a format xxxx[line]xxxx[line]xxxx[line]xxxx

   	draw_circles(background, bbox):
   		Draws a circle around a randomly selected word

   	put_text_on_location(background, bbox):
   		Puts sentences in the specific bounding box provided

   	underline_words(background, bbox):
   		Underlines words with a handwritten line

   	cross_words(background, bbox):
   		Cross words with a handwritten line

   	add_PII(background):
   		Add phone, SSN, and credit card numbers

   	add_words(background, rotate = False):
   		Add words or sentences

   	add_arrows(background):
   		Add arrows in random direction/rotation


    """
	def __init__(self, config):
		"""
        Constructs all the necessary attributes for the generator object.

        Parameters
        ----------
        config : dict
            configuration containing all of the necessary image paths

        Returns
        ----------
        None
        """

		digits_dir = config['digits']

		self.digits = []

		with open(digits_dir, 'r') as f:
			for line in f:
				temp = []
				for i in line.split()[:-10]:
					if int(float(i)) == 1:
						temp.append(0)
					else:
						temp.append(1)
				self.digits.append(np.reshape(np.array(temp, dtype = np.uint8) * 255, (16, 16)))

		path_word_images = Path(config['words'])
		path_foreground_images = Path(config['sentences'])
		path_arrow_images = Path(config['arrows'])
		self.word_foreground = [f for f in path_word_images.glob("**/*.png")]
		self.sentence_foreground = [f for f in path_foreground_images.glob("**/*.png")]
		self.arrow_foreground = [f for f in path_arrow_images.glob("**/*.png")]
		self.circle = np.load(config['circles'])
		self.line = np.load(config['lines'])
		self.foreground = None

	def set_foreground(self, foreground):
		"""
        Set the current foreground

        Parameters
        ----------
        foreground : Numpy array-like
        	2D Numpy matrix representing the current foreground

        Returns
        ----------
        None
        """
		self.foreground = foreground.copy()

	def reset_foreground(self):
		"""
        Reset the current foreground

        Parameters
        ----------
        None

        Returns
        ----------
        None
        """

		self.foreground = None
	def gen_cell(self):
		"""
        Generates a handwritten cell phone number in the form of xxx[line]xxx[line]xxx

        Parameters
        ----------
        None

        Returns
        ----------
        new_im: PIL Image
        	Image in a 16 x 16 * n (where n is the numbe of elements)
        """
		random_pos = np.random.randint(0, len(self.digits) - 1, size = 3)

		images = [Image.fromarray(self.digits[i]) for i in random_pos]
		random_pos = round(np.random.uniform(0, len(self.line) - 1))


		selected_line = cv2.resize(np.reshape(255 - self.line[random_pos], (28, 28)), [16, 16], cv2.INTER_AREA)
		images.append(Image.fromarray(selected_line))

		random_pos = np.random.randint(0, len(self.digits) - 1, size = 3)

		images.extend([Image.fromarray(self.digits[i]) for i in random_pos])
		random_pos = round(np.random.uniform(0, len(self.line) - 1))


		selected_line = cv2.resize(np.reshape(255 - self.line[random_pos], (28, 28)), [16, 16], cv2.INTER_AREA)
		images.append(Image.fromarray(selected_line))

		random_pos = np.random.randint(0, len(self.digits) - 1, size = 3)

		images.extend([Image.fromarray(self.digits[i]) for i in random_pos])
		random_pos = round(np.random.uniform(0, len(self.line) - 1))

		widths, heights = zip(*(i.size for i in images))


		total_width = sum(widths)
		max_height = max(heights)

		new_im = Image.new('RGB', (total_width, max_height))


		x_offset = 0

		for im in images:
			new_im.paste(im, (x_offset,0))
			x_offset += im.size[0]
		
		return new_im

	def gen_ssn(self):
		"""
        Generates a handwritten social security number in the form of xxx[line]xxx[line]xxxx

        Parameters
        ----------
        None

        Returns
        ----------
        new_im: PIL Image
        	Image in a 16 x 16 * n (where n is the numbe of elements)
        """

		random_pos = np.random.randint(0, len(self.digits) - 1, size = 3)

		images = [Image.fromarray(self.digits[i]) for i in random_pos]
		random_pos = round(np.random.uniform(0, len(self.line) - 1))


		selected_line = cv2.resize(np.reshape(255 - self.line[random_pos], (28, 28)), [16, 16], cv2.INTER_AREA)
		images.append(Image.fromarray(selected_line))

		random_pos = np.random.randint(0, len(self.digits) - 1, size = 3)

		images.extend([Image.fromarray(self.digits[i]) for i in random_pos])
		random_pos = round(np.random.uniform(0, len(self.line) - 1))


		selected_line = cv2.resize(np.reshape(255 - self.line[random_pos], (28, 28)), [16, 16], cv2.INTER_AREA)
		images.append(Image.fromarray(selected_line))

		random_pos = np.random.randint(0, len(self.digits) - 1, size = 4)

		images.extend([Image.fromarray(self.digits[i]) for i in random_pos])
		random_pos = round(np.random.uniform(0, len(self.line) - 1))

		widths, heights = zip(*(i.size for i in images))


		total_width = sum(widths)
		max_height = max(heights)

		new_im = Image.new('RGB', (total_width, max_height))


		x_offset = 0

		for im in images:
			new_im.paste(im, (x_offset,0))
			x_offset += im.size[0]
		
		return new_im


	def gen_credit_card(self):
		"""
        Generates a handwritten cell phone number in the form of xxxx[line]xxxx[line]xxxx[line]xxxx

        Parameters
        ----------
        None

        Returns
        ----------
        new_im: PIL Image
        	Image in a 16 x 16 * n (where n is the numbe of elements)
        """
		random_pos = np.random.randint(0, len(self.digits) - 1, size = 4)

		images = [Image.fromarray(self.digits[i]) for i in random_pos]
		random_pos = round(np.random.uniform(0, len(self.line) - 1))


		selected_line = cv2.resize(np.reshape(255 - self.line[random_pos], (28, 28)), [16, 16], cv2.INTER_AREA)
		images.append(Image.fromarray(selected_line))

		random_pos = np.random.randint(0, len(self.digits) - 1, size = 4)

		images.extend([Image.fromarray(self.digits[i]) for i in random_pos])
		random_pos = round(np.random.uniform(0, len(self.line) - 1))


		selected_line = cv2.resize(np.reshape(255 - self.line[random_pos], (28, 28)), [16, 16], cv2.INTER_AREA)
		images.append(Image.fromarray(selected_line))

		random_pos = np.random.randint(0, len(self.digits) - 1, size = 4)

		images.extend([Image.fromarray(self.digits[i]) for i in random_pos])
		random_pos = round(np.random.uniform(0, len(self.line) - 1))
		
		selected_line = cv2.resize(np.reshape(255 - self.line[random_pos], (28, 28)), [16, 16], cv2.INTER_AREA)
		images.append(Image.fromarray(selected_line))
		
		random_pos = np.random.randint(0, len(self.digits) - 1, size = 4)

		images.extend([Image.fromarray(self.digits[i]) for i in random_pos])

		widths, heights = zip(*(i.size for i in images))


		total_width = sum(widths)
		max_height = max(heights)

		new_im = Image.new('RGB', (total_width, max_height))


		x_offset = 0

		for im in images:
			new_im.paste(im, (x_offset,0))
			x_offset += im.size[0]
		
		return new_im

	def draw_circles(self, background, bbox):
		"""
        Generates a handwritten circle around a selected bounding box

        Parameters
        ----------
        background : Numpy array-like
        	2D Numpy matrix representing an image
        bbox : tuple
        	Tuple containing x (left), y (top), width, height

        Returns
        ----------
        added : Boolean
        	True if circle was added
        """

		(x, y, w, h) = bbox #left, top, width, height
		
		random_pos = round(np.random.uniform(0, len(self.circle) - 1))
		
		
		selected_circle = np.reshape(255 - self.circle[random_pos], (28, 28))
		
		circle_w, circle_h = selected_circle.shape
		
		# resize the circle to surround the word bbox
		resized_circle = cv2.resize(selected_circle, (int(w*2), int(h*2)), interpolation = cv2.INTER_LINEAR)

		resized_circle = resized_circle.astype('uint8')
		
		# limiarization foreground
		th = filters.threshold_sauvola(resized_circle, window_size=15, k=0.2)
		resized_circle = resized_circle > th
		resized_circle = resized_circle.astype('uint8')

		resized_w, resized_h = resized_circle.shape
		
		# if the circle is too big, don't draw it on the foreground
		if resized_h > 1000:
			return False
		else:
			# choose the positions of the lines
			pos_ini_x = int(x - (resized_h/4))
			pos_ini_y = int(y - (resized_w/4))
			pos_ini_y2 = min(pos_ini_y+resized_w, background.shape[0])
			pos_ini_x2 = min(pos_ini_x+resized_h, background.shape[1])
			
			try:
				self.foreground[pos_ini_y:pos_ini_y2, pos_ini_x:pos_ini_x2] = resized_circle[0:(pos_ini_y2 - pos_ini_y), 0:(pos_ini_x2 - pos_ini_x)]
				self.foreground = self.foreground.astype('uint8')
			except:
				return False

			return True


	def put_text_on_location(self, background, bbox):
		"""
        Puts some element of text in the specific location in the foreground

        Parameters
        ----------
        background : Numpy array-like
        	2D Numpy matrix representing an image
        bbox : tuple
        	Tuple containing x (left), y (top), width, height

        Returns
        ----------
        added : Boolean
        	True if element was added
        """

		(x, y, w, h) = bbox

		choice = np.random.randint(low = 0, high = 10)

		# the choice of text are: words, sentences, SSN
		if choice < 5:
			pos = round(np.random.uniform(0, len(self.sentence_foreground) -1))  

			word = cv2.imread(self.sentence_foreground[pos].as_posix(), cv2.IMREAD_COLOR)
			word = cv2.cvtColor(word, cv2.COLOR_BGR2GRAY)
		elif choice < 9:
			pos = round(np.random.uniform(0, len(self.word_foreground) -1))  

			word = cv2.imread(self.word_foreground[pos].as_posix(), cv2.IMREAD_COLOR)
			word = cv2.cvtColor(word, cv2.COLOR_BGR2GRAY)

		elif choice < 10:
			word = self.gen_ssn()


			word = cv2.cvtColor(np.array(word), cv2.COLOR_BGR2GRAY)


			word = cv2.resize(word, (200, 100), interpolation = cv2.INTER_LINEAR)

		th = filters.threshold_sauvola(word, window_size=15, k=0.2)
		word = word > th
		word = word.astype('uint8')

		resized_w, resized_h = word.shape
		
		# don't add to the foreground if the size is too big
		if resized_h > 1000:
			return False


		# choose the positions of the lines
		pos_ini_x = int(x - (resized_h/4))
		pos_ini_y = int(y - 0)

		pos_ini_y2 = min(pos_ini_y+resized_w, background.shape[0])
		pos_ini_x2 = min(pos_ini_x+resized_h, background.shape[1])
		
		try:
			self.foreground[pos_ini_y:pos_ini_y2, pos_ini_x:pos_ini_x2] = word[0:pos_ini_y2 - pos_ini_y, 0:pos_ini_x2 - pos_ini_x]
			self.foreground = self.foreground.astype('uint8')
		except:
			return False
		
		return True


	def underline_words(self, background, bbox):
		"""
       	Underline a text in the printed image using a handwritten line

        Parameters
        ----------
        background : Numpy array-like
        	2D Numpy matrix representing an image
        bbox : tuple
        	Tuple containing x (left), y (top), width, height

        Returns
        ----------
        added : Boolean
        	True if element was added
        """


		(x, y, w, h) = bbox #left, top, width, height
		
		random_pos = round(np.random.uniform(0, len(self.line) - 1))
		
		
		selected_line = np.reshape(255 - self.line[random_pos], (28, 28))
		
		line_w, line_h = selected_line.shape
		
		resized_line = cv2.resize(selected_line, (int(w*2), int(h*2)), interpolation = cv2.INTER_LINEAR)

		resized_line = resized_line.astype('uint8')

		 # limiarization foreground
		th = filters.threshold_sauvola(resized_line, window_size=15, k=0.2)
		resized_line = resized_line > th
		resized_line = resized_line.astype('uint8')

		resized_w, resized_h = resized_line.shape
		
		if resized_h > 1000:
			return False
		else:

			# choose the positions of the lines
			pos_ini_x = int(x - (resized_h/4))
			pos_ini_y = int(y - 0)

			pos_ini_y2 = min(pos_ini_y+resized_w, background.shape[0])
			pos_ini_x2 = min(pos_ini_x+resized_h, background.shape[1])
			
			try:
				self.foreground[pos_ini_y:pos_ini_y2, pos_ini_x:pos_ini_x2] = resized_line[0:pos_ini_y2 - pos_ini_y, 0:pos_ini_x2 - pos_ini_x]
				self.foreground = self.foreground.astype('uint8')
			except:
				return False
			
			return True

	def cross_words(self, background, bbox):
		"""
        Cross text with a handwritten line

        Parameters
        ----------
        background : Numpy array-like
        	2D Numpy matrix representing an image
        bbox : tuple
        	Tuple containing x (left), y (top), width, height

        Returns
        ----------
        added : Boolean
        	True if element was added
        """

		(x, y, w, h) = bbox #left, top, width, height
		
		random_pos = round(np.random.uniform(0, len(self.line) - 1))
		
		
		selected_line = np.reshape(255 - self.line[random_pos], (28, 28))
		
		line_w, line_h = selected_line.shape
		
		
		resized_line = cv2.resize(selected_line, (int(w*2), int(h*2)), interpolation = cv2.INTER_LINEAR)

		resized_line = resized_line.astype('uint8')

		 # limiarization foreground
		th = filters.threshold_sauvola(resized_line, window_size=15, k=0.2)
		resized_line = resized_line > th
		resized_line = resized_line.astype('uint8')

		resized_w, resized_h = resized_line.shape
		
		if resized_h > 1000:
			return False
		elif resized_w < 50:
			return False
		else:

			# choose the positions of the lines
			pos_ini_x = int(x - (resized_h/4))
			pos_ini_y = int(y - (resized_w/4))

			pos_ini_y2 = min(pos_ini_y+resized_w, background.shape[0])
			pos_ini_x2 = min(pos_ini_x+resized_h, background.shape[1])
			
			
			try:
				self.foreground[pos_ini_y:pos_ini_y2, pos_ini_x:pos_ini_x2] = resized_line[0:pos_ini_y2 - pos_ini_y, 0:pos_ini_x2 - pos_ini_x]
				self.foreground = self.foreground.astype('uint8')
			except:
				return True
			return False

	def add_PII(self, background):
		"""
        Puts some PII elements in the foreground

        Parameters
        ----------
        background : Numpy array-like
        	2D Numpy matrix representing an image

        Returns
        ----------
        added : Boolean
        	True if element was added
        """

		ssn = self.gen_ssn()
		credit = self.gen_credit_card()
		cell = self.gen_cell()
		
		for k in [ssn, credit, cell]:
			
			basewidth = round(np.random.uniform(200, 500))
			wpercent = (basewidth/float(k.size[0]))
			hsize = int((float(k.size[1])*float(wpercent)))
			k = k.resize((basewidth,hsize), Image.Resampling.LANCZOS)
			
			img = np.array(k)
			word = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
			
			
			angle = round(np.random.uniform(-50, 50))
			word = rotate_bound(word, angle)

			# limiarization foreground
			th = filters.threshold_sauvola(word, window_size=15, k=0.2)
			word = word > th
			word = word.astype('uint8')

			word_w, word_h = word.shape

			# choose the positions of the lines
			pos_ini_x = round(np.random.uniform(0, background.shape[1]))
			pos_ini_y = round(np.random.uniform(0, background.shape[0]))

			pos_ini_y2 = min(pos_ini_y+word_w, background.shape[0])
			pos_ini_x2 = min(pos_ini_x+word_h, background.shape[1])

			self.foreground[pos_ini_y:pos_ini_y2, pos_ini_x:pos_ini_x2] = word[0:pos_ini_y2 - pos_ini_y, 0:pos_ini_x2 - pos_ini_x]
			self.foreground = self.foreground.astype(np.uint8)
			
		return True


	def add_words(self, background, rotate = False):
		"""
        Puts words or sentences to the foreground

        Parameters
        ----------
        background : Numpy array-like
        	2D Numpy matrix representing an image
		
		rotate : Boolean
			Rotate the image if true
        Returns
        ----------
        added : Boolean
        	True if element was added
        """


		# the two choices are words or sentences
		# if bool(getrandbits(1)):
		pos = round(np.random.uniform(0, len(self.sentence_foreground) -1))  

		word = cv2.imread(self.sentence_foreground[pos].as_posix(), cv2.IMREAD_COLOR)
		word = cv2.cvtColor(word, cv2.COLOR_BGR2GRAY)
		
		if rotate:
			angle = round(np.random.uniform(-90, 90))
			word = rotate_bound(word, angle)

		# limiarization foreground
		th = filters.threshold_sauvola(word, window_size=15, k=0.2)
		word = word > th
		word = word.astype('uint8')

		word_w, word_h = word.shape

		# choose the positions of the lines
		pos_ini_x = round(np.random.uniform(0, background.shape[1]))
		pos_ini_y = round(np.random.uniform(0, background.shape[0]))

		pos_ini_y2 = min(pos_ini_y+word_w, background.shape[0])
		pos_ini_x2 = min(pos_ini_x+word_h, background.shape[1])

		self.foreground[pos_ini_y:pos_ini_y2, pos_ini_x:pos_ini_x2] = word[0:pos_ini_y2 - pos_ini_y, 0:pos_ini_x2 - pos_ini_x]
		self.foreground = self.foreground.astype(np.uint8)
			
		return True


	def add_arrows(self, background):
		"""
        Puts handwritten arrows in the foreground

        Parameters
        ----------
        background : Numpy array-like
        	2D Numpy matrix representing an image

        Returns
        ----------
        added : Boolean
        	True if element was added
        """

		pos = round(np.random.uniform(0, len(self.arrow_foreground) -1))  

		arrow = cv2.imread(self.arrow_foreground[pos].as_posix(), cv2.IMREAD_COLOR)
		arrow = cv2.cvtColor(arrow, cv2.COLOR_BGR2GRAY)

		angle = round(np.random.uniform(-90, 90))
		arrow = rotate_bound(arrow, angle)

		# limiarization foreground
		th = filters.threshold_sauvola(arrow, window_size=15, k=0.2)
		arrow = arrow > th
		arrow = arrow.astype('uint8')

		resized_arrow = cv2.resize(arrow, (round(np.random.uniform(150, 300)), round(np.random.uniform(150, 300))), interpolation = cv2.INTER_LINEAR)

		resized_arrow = resized_arrow.astype('uint8')

		arrow_w, arrow_h = resized_arrow.shape

		# choose the positions of the lines
		pos_ini_x = round(np.random.uniform(0, background.shape[1]))
		pos_ini_y = round(np.random.uniform(0, background.shape[0]))

		pos_ini_y2 = min(pos_ini_y+arrow_w, background.shape[0])
		pos_ini_x2 = min(pos_ini_x+arrow_h, background.shape[1])

		self.foreground[pos_ini_y:pos_ini_y2, pos_ini_x:pos_ini_x2] = resized_arrow[0:pos_ini_y2 - pos_ini_y, 0:pos_ini_x2 - pos_ini_x]
		self.foreground = self.foreground.astype(np.uint8)

			
		return True

# taken from https://pyimagesearch.com/2017/01/02/rotate-images-correctly-with-opencv-and-python/
def rotate_bound(image, angle):
	
	# grab the dimensions of the image and then determine the
	# center
	(h, w) = image.shape[:2]
	(cX, cY) = (w // 2, h // 2)
	
	# grab the rotation matrix (applying the negative of the
	# angle to rotate clockwise), then grab the sine and cosine
	# (i.e., the rotation components of the matrix)
	M = cv2.getRotationMatrix2D((cX, cY), -angle, 1.0)
	cos = np.abs(M[0, 0])
	sin = np.abs(M[0, 1])
	
	# compute the new bounding dimensions of the image
	nW = int((h * sin) + (w * cos))
	nH = int((h * cos) + (w * sin))
	
	# adjust the rotation matrix to take into account translation
	M[0, 2] += (nW / 2) - cX
	M[1, 2] += (nH / 2) - cY
	
	# perform the actual rotation and return the image
	return cv2.warpAffine(image, M, (nW, nH), borderMode=cv2.BORDER_CONSTANT, borderValue=(255,255,255))