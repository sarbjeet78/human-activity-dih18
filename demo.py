import sys

import model as cnn_model
import model_yolo
from utility.cv_utils import *
from utils import *
from imutils.object_detection import non_max_suppression
from math import isclose


def draw_boxes(image, boxes):
    image_h, image_w, _ = image.shape

    for box in boxes:
        xmin = int(box.xmin * image_w)
        ymin = int(box.ymin * image_h)
        xmax = int(box.xmax * image_w)
        ymax = int(box.ymax * image_h)

        category = model_yolo.categories[box.get_label()]
        text = category + ' ' + "%.2f%%" % (box.get_score() * 100)
        cv2.putText(image,
                    text,
                    (xmin - 2, ymin - 24),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1e-3 * image_h,
                    (255, 255, 255), 2)
        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (200, 200, 200), 3)
        if category == 'person':
            roi = image[ymin:ymax, xmin:xmax, :]
            roi = im2gray(roi)
            roi = cv2.resize(roi, cnn_model.SIZE)
            roi = roi.reshape(1, *roi.shape, 1)

            prediction = phase_two.predict(roi)[0]
            index = np.argmax(prediction)
            activity = cnn_model.categories[index]
            text = activity
            cv2.putText(image,
                        text,
                        (xmin - 2, ymin - 7),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1e-3 * image_h,
                        (255, 255, 255), 2)
    return image


if __name__ == '__main__':
    SHOW = False
    YOLO =True
    if len(sys.argv) == 2:
        video_path = sys.argv[1]
    else:
        video_path = 0
    print('detecting ',video_path)
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    phase_one = model_yolo.load_model()
    phase_two = cnn_model.load_model()
    video = Video(video_path)
    dummy_array = np.zeros((1, 1, 1, 1, model_yolo.TRUE_BOX_BUFFER, 4))
    fourcc = cv2.VideoWriter_fourcc(*"MPEG")
    clip = cv2.VideoWriter('demo.avi', fourcc, 30, (1024, 1024))
    y,x=video.read().shape[:2]
    t=min(x,y)
    for image in video:
        try:
            image = image[:t,:t,:]            
            image = cv2.resize(image, (1024, 1024))
            inp = cv2.resize(image, (416, 416))
            if YOLO:
                
                input_image = inp / 255.
                input_image = input_image[:, :, ::-1]
                input_image = np.expand_dims(input_image, 0)
                netout = phase_one.predict([input_image, dummy_array])
                boxes = decode_netout(netout[0],
                                      obj_threshold=model_yolo.OBJ_THRESHOLD,
                                      nms_threshold=model_yolo.NMS_THRESHOLD,
                                      anchors=model_yolo.ANCHORS,
                                      nb_class=model_yolo.CLASS)
            else:
                hogout = hog.detectMultiScale(image, winStride=(4,4),padding=(8, 8), scale=1.05)
                boxes = decode_hogout(hogout,image)
            rects = np.array([[x*image.shape[0], y*image.shape[1], x2*image.shape[0], y2*image.shape[1]] for (x, y, x2, y2) in boxes])
            print(rects)
            pick = non_max_suppression(rects, probs=None, overlapThresh=.065)
            pickb=[]
            for box in boxes:
                for [x, y, x2, y2] in pick:
                    if isclose(x,box.xmin*image.shape[0],abs_tol=1)and isclose(y,box.ymin*image.shape[1],abs_tol=1) and isclose(x2,box.xmax*image.shape[0],abs_tol=1) and isclose(y2,box.ymax*image.shape[1],abs_tol=1):
                        pickb.append(box)
            print(len(pickb),len(boxes))
            image = draw_boxes(image, pickb)
            clip.write(image.astype('uint8'))
            if SHOW:
                cv2.imshow('window', image)
                cv2.waitKey(1)
            #print (len(boxes))
        except Exception as s:
            print(s)
            if s == KeyboardInterrupt:
                break
    clip.release()
    if SHOW:
        destroy_window('window')
