import os
import cv2.cv2 as cv
import matplotlib.pyplot as plt
import numpy as np
import time

_count = 0

class ScriptWrapper:
    def __init__(self, imgTemplate:np.ndarray):
        self.__distance = 0
        self.__imgTemplate:np.ndarray = imgTemplate
        self.__imgShape = imgTemplate.shape


    def _FindStartPoint(self, imgSnapshotGray:np.ndarray):
        matched = cv.matchTemplate(imgSnapshotGray, self.__imgTemplate, cv.TM_CCOEFF)
        loc = cv.minMaxLoc(matched)

        imgSzH, imgSzW = self.__imgShape
        startPoint = (int(loc[3][0] + imgSzW / 2), int(loc[3][1] + imgSzH))
        return startPoint


    def _FindEndOfMass(self, imgSnapshotGray:np.ndarray, startPoint):
        imgSnapshotGray = cv.GaussianBlur(imgSnapshotGray, (5, 5), 0.8)
        margin = cv.Canny(imgSnapshotGray, 1, 8)

        h, w = self.__imgShape
        for i in range(int(startPoint[0] - w / 2 - 1), int(startPoint[0] + w / 2 + 1)):
            for j in range(int(startPoint[1] - h - 100), startPoint[1]):
                margin[j, i] = 0

        plt.imsave(f"E:\\Users\\Administrator\\pictures\\jump_game\\margin{_count}.jpg", margin, cmap="gray")
        # plt.imshow(margin, cmap="gray")
        # plt.show()

        margin[0:200] = 0
        res = np.where(margin == 0xff)
        posY = np.min(res[0][0])
        posX = np.mean(np.where(margin[posY] == 0xff)[0][0])
        return int(posX), int(posY + 20)


    def Measure(self):
        os.system(f"adb shell screencap -p /sdcard/snapshot{_count}.png")
        os.system(f"adb pull /sdcard/snapshot{_count}.png")
        os.system(f"adb shell rm /sdcard/snapshot{_count}.png")

        imgSnapshot = cv.imread(f"snapshot{_count}.png")
        imgSnapshotGray = cv.cvtColor(imgSnapshot, cv.COLOR_BGR2GRAY)

        startPoint = self._FindStartPoint(imgSnapshotGray)
        endPoint = self._FindEndOfMass(imgSnapshotGray, startPoint)

        cv.circle(imgSnapshot, endPoint, 5, (0,0,255), -1)
        print(f"startPoint = {startPoint}, endPoint = {endPoint}")
        self.__distance = np.sqrt((startPoint[0] - endPoint[0]) ** 2 + (startPoint[1] - endPoint[1]) ** 2)


    def Apply(self):
        dis = self.__distance
        global _count
        _count += 1
        print(f"[{_count}] distance = {dis} time = {dis *2.90}")
        os.system(f"adb shell input touchscreen swipe 320 410 320 410 { int(dis *2.95)}")


if __name__ == "__main__":
    count = 0
    imgTemplate =  cv.imread("E:\\Users\\Administrator\\pictures\\jump_game\\template.jpg", 0)
    wrapper = ScriptWrapper(imgTemplate)

    while True:
        time.sleep(3)
        wrapper.Measure()
        wrapper.Apply()