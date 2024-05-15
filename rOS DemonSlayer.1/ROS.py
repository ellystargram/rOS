import numpy as np

import RKernel

rk = RKernel.RKernel()
fps_history = []

# resize window 360 360
rk.cv.namedWindow("ROS", rk.cv.WINDOW_NORMAL)
rk.cv.resizeWindow("ROS", 320, 320)

boot_start_time = rk.time.time()
while rk.time.time() - boot_start_time < 5:
    rk.cv.imshow("ROS", rk.splash_screen)
    rk.cv.waitKey(1)

if rk.key_engine.get_key("CameraDevice").get("value") == "macbook pro":
    camera = rk.cv.VideoCapture(0)
elif rk.key_engine.get_key("CameraDevice").get("value") == "iphone":
    camera = rk.cv.VideoCapture(1)
else:
    print("warning! Invalid camera device. Using default device.")
    camera = rk.cv.VideoCapture(0)

last_update_time = rk.time.time()
while True:
    capture_success, frame = camera.read()
    if not capture_success:
        break

    # make new_frame but don't flect it
    target_width = 320
    target_height = 320
    aspect_ratio = float(target_height) / frame.shape[0]
    dsize = (int(frame.shape[1] * aspect_ratio), target_height)
    new_frame = rk.cv.resize(frame, dsize)

    # cut the new_frame width to 320 center
    new_frame = new_frame[:, new_frame.shape[1] // 2 - target_width // 2: new_frame.shape[1] // 2 + target_width // 2]

    if rk.key_engine.get_key("ROSModelActive").get("value"):
        rk.process_frame(new_frame)

        boxes_idx, classes_idx, scores_idx = 0, 1, 2
        boxes = rk.model.get_tensor(rk.model_output_details[boxes_idx]['index'])[0]
        classes = rk.model.get_tensor(rk.model_output_details[classes_idx]['index'])[0]
        scores = rk.model.get_tensor(rk.model_output_details[scores_idx]['index'])[0]

        for i in range(len(scores)):
            class_name = rk.label_engine.get_label(int(classes[i] + 1)).get("value")
            class_color = rk.color_engine.get_color(class_name)
            if scores[i] > 0.5:
                box = boxes[i] * [320, 320, 320, 320]
                if rk.key_engine.get_key("ROSMindDisplayWay").get("value") == "filled box":
                    inverted_color = (255 - class_color[0], 255 - class_color[1], 255 - class_color[2])
                    #outer line
                    rk.cv.rectangle(new_frame, (int(box[1]), int(box[0]), int(box[3]), int(box[2])), inverted_color, 2)
                    #inner box
                    rk.cv.rectangle(new_frame, (int(box[1]), int(box[0])), (int(box[3]), int(box[2])), class_color, -1)
                    # put text center of the box
                    text_size = rk.cv.getTextSize(class_name, rk.cv
                                                    .FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                    text_x = int((box[1] + box[3]) / 2 - text_size[0] / 2)
                    text_y = int((box[0] + box[2]) / 2 + text_size[1] / 2)
                    rk.cv.putText(new_frame, class_name, (text_x, text_y), rk.cv.FONT_HERSHEY_SIMPLEX, 0.5,
                                  inverted_color, 2)
                elif rk.key_engine.get_key("ROSMindDisplayWay").get("value") == "outlined box":
                    rk.cv.rectangle(new_frame, (int(box[1]), int(box[0])), (int(box[3]), int(box[2])), class_color, 2)
                    rk.cv.putText(new_frame, class_name, (int(box[1]), int(box[0])), rk.cv.FONT_HERSHEY_SIMPLEX, 0.5,
                                  class_color, 2)

    if rk.key_engine.get_key("ROSDisplayFPSEnable").get("value"):
        update_time = rk.time.time()
        fps = 1 / (update_time - last_update_time)
        fps_history.append(fps)
        if len(fps_history) > 10:
            fps_history.pop(0)
        last_update_time = update_time
        avg_fps = np.mean(fps_history)
        rk.cv.putText(new_frame, f"FPS: {avg_fps:.2f}", (10, 20), rk.cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    rk.cv.imshow("ROS", new_frame)

    if rk.cv.waitKey(1) & 0xFF == 27:
        break

rk.shutdown()