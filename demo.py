import os
import cv2.cv2 as cv
import matplotlib.pyplot as plt
import numpy as np
import time

_count = 0

class ScriptWrapper:
    def __init__(self, imgListChessTemplate:list, imgWhitePointTemplate:np.ndarray):
        self.__distance = 0
        self.__imgListChessTemplate:np.ndarray = imgListChessTemplate
        self.__imgWhitePointTemplate: np.ndarray = imgWhitePointTemplate
        self.__bIsWhitePointMatched = False
        self.__matchedChessTemplate = None


    def _FindStartPoint(self, imgSnapshotGray:np.ndarray):
        startPoint = (-1, -1)
        for i in range(len(self.__imgListChessTemplate)):
            t = self.__imgListChessTemplate[i]
            matched = cv.matchTemplate(imgSnapshotGray, t, cv.TM_CCOEFF_NORMED)
            minVal, maxVal, minLoc, maxLoc = cv.minMaxLoc(matched)

            if maxVal >= 0.5 or i == len(self.__imgListChessTemplate) - 1:
                imgSzH, imgSzW = t.shape
                startPoint = (int(maxLoc[0] + imgSzW / 2), int(maxLoc[1] + imgSzH))
                self.__matchedChessTemplate = t

        return startPoint


    def _FindEndOfMass(self, imgSnapshotGray:np.ndarray, startPoint):
        imgSnapshotGray = cv.GaussianBlur(imgSnapshotGray, (5, 5), 1.9)
        #plt.imshow(imgSnapshotGray, cmap="gray")
        #plt.show()

        res = cv.matchTemplate(imgSnapshotGray, self.__imgWhitePointTemplate, cv.TM_CCOEFF_NORMED)
        minVal, maxVal, minLoc, maxLoc = cv.minMaxLoc(res)

        if maxVal >= 0.965:
            wth, wtw = self.__imgWhitePointTemplate.shape
            posX = maxLoc[0] + wtw / 2
            posY = maxLoc[1] + wth / 2
            self.__bIsWhitePointMatched = True
            print("White point matched")
        else:
            margin = cv.Canny(imgSnapshotGray, 1, 12)

            h, w = self.__matchedChessTemplate.shape
            for i in range(int(startPoint[0] - w / 2 - 20), int(startPoint[0] + w / 2 + 20)):
                for j in range(int(startPoint[1] - h - 100), startPoint[1]):
                    margin[j, i] = 0

            margin[0:300] = 0
            margin[:, 0:40] = 0
            margin[:, margin.shape[1] - 40: margin.shape[1]] = 0
            kernel = np.ones([2, 3] ,dtype=np.uint8)
            margin = cv.morphologyEx(margin, cv.MORPH_DILATE, kernel)
            lines = cv.HoughLinesP(margin, 1, np.pi/180, 12, minLineLength=10)
            if not lines is None:
                for errorLine in lines:
                    if -3 <= errorLine[0, 1] - errorLine[0, 3] <= 3:
                        # print(errorLine[0, 1], errorLine[0, 2])
                        margin[errorLine[0, 1] - 3 : errorLine[0, 1] + 3] = 0

            # plt.imshow(margin, cmap="gray")
            # plt.show()

            res = np.where(margin == 0xff)
            posY = np.min(res[0][0])
            posX = np.mean(np.where(margin[posY] == 0xff)[0][0]) + 3
            posY += 16

            self.__bIsWhitePointMatched = False
            cv.circle(margin, (int(posX), int(posY)), 5, 255, -1)
            plt.imsave(f"E:\\Users\\Administrator\\pictures\\jump_game\\margin\\margin{_count}.jpg", margin, cmap="gray")

        return int(posX), int(posY)


    def Measure(self):
        os.system(f"adb shell screencap -p /sdcard/snapshot{_count}.png")
        os.system(f"adb pull /sdcard/snapshot{_count}.png -p E:\\Users\\Administrator\\pictures\\jump_game\\origin\\snapshot{_count}.png")
        os.system(f"adb shell rm /sdcard/snapshot{_count}.png")

        imgSnapshot = cv.imread(f"E:\\Users\\Administrator\\pictures\\jump_game\\origin\\snapshot{_count}.png")
        #imgSnapshot = cv.imread("E:\\Users\\Administrator\\pictures\\error\\snapshot321.png")

        imgSnapshot = cv.cvtColor(imgSnapshot, cv.COLOR_BGR2HSV)
        h, s, v = cv.split(imgSnapshot)
        s = cv.pow(np.float32(s), 1/2.4)
        v = cv.pow(np.float32(v), 1/1.8)
        cv.normalize(s, s, 0, 255, cv.NORM_MINMAX)
        cv.normalize(v, v, 0, 255, cv.NORM_MINMAX)
        imgSnapshot = cv.merge((h, np.uint8(s), np.uint8(v)))
        imgSnapshot = cv.cvtColor(imgSnapshot, cv.COLOR_HSV2BGR)
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

        if dis < 180:
            intensity = 2.98
        elif dis < 250:
            intensity = 2.97 if not self.__bIsWhitePointMatched else 2.96
        else:
            intensity = 2.94 if not self.__bIsWhitePointMatched else 2.95

        print(f"[{_count}] distance = {dis} time = {dis * intensity}")
        os.system(f"adb shell input touchscreen swipe 320 410 320 410 { int(dis *intensity)}")


if __name__ == "__main__":
    count = 0
    os.system("cd E:\\Users\\Administrator\\pictures\\jump_game\\origin")

    # 模板大小都是
    listTemplate = list()
    imgChessTemplate1 =  cv.imread("E:\\Users\\Administrator\\pictures\\jump_game\\template1.jpg", 0)
    listTemplate.append(imgChessTemplate1)

    imgChessTemplate2 = cv.imread("E:\\Users\\Administrator\\pictures\\jump_game\\template2.jpg", 0)
    listTemplate.append(imgChessTemplate2)

    imgChessTemplate3 = cv.imread("E:\\Users\\Administrator\\pictures\\jump_game\\template3.jpg", 0)
    listTemplate.append(imgChessTemplate3)

    imgWhitePointTemplate = cv.imread("E:\\Users\\Administrator\\pictures\\jump_game\\whitePoint.jpg", 0)
    wrapper = ScriptWrapper(listTemplate, imgWhitePointTemplate)

    for i in range(2000):
        time.sleep(3.5)
        wrapper.Measure()
        wrapper.Apply()