import pyautogui
import keyboard
import pyscreeze
import time

RUNNING = True

while RUNNING:
    if keyboard.is_pressed("Space"):
        x,y = pyautogui.position()
        rgb = pyautogui.pixel(x,y)
        print(f"X:{x}   Y:{y}")
        print(f"{rgb}")
        offsetx,offsety = x - 421,y-133
        print (f"Offsetx:{offsetx}    Offsety:{offsety}")

    if keyboard.is_pressed('q'):
        print("Stopping")
        RUNNING = False               

    if keyboard.is_pressed('b'):
        pyautogui.moveTo(240,212)

    time.sleep(0.3)

#246 168 top left 
#261 183 bottom right        100% zoom
#15 size of cell

#251 194 top left
#274 217 bottom right        150% zoom          
#23  size of cell
# center 

#240 212 top left
#270 242 bottom right        200% zoom
#30 size of cell 
