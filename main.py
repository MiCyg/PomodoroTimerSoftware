import machine
import time
import neopixel
from math import floor, ceil



LED_NUMBER = 8
BUTTON_PIN = 22
LED_PIN = 13

BRIGHTNESS = 0.1

POMODORO_END_COLOR = (255,255,255)

POMODORO_TIME_MS = 25*60*1000
POMODORO_COLOR = (255,30,0)

BREAK_TIME_MS = 5*60*1000
BREAK_COLOR = (0,100,255)

LONG_BREAK_TIME_MS = 15*60*1000
LONG_BREAK_COLOR = (0,220,255)


class CircDisplay:
	def __init__(self, led_pin:int, led_number:int):
		self.neop = neopixel.NeoPixel(machine.Pin(led_pin), led_number)
		# self.dt = dt_ms

		self.sample_timer = 0
		self.point_run_ms = 1500

		self.actual_color = POMODORO_COLOR

	@staticmethod
	def color_brightness(color, brightness):
		return (int(color[0]*brightness), int(color[1]*brightness), int(color[2]*brightness))
	
	@staticmethod
	def color_mean(color1, color2):
		return (int((color1[0]+color2[0])*0.5), int((color1[1]+color2[1])*0.5), int((color1[2]+color2[2])*0.5))

	@staticmethod
	def color_sum(color1, color2):
		
		return (min(int(color1[0]+color2[0]),255), min(int(color1[1]+color2[1]),255), min(int((color1[2]+color2[2])),255))

	def set_brightness(self, brightness):
		for i in range(self.neop.__len__()):
			self.neop[i] = CircDisplay.color_brightness(self.neop[i], brightness)

	def clear(self):
		self.neop.fill((0,0,0))

	def draw_pomodoro(self, ratio, color):

		fullLedsNumber = (ratio * LED_NUMBER)%LED_NUMBER

		idx = -1
		for idx in range(int(fullLedsNumber)):
			self.neop[idx] = CircDisplay.color_sum(self.neop[idx], color)

		if fullLedsNumber < LED_NUMBER:
			color = CircDisplay.color_brightness(color, (fullLedsNumber-int(fullLedsNumber)))
			self.neop[idx+1] = CircDisplay.color_sum(self.neop[idx+1], color)
		
	def draw_point(self, ratio:float, color:tuple):

		point_position = (ratio * LED_NUMBER)%LED_NUMBER

		idx_left = floor(point_position)
		idx_right = ceil(point_position)

		if idx_left == idx_right:
			self.neop[idx_right] = CircDisplay.color_sum(self.neop[idx_right], color)
		else:
			# CircDisplay.color_sum(CircDisplay.color_brightness(color, abs(idx_right-point_position)), self.neop[idx_left%LED_NUMBER])
			self.neop[idx_right%LED_NUMBER] = CircDisplay.color_sum(CircDisplay.color_brightness(color, abs(point_position-idx_left)), self.neop[idx_right%LED_NUMBER])
			self.neop[idx_left%LED_NUMBER] = CircDisplay.color_sum(CircDisplay.color_brightness(color, abs(idx_right-point_position)), self.neop[idx_left%LED_NUMBER])

	def fill(self, color:tuple):
		for i in range(LED_NUMBER):
			self.neop[i] = CircDisplay.color_sum(color, self.neop[i])

	def write(self):
		self.neop.write()

	'''
		def loop(self, time_ms:int):
			
			if (time_ms - self.sample_timer) > self.dt:
				self.sample_timer = time_ms
				self.neop.fill((0,0,0))

				point_ratio = (time_ms % self.point_run_ms) / self.point_run_ms
				self.draw_point(point_ratio, CircDisplay.color_brightness(self.actual_color, 0.1))

				pomodorro_ratio = (time_ms % POMODORO_TIME_MS) / POMODORO_TIME_MS
				self.draw_pomodoro(pomodorro_ratio, POMODORO_COLOR)


				self.set_brightness(BRIGHTNESS)

				self.neop.write()
	'''

class Timer:
	def __init__(self):
		self.pause_time = None
		self.start_time = 0
		self.set_time_ms = 0

	def set(self, time_ms:int)  -> None:
		self.pause_time = None
		self.start_time = 0
		self.set_time_ms = time_ms
	
	def start(self) -> None:
		if not self.pause_time:
			self.start_time = time.ticks_ms()
		else:
			self.start_time = time.ticks_ms() - (self.pause_time - self.start_time)
		self.pause_time = None



	def actual_time(self) -> int:
		if self.pause_time:
			return self.pause_time - self.start_time
		else:
			return time.ticks_ms() - self.start_time

	def pause(self) -> None:
		self.pause_time = time.ticks_ms()

	def reset(self) -> None:
		self.pause_time = None
		self.start_time = 0
		self.set_time_ms = 0
	

	def is_end(self) -> bool:
		if time.ticks_ms() - self.start_time > self.set_time_ms:
			return True
		else:
			return False

class Animation:

	def __init__(self, display:CircDisplay, sample_ms:int=50):
		self.display = display
		self.display.clear()
		self.display.write()

		self.dt_ms = sample_ms
		self.last_tick_ms = 0

		self.anim_kind = 0
		self.anim_kind_save = 0
		self.timer = Timer()
		self.pulseTimer = Timer()
		self.blink_time = 1000
		self.point_time = 3000
		self.point_brightness = 0.5

		self.color = (0,0,0)

		self.disp_screenshot = []





	def time_estimation(self):
		point_ratio = self.timer.actual_time()%self.point_time / self.point_time
		self.display.draw_point(point_ratio, CircDisplay.color_brightness(self.color, self.point_brightness))

		pomodorro_ratio = self.timer.actual_time() / self.timer.set_time_ms
		self.display.draw_pomodoro(pomodorro_ratio, self.color)


	def blink(self):

		if self.timer.is_end():
			self.timer.set(self.timer.set_time_ms)
			self.timer.start()

		if self.timer.actual_time() > 500:
			self.display.fill((0,0,0))
		
		elif self.timer.actual_time() > 0:
			self.display.fill(self.color)

		
	def pulse(self):
		if self.timer.is_end():
			self.timer.set(self.timer.set_time_ms)
			self.timer.start()
		br = 0
		if self.timer.actual_time() >= self.timer.set_time_ms/2:
			br = (self.timer.actual_time()/self.timer.set_time_ms*2)-1
		
		elif self.timer.actual_time() >= 0:
			br = 1-(self.timer.actual_time()/self.timer.set_time_ms*2)

		self.display.fill(CircDisplay.color_brightness(self.color, br))
		
	def pulse_save(self):
		if self.pulseTimer.is_end():
			self.pulseTimer.set(self.pulseTimer.set_time_ms)
			self.pulseTimer.start()

		# print(self.timer.actual_time())
		self.time_estimation()

		br = 0
		if self.pulseTimer.actual_time() >= self.pulseTimer.set_time_ms/2:
			br = (self.pulseTimer.actual_time()/self.pulseTimer.set_time_ms*2)-1
		
		elif self.pulseTimer.actual_time() >= 0:
			br = 1-(self.pulseTimer.actual_time()/self.pulseTimer.set_time_ms*2)

		self.display.set_brightness(br)
		
	def stop_and_pulse(self):
		self.timer.pause()
		self.pulseTimer.set(2000)
		self.pulseTimer.start()
		self.anim_kind_save = self.anim_kind
		self.anim_kind = 3
		
	def start_and_pulse(self):
		self.timer.start()
		self.pulseTimer.pause()
		self.anim_kind = self.anim_kind_save
		

	def set(self, anim_kind:int, anim_time:int):
		self.anim_kind = anim_kind
		self.timer.set(anim_time)
		self.timer.start()


	def loop(self):
		if (time.ticks_ms() - self.last_tick_ms) > self.dt_ms:
			self.last_tick_ms = time.ticks_ms()

			self.display.clear()

			if self.anim_kind == 0:
				self.blink()
			elif self.anim_kind == 1:
				self.time_estimation()

				if self.timer.is_end():
					self.anim_kind = 2
					self.timer.set(3000)

			elif self.anim_kind == 2:
				self.pulse()

			elif self.anim_kind == 3:
				self.pulse_save()
			

			self.display.set_brightness(BRIGHTNESS)

			self.display.write()

class ButtonWrapper:
	def __init__(self, button_pin, long_press_time_ms=1500, debouncing_time_ms=150):
		self.timer = Timer()

		self.button = machine.Pin(button_pin, machine.Pin.IN, machine.Pin.PULL_UP)
		self.deb_time_ms = debouncing_time_ms
		self.long_press_time_ms = long_press_time_ms

		self.state = 0

		self.short_press = False
		self.long_press = False

	def is_short_press(self):
		a = self.short_press
		self.short_press = False
		return a

	def is_long_press(self):
		a = self.long_press
		self.long_press = False
		return a

	def loop(self):
		if self.state == 0:
			if not self.button.value():
				self.state = 1
				self.timer.set(self.deb_time_ms)
				self.timer.start()

		elif self.state == 1:
			if self.timer.is_end():
				if self.button.value():
					self.state = 2
				else:
					self.state = 3

		elif self.state == 2:
			self.short_press = True
			self.timer.set(self.long_press_time_ms)
			self.timer.start()
			self.state = 3

		elif self.state == 3:
			if self.button.value():
				self.state = 0
			elif self.timer.is_end():
				self.state = 4

		elif self.state == 4:
			self.long_press = True
			self.state = 5

		elif self.state == 5:
			if self.button.value():
				self.state = 0

class Core:
	def __init__(self):
		display = CircDisplay(LED_PIN, LED_NUMBER)
		self.anim = Animation(display)
		self.butt = ButtonWrapper(BUTTON_PIN)
		self.i = 0

		self.pom_list = [
			("pomodoro", 1, POMODORO_TIME_MS, POMODORO_COLOR),
			("short break", 1, BREAK_TIME_MS, BREAK_COLOR),
			("long break", 1, LONG_BREAK_TIME_MS, LONG_BREAK_COLOR),
		]
		self.pom_idx = 0

		self.anim.set(0, 1000)
		self.anim.color = self.pom_list[self.pom_idx][3]
		self.state = 0


	def run(self):

		while True:
			self.butt.loop()
			self.anim.loop()

			# print(self.state, self.anim.timer.actual_time())
			# choose type pomodoroo
			if self.state == 0:
				if self.butt.is_short_press():
					self.pom_idx += 1
					self.pom_idx %= len(self.pom_list)
					self.anim.set(0, 1000)
					self.anim.color = self.pom_list[self.pom_idx][3]
				

				if self.butt.is_long_press():
					print(self.pom_list[self.pom_idx][0])
					self.anim.color = self.pom_list[self.pom_idx][3]
					self.anim.set(1, self.pom_list[self.pom_idx][2])
					self.state = 1


			# pomodoro running
			elif self.state == 1:

				if self.anim.timer.is_end():
					self.state = 3


				if self.butt.is_short_press():
					# self.anim.set(3, self.pom_list[self.pom_idx][2])
					self.anim.stop_and_pulse()
					self.state = 2
					

				if self.butt.is_long_press():
					self.anim.set(0, self.pom_list[self.pom_idx][2])
					self.state = 0

			# pomodoro pause
			elif self.state == 2:
				if self.butt.is_short_press():
					self.anim.start_and_pulse()
					self.state = 1
					
			elif self.state == 3:
				if self.butt.is_short_press():
					self.pom_idx += 1
					self.pom_idx %= len(self.pom_list)
					self.anim.set(1, self.pom_list[self.pom_idx][2])
					self.anim.color = self.pom_list[self.pom_idx][3]
					self.state = 1
					

if __name__ == '__main__':
	core = Core()
	core.run()

