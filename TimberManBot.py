# author: Gamer199
from time import sleep

from PIL import ImageGrab
import constant
import pyautogui
import threading
import queue

directions = queue.Queue()
directions.put("right")
directions.put("right")
pyautogui.hotkey("alt", "tab")
sleep(0.5)


def startbot():
    t = threading.Timer(0.28, startbot)
    t.start()
    px = ImageGrab.grab().load()
    
    colors = constant.COLORS

    direction = checkpixel(690, 834, 342, 378, px, colors, "right")
    if direction is True:
        direction = checkpixel(1133, 1241, 338, 374, px, colors, "left")
        if direction is True:
            directions.put(direction)
        else:
            directions.put(direction)
            directions.put(direction)
    else:
        directions.put(direction)
        directions.put(direction)

    if px[966, 1015] == constant.ARROW:
        t.cancel()

    while directions.qsize() > 2:
        direction = directions.get()
        if direction is True:
            direction = "right"
        pyautogui.press(direction)


def checkpixel(x1, x2, y1, y2, grabber, colors, direction):
    result = True
    for x in range(x1, x2, 18):
        for y in range(y1, y2, 18):
            if grabber[x, y] in colors:
                result = direction
    return result


startbot()

#2Player Coordinates
#ImageGrab.grab(bbox=(302, 338, 448, 377))
#ImageGrab.grab(bbox=(738, 338, 882, 377))