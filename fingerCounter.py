import cv2
import time
import handDetectModule as hd

wCam, hCam = 800, 800

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

pTime = 0
detector = hd.handDetector(detectionCon=0.75)
tipIds = [8, 12]
totalFingers = 0
while True:
    success, img = cap.read()
    
    img = detector.findHands(img, draw=False)
    lmList, _ = detector.findPosition(img, draw=False)

    if len(lmList) != 0:
        fingers = []

        for id in [0,1]:
            if lmList[tipIds[id]][2] < lmList[tipIds[id]-2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        totalFingers = fingers.count(1)
        print(lmList[8])
        circleX=[0,0]
        circleY=[0,0]

        if lmList[8][1]<200:
            circleX = 200
        elif lmList[8][1]>400:
            circleX = 400
        else:
            circleX = lmList[8][1]

        if lmList[8][2]<25:
            circleY = 25
        elif lmList[8][2]>305:
            circleY = 305
        else:
            circleY = lmList[8][2]

        cv2.circle(img, (circleX,circleY), 10, (255,0,0), cv2.FILLED)
        cv2.circle(img, (lmList[12][1],lmList[12][2]), 10, (255,0,0), cv2.FILLED)

    cTime = time.time()
    fps = 1/(cTime - pTime)
    
    cv2.putText(img, f'fps: {int(fps)}', (50, 120), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 3)
    pTime = cTime

    cv2.rectangle(img, (200, 25), (400, 305), (0,0,0), 10)

    cv2.imshow("IMG", img)
    cv2.waitKey(1)