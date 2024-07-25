# PomodoroTimer

Project in production

![pomodoroTimer](images/pomodoroTimer.gif)

## Description


The PomodoroTimer is a tool designed to assist with implementing the [Pomodoro Technique](https://en.wikipedia.org/wiki/Pomodoro_Technique) for both work and study. This technique is a time management method that uses a timer to break work into intervals, traditionally 25 minutes in length, separated by 5 minutes breaks.

## Features

- Built using the Raspberry Pi RP2040 microcontroller.
- Utilizes WS2812B programmable LEDs for visual feedback.
- Incorporates my previous repository, [LedRing](https://github.com/MiCyg/LedRing), which proved to be an ideal solution for this project.
- Developed with CircuitPython for rapid and aesthetic implementation, leveraging polymorphism and class inheritance.

## Case 
If you have some diy skills probably can you build your own enclosure. 
Although if you do not have time for it, can you simply download and print my version. 
Enclosure is prepared for 3D print. Stls are avaliable on [stl](stl) folder. Assembly Should be simple, as shown below.

![case assembly](images/assembly.gif)


## Firmware usage

To program and use the PomodoroTimer, follow these steps:
- Ensure you have CircuitPython installed on your Raspberry Pi RP2040.
- Upload the PomodoroTimer code to your RP2040.
- Run the code and start managing your time effectively with the Pomodoro Technique.

## Instruction
After upload code timer has orange blinking light color. After short press button pomodoro timer start counting up to twenty five minutes. Leds slowly fill up a circle to strong red color. When time has to come, leds start blinking. Next short button press starts break timer has count up to fife minutes.

If you end of study or work, you can power off device by long press button.

## Contributing

Contributions are welcome! If you have any ideas or suggestions, please open an issue or submit a pull request. 


