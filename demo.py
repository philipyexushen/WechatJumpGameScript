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
        self.__direction = True


    def _FindStartPoint(self, imgSnapshotGray:np.ndarray):
        matched = cv.matchTemplate(imgSnapshotGray, self.__imgTemplate, cv.TM_CCOEFF)
        loc = cv.minMaxLoc(matched)

        imgSzH, imgSzW = self.__imgShape
        startPoint = (int(loc[3][0] + imgSzW / 2), int(loc[3][1] + imgSzH))
        return startPoint


    def _FindEndOfMass(self, imgSnapshotGray:np.ndarray, startPoint):
        # imgSnapshotGray = cv.imread("E:\\Users\\Administrator\\pictures\\error\\snapshot82.png")
        imgSnapshotGray = cv.GaussianBlur(imgSnapshotGray, (5, 5), 1.8)
        #plt.imshow(imgSnapshotGray, cmap="gray")
        #plt.show()

        margin = cv.Canny(imgSnapshotGray, 1, 12)

        h, w = self.__imgShape
        for i in range(int(startPoint[0] - w / 2 - 1), int(startPoint[0] + w / 2 + 1)):
            for j in range(int(startPoint[1] - h - 100), startPoint[1]):
                margin[j, i] = 0

        margin[0:300] = 0
        #plt.imshow(margin, cmap="gray")
        #plt.show()


        res = np.where(margin == 0xff)
        posY = np.min(res[0][0])
        posX = np.mean(np.where(margin[posY] == 0xff)[0][0])

        posY += 18
        cv.circle(margin, (int(posX), int(posY)), 5, 255, -1)
        plt.imsave(f"E:\\Users\\Administrator\\pictures\\jump_game\\margin{_count}.jpg", margin, cmap="gray")

        return int(posX), int(posY)


    def Measure(self):
        os.system(f"adb shell screencap -p /sdcard/snapshot{_count}.png")
        os.system(f"adb pull /sdcard/snapshot{_count}.png")
        os.system(f"adb shell rm /sdcard/snapshot{_count}.png")

        imgSnapshot = cv.imread(f"snapshot{_count}.png")
        # imgSnapshot = cv.imread("E:\\Users\\Administrator\\pictures\\error\\snapshot2.png")

        imgSnapshot = cv.cvtColor(imgSnapshot, cv.COLOR_BGR2HSV)
        h, s, v = cv.split(imgSnapshot)
        s = cv.pow(np.float32(s), 1/1.2)
        cv.normalize(s, s, 0, 255, cv.NORM_MINMAX)
        imgSnapshot = cv.merge((h, np.uint8(s), v))
        imgSnapshot = cv.cvtColor(imgSnapshot, cv.COLOR_HSV2BGR)
        imgSnapshotGray = cv.cvtColor(imgSnapshot, cv.COLOR_BGR2GRAY)

        startPoint = self._FindStartPoint(imgSnapshotGray)
        endPoint = self._FindEndOfMass(imgSnapshotGray, startPoint)

        cv.circle(imgSnapshot, endPoint, 5, (0,0,255), -1)
        print(f"startPoint = {startPoint}, endPoint = {endPoint}")
        self.__distance = np.sqrt((startPoint[0] - endPoint[0]) ** 2 + (startPoint[1] - endPoint[1]) ** 2)
        self.__direction = startPoint[0] - endPoint[0] > 0  #大于零在左，小于零在右


    def Apply(self):
        dis = self.__distance
        global _count
        _count += 1
        intensity = 2.93 if self.__direction else 2.93
        print(f"[{_count}] distance = {dis} time = {dis * intensity}")
        os.system(f"adb shell input touchscreen swipe 320 410 320 410 { int(dis *intensity)}")


if __name__ == "__main__":
    count = 0
    imgTemplate =  cv.imread("E:\\Users\\Administrator\\pictures\\jump_game\\template.jpg", 0)
    wrapper = ScriptWrapper(imgTemplate)

    for i in range(2000):
        time.sleep(3)
        wrapper.Measure()
        wrapper.Apply()