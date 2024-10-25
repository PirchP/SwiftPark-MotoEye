import cv2 as open_cv

def draw_contours(frame, coordinates, label, color_text, color_box):
    open_cv.drawContours(frame, [coordinates], contourIdx=-1, color=color_box, thickness=2, lineType=open_cv.LINE_8)

    moments = open_cv.moments(coordinates)
    if moments["m00"] != 0:
        x = int(moments["m10"] / moments["m00"])
        y = int(moments["m01"] / moments["m00"])
    else:
        x, y = coordinates[0][0], coordinates[0][1]

    open_cv.putText(frame, label, (x - 30, y), open_cv.FONT_HERSHEY_SIMPLEX, 0.7, color_text, 2, open_cv.LINE_AA)
