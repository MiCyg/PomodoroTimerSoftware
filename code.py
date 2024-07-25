import microcontroller
import watchdog
import alarm.pin
import board
import alarm
import time
import neopixel
import digitalio
from math import floor, ceil
from adafruit_debouncer import Debouncer, Button

LED_NUMBER = 8
BUTTON_PIN = board.GP22
LED_PIN = board.GP13

DISPLAY_DT_NS = 10000000

BRIGHTNESS_GLOBAL = 0.5

START_COLOR = (255,90,0)


POMODORO_TIME_MS = 25*1000*60
POMODORO_COLOR = (255,30,0)
POMODORO_COLOR_START = (255,30,0)
POMODORO_COLOR_END = (255,90,0)

BREAK_TIME_MS = 5*1000*60
BREAK_COLOR = (0,220,255)
BREAK_COLOR_START = (0,220,255)
BREAK_COLOR_END = (0,220,255)

LONG_BREAK_TIME_MS = 15*1000*60
LONG_BREAK_COLOR = (0,30,255)
LONG_BREAK_COLOR_START = (0,100,255)
LONG_BREAK_COLOR_END = (0,100,255)



MENU_BATTERY_COLOR = (255, 242, 0)
MENU_BRIGHTNESS_SET_COLOR = (0, 255, 110)
MENU_SLEEP_COLOR = (140, 0, 255)
MENU_BACK_COLOR = (255, 0, 0)



class CircDisplay:
	def __init__(self, led_pin:int, led_number:int):
		self.neop = neopixel.NeoPixel(led_pin, led_number, auto_write=False)
		self.neop.fill((0,0,0))
		self.neop.show()
		self.isEnable = True



	def enable(self, isEnable:bool):
		self.isEnable = isEnable
		self.neop.fill((0,0,0))
		self.neop.show()
		

	def send_draw(self, points:list[tuple]):
		if self.isEnable:
			for i, point in enumerate(points):
				self.neop[i] = point
			self.neop.show()



	def loop(self, pixels):
		self.send_draw(pixels)



class DisplayDrawer:
	def __init__(self, pixel_num):
		self.pixels = [(0,0,0)]*pixel_num
		self.pixel_num = pixel_num

	def get_pixels(self):
		return self.pixels

	@staticmethod
	def color_brightness(color, brightness):
		return (int(color[0]*brightness), int(color[1]*brightness), int(color[2]*brightness))
	
	@staticmethod
	def color_mean(color1, color2):
		return (int((color1[0]+color2[0])*0.5), int((color1[1]+color2[1])*0.5), int((color1[2]+color2[2])*0.5))

	@staticmethod
	def color_sum(color1, color2):
		return (min(int(color1[0]+color2[0]),255), min(int(color1[1]+color2[1]),255), min(int((color1[2]+color2[2])),255))

	def clear(self):
		for i in range(self.pixel_num):
			self.pixels[i] = (0,0,0)

	def point(self, coord:float, color:tuple):
		point_position = (coord * self.pixel_num)%self.pixel_num

		idx_left = floor(point_position)
		idx_right = ceil(point_position)

		if idx_left == idx_right:
			self.pixels[idx_right] = DisplayDrawer.color_sum(self.pixels[idx_right], color)
		else:
			# DisplayDrawer.color_sum(DisplayDrawer.color_brightness(color, abs(idx_right-point_position)), self.pixels[idx_left%self.pixel_num])
			self.pixels[idx_right%self.pixel_num] = DisplayDrawer.color_sum(DisplayDrawer.color_brightness(color, abs(point_position-idx_left)), self.pixels[idx_right%self.pixel_num])
			self.pixels[idx_left%self.pixel_num] = DisplayDrawer.color_sum(DisplayDrawer.color_brightness(color, abs(idx_right-point_position)), self.pixels[idx_left%self.pixel_num])

	def fill(self, color:tuple):
		for i in range(self.pixel_num):
			self.pixels[i] = DisplayDrawer.color_sum(color, self.pixels[i])

	def set_brightness(self, brightness):
		for i in range(self.pixel_num):
			self.pixels[i] = DisplayDrawer.color_brightness(self.pixels[i], brightness)


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
			self.start_time = time.monotonic_ns()/1000000
		else:
			self.start_time = time.monotonic_ns()/1000000 - (self.pause_time - self.start_time)
		self.pause_time = None



	def actual_time(self) -> int:
		if self.pause_time:
			return self.pause_time - self.start_time
		else:
			return time.monotonic_ns()/1000000 - self.start_time

	def pause(self) -> None:
		self.pause_time = time.monotonic_ns()/1000000

	def reset(self) -> None:
		self.pause_time = None
		self.start_time = 0
	

	def is_end(self) -> bool:
		if time.monotonic_ns()/1000000 - self.start_time > self.set_time_ms:
			return True
		else:
			return False




class ButtonWrapper:
	def __init__(self, button_pin, long_press_time_ms=1500, debouncing_time_ms=100):
		self.pin = digitalio.DigitalInOut(button_pin)
		self.pin.direction = digitalio.Direction.INPUT
		self.pin.pull = digitalio.Pull.UP
		self.button = Button(self.pin, debouncing_time_ms, long_press_time_ms)


	def set_short_press_callback(self, callback:function) -> None:
		self.short_press_func = callback

	def set_long_press_callback(self, callback:function) -> None:
		self.long_press_func = callback
	
	def loop(self) -> None:
		self.button.update()

		if self.button.pressed:
			if self.short_press_func:
				self.short_press_func()

		if self.button.long_press:
			print("long_press")
			if self.long_press_func:
				self.long_press_func()

	def state(self) -> bool:
		return bool(self.button.value())

	def deinit(self):
		del self.button
		self.pin.deinit()

	

class Animation:
	def __init__(self, pixel_num, animation_time):
		self.drawer = DisplayDrawer(pixel_num)
		self.timer = Timer()
		# assert(animation_time == 0)
		self.timer.set(animation_time)
		# print("animation time", animation_time)
		# print("timer set", self.timer.set_time_ms)


	def loop(self):
		pass

	def start(self):
		self.timer.start()

	def stop(self):
		self.timer.pause()

	def restart(self):
		self.timer.reset()
		self.timer.start()

	def get_pixels(self):
		return self.drawer.get_pixels()


class RotatingPoint(Animation):
	DIRECTION_RIGHT = 1
	DIRECTION_LEFT = 2

	def __init__(self, pixel_num, animation_time, color, direction, brightness=1.0,callback=None):
		super().__init__(pixel_num, animation_time)
		self.color = color
		self.direction = direction
		self.anim_dt = 10
		self.brightness = brightness
		self.end_cb = callback


	def loop(self):
		# print(self.timer.set_time_ms, self.timer.actual_time())
		if self.direction == RotatingPoint.DIRECTION_RIGHT:
			ratio = self.timer.actual_time() / self.timer.set_time_ms
		elif self.direction == RotatingPoint.DIRECTION_LEFT:
			ratio = 1 - (self.timer.actual_time() / self.timer.set_time_ms)
		if ratio >= 1:
			self.timer.reset()
			if self.end_cb:
				self.end_cb()
			else:
				self.timer.start()
		# ratio = 0
		self.drawer.clear()
		# print(self.drawer.get_pixels())
		self.drawer.point(ratio, self.color)
		self.drawer.set_brightness(self.brightness)
		# print(self.drawer.get_pixels())

class PomodoroTimer(Animation):
	def __init__(self, pixel_num, animation_time, color, brightness=1.0, callback=None):
		super().__init__(pixel_num, animation_time)
		self.color = color
		self.anim_dt = 10
		self.brightness = brightness
		self.end_cb = callback

	def draw_pomodoro(self, ratio, color):

		fullLedsNumber = (ratio * self.drawer.pixel_num)%self.drawer.pixel_num

		idx = -1
		for idx in range(int(fullLedsNumber)):
			color = self.drawer.color_sum(self.drawer.get_pixels()[idx], color)
			self.drawer.point(idx/self.drawer.pixel_num, color)
			

		if fullLedsNumber < self.drawer.pixel_num:
			color = self.drawer.color_brightness(color, (fullLedsNumber-int(fullLedsNumber)))
			self.drawer.point((idx+1)/self.drawer.pixel_num, self.drawer.color_sum(self.drawer.get_pixels()[idx+1], color))


	def loop(self):
		# print(self.timer.set_time_ms, self.timer.actual_time())

		ratio = self.timer.actual_time() / self.timer.set_time_ms
		if ratio >= 1:
			self.timer.reset()
			if self.end_cb:
				self.end_cb()
			else:
				self.timer.start()
		# ratio = 0
		self.drawer.clear()
		# print(self.drawer.get_pixels())
		self.draw_pomodoro(ratio, self.color)
		self.drawer.set_brightness(self.brightness)
		# self.drawer.point(ratio, self.drawer.color_brightness(self.color, 0.5))
		# print(self.drawer.get_pixels())

class PulseFill(Animation):

	START_MAX = 0
	START_MIN = 1

	def __init__(self, pixel_num, animation_time, color, start_point, brightness=1.0, callback=None):
		super().__init__(pixel_num, animation_time)
		self.color = color
		self.anim_dt = 10
		self.start_point = start_point
		self.brightness = brightness
		self.end_cb = callback


	def loop(self):

		ratio = self.timer.actual_time() / self.timer.set_time_ms
		if ratio >= 1:
			self.timer.reset()
			if self.end_cb:
				self.end_cb()
			else:
				self.timer.start()

		brightness = 0

		self.drawer.clear()

		if ratio<0.5:
			brightness = ratio*2
		elif ratio>=0.5 and ratio <1:
			brightness = -(ratio*2)+2

		if self.start_point == PulseFill.START_MIN:
			brightness = brightness
		elif self.start_point == PulseFill.START_MAX:
			brightness = 1-brightness
		
		self.drawer.fill(DisplayDrawer.color_brightness(self.color, brightness))
		self.drawer.set_brightness(self.brightness)

		# self.drawer.point(ratio, self.drawer.color_brightness(self.color, 0.5))
		# print(self.drawer.get_pixels())


class PulsePoint(Animation):

	def __init__(self, pixel_num, animation_time, color, point_ratio, brightness=1.0, callback=None):
		super().__init__(pixel_num, animation_time)
		self.color = color
		self.anim_dt = 10
		self.point_ratio = point_ratio
		self.brightness = brightness
		self.end_cb = callback


	def loop(self):
		ratio = self.timer.actual_time() / self.timer.set_time_ms
		if ratio >= 1:
			self.timer.reset()
			if self.end_cb:
				self.end_cb()
			else:
				self.timer.start()

		brightness = 0

		self.drawer.clear()

		if ratio<0.5:
			brightness = ratio*2
		elif ratio>=0.5 and ratio <1:
			brightness = -(ratio*2)+2

		self.drawer.point(self.point_ratio, DisplayDrawer.color_brightness(self.color, brightness))
		self.drawer.set_brightness(self.brightness)

		# self.drawer.point(ratio, self.drawer.color_brightness(self.color, 0.5))
		# print(self.drawer.get_pixels())

class Point(Animation):

	def __init__(self, pixel_num, color, point_ratio, brightness=1.0, callback=None):
		super().__init__(pixel_num, 1)
		self.color = color
		self.point_ratio = point_ratio
		self.brightness = brightness
		self.end_cb = callback


	def loop(self):

		self.drawer.clear()
		self.drawer.point(self.point_ratio, self.color)
		self.drawer.set_brightness(self.brightness)


class AnimationContainer:
	def __init__(self, pixel_num:int, animations=None):
		if animations:
			self.animations = animations
		else:
			self.animations = []
		self.pixel_num=pixel_num

	def append(self, animation):
		self.animations.append(animation)

	def loop(self):
		for anim in self.animations:
			anim.loop()
	
	def start(self):
		for anim in self.animations:
			anim.start()

	def stop(self):
		for anim in self.animations:
			anim.stop()
		

	def restart(self):
		for anim in self.animations:
			anim.restart()

	def get_pixels(self):
		# print("baba")
		ret_pixels = [(0,0,0)]*self.pixel_num
		# print(ret_pixels)
		for anim in self.animations:
			# print(anim)
			anim_pixels = anim.get_pixels()
			for i in range(self.pixel_num):
				ret_pixels[i] = DisplayDrawer.color_sum(ret_pixels[i], anim_pixels[i])
		
		# print(ret_pixels)
		return ret_pixels
	
	def get_animations(self):
		return self.animations
	
class PomodoroTimerContainer(AnimationContainer):
	def __init__(self, pixel_num:int, color, time, brightness, callback):
		super().__init__(pixel_num)
		self._build(color, time, brightness, callback)


	def _build(self, color, time, brightness, cb):

		self.append(RotatingPoint(LED_NUMBER, 2000, color, RotatingPoint.DIRECTION_RIGHT, 0.5*brightness))
		self.append(PomodoroTimer(LED_NUMBER, time, color, 0.5*brightness, cb))

class PomodoroEndContainer(AnimationContainer):
	def __init__(self, pixel_num:int, color, brightness, startPoint=None):
		super().__init__(pixel_num)
		self._build(color, brightness, startPoint)


	def _build(self, color, brightness, startPoint):
		endPulseTime = 1000

		self.append(RotatingPoint(LED_NUMBER, 2137, color, RotatingPoint.DIRECTION_RIGHT, 0.3*brightness))
		self.append(RotatingPoint(LED_NUMBER, 2666, color, RotatingPoint.DIRECTION_LEFT, 0.3*brightness))
		if not startPoint:
			self.append(PulseFill(LED_NUMBER, endPulseTime, color, PulseFill.START_MAX, 0.3*brightness))
		else:
			self.append(PulseFill(LED_NUMBER, endPulseTime, color, PulseFill.START_MIN, 0.3*brightness))


class MenuContainer(AnimationContainer):
	def __init__(self, pixel_num:int):
		super().__init__(pixel_num)

		self.choose_menu = 0
		self.colors = [MENU_BATTERY_COLOR, MENU_BRIGHTNESS_SET_COLOR, MENU_SLEEP_COLOR, MENU_BACK_COLOR]

		self._build_menu(self.choose_menu)


	def _build_menu(self, choose_num):
		self.animations = []
		for i, col in enumerate(self.colors):
			if i != choose_num:
				self.append(Point(LED_NUMBER, col, i*2/LED_NUMBER, BRIGHTNESS_GLOBAL))
			else:
				self.append(PulsePoint(LED_NUMBER, 500, col, i*2/LED_NUMBER, BRIGHTNESS_GLOBAL))


	def change_menu(self, choose_num):
		for i, col in enumerate(self.colors):
			if i != choose_num:
				self.animations[i] = Point(LED_NUMBER, col, i*2/LED_NUMBER, BRIGHTNESS_GLOBAL)
			else:
				self.animations[i] = PulsePoint(LED_NUMBER, 500, col, i*2/LED_NUMBER, BRIGHTNESS_GLOBAL)

	def perform_action(self):
		self.choose_menu-=1
		self.choose_menu=self.choose_menu % len(self.animations)
		self.change_menu(self.choose_menu)

		if self.choose_menu == 3:
			print("back")


	def hop_menu(self):
		self.choose_menu+=1
		self.choose_menu=self.choose_menu % len(self.animations)

		self.change_menu(self.choose_menu)






class Core:
	def __init__(self):

		self.butt = ButtonWrapper(BUTTON_PIN)

		self.display = CircDisplay(LED_PIN, LED_NUMBER)

		self.menuContainer = MenuContainer(LED_NUMBER)
		
		pomodoroTimerContainer = PomodoroTimerContainer(LED_NUMBER, POMODORO_COLOR, POMODORO_TIME_MS, BRIGHTNESS_GLOBAL, self.increment_sequence)
		pomodoroEndContainer = PomodoroEndContainer(LED_NUMBER, POMODORO_COLOR, BRIGHTNESS_GLOBAL)

		breakTimerContainer = PomodoroTimerContainer(LED_NUMBER, BREAK_COLOR, BREAK_TIME_MS, BRIGHTNESS_GLOBAL, self.increment_sequence)
		breakEndContainer = PomodoroEndContainer(LED_NUMBER, BREAK_COLOR, BRIGHTNESS_GLOBAL)

		longBreakTimerContainer = PomodoroTimerContainer(LED_NUMBER, LONG_BREAK_COLOR, LONG_BREAK_TIME_MS, BRIGHTNESS_GLOBAL, self.increment_sequence)
		longBreakEndContainer = PomodoroEndContainer(LED_NUMBER, LONG_BREAK_COLOR, BRIGHTNESS_GLOBAL)

		goToSleepContainer = PomodoroEndContainer(LED_NUMBER, POMODORO_COLOR, BRIGHTNESS_GLOBAL)

		self.anim_containers = [

			pomodoroTimerContainer,
			pomodoroEndContainer,
			breakTimerContainer,
			breakEndContainer,

			pomodoroTimerContainer,
			pomodoroEndContainer,
			breakTimerContainer,
			breakEndContainer,

			pomodoroTimerContainer,
			pomodoroEndContainer,
			breakTimerContainer,
			breakEndContainer,

			pomodoroTimerContainer,
			pomodoroEndContainer,
			longBreakTimerContainer,
			longBreakEndContainer,
		]

		self.wake_up()



	def increment_sequence(self):
		
		self.animation_idx += 1
		self.animation_idx = self.animation_idx %len(self.anim_containers)

		self.actual_animationContainer = self.anim_containers[self.animation_idx]

		self.actual_animationContainer.restart()
		
		print("anim:", self.animation_idx)

	def go_to_menu(self):
		self.actual_animationContainer = self.menuContainer
		self.butt.set_short_press_callback(self.menuContainer.hop_menu)
		self.butt.set_long_press_callback(self.menuContainer.perform_action)



	def prepare_to_sleep(self):
		self.display.enable(False)
		self.butt.set_short_press_callback(None)
		self.butt.set_long_press_callback(None)
		self.butt.deinit()
		self.wdt.deinit()
		time.sleep(2)

		pinAlarm = alarm.pin.PinAlarm(BUTTON_PIN, value=False, pull=True)
		alarm.exit_and_deep_sleep_until_alarms(pinAlarm)

		print('THIS MESSAGE SHOULD NEVER HAPPEN!')



	
	def wake_up(self):

		print("WAKE UP!")
		self.display.enable(True)
		self.actual_animationContainer = PomodoroEndContainer(LED_NUMBER, START_COLOR, BRIGHTNESS_GLOBAL, 1)

		self.animation_idx = -1

		self.actual_animationContainer.start()

		self.butt.set_short_press_callback(self.increment_sequence)
		self.butt.set_long_press_callback(self.prepare_to_sleep)

		self.wdt = microcontroller.watchdog
		self.wdt.timeout = 8
		self.wdt.mode = watchdog.WatchDogMode.RESET

		
	def run(self):
		disp_time = 0
		while True:
			self.butt.loop()

			if time.monotonic_ns() - disp_time > DISPLAY_DT_NS:
				disp_time = time.monotonic_ns()
				self.actual_animationContainer.loop()

				pixels = self.actual_animationContainer.get_pixels()
				# print(pixels)
				self.display.loop(pixels)
			
			self.wdt.feed()



if __name__ == '__main__':
	core = Core()
	core.run()


