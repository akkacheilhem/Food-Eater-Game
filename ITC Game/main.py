import cv2
import mediapipe as mp


BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = FaceLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path="face_landmarker.task"
    ),
    running_mode=VisionRunningMode.VIDEO,
    num_faces=1
)

landmarker = FaceLandmarker.create_from_options(options)

camera = cv2.VideoCapture(0)

frame_timestamp = 0

while True:

    success, frame = camera.read()

    if not success:
        print("Impossible d'accéder à la caméra")
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    
    results = landmarker.detect_for_video(
        mp_image,
        frame_timestamp
    )

    frame_timestamp += 33


    if results.face_landmarks:

        face_landmarks = results.face_landmarks[0]

        h, w, _ = frame.shape




        for i, landmark in enumerate(face_landmarks):

            x = int(landmark.x * w)
            y = int(landmark.y * h)

            cv2.circle(
                frame,
                (x, y),
                1,
                (0, 255, 0),
                -1
            )



        mouth_landmarks = [
            61, 291,
            0, 17,
            13, 14,
            78, 308,
            185, 40,
            39, 37,
            267, 269,
            405, 314
        ]

        for index in mouth_landmarks:

            landmark = face_landmarks[index]

            x = int(landmark.x * w)
            y = int(landmark.y * h)

            cv2.circle(
                frame,
                (x, y),
                4,
                (0, 0, 255),
                -1
            )

            upper_lip = face_landmarks[13]
            lower_lip = face_landmarks[14]

            upper_y = int(upper_lip.y * h)
            lower_y = int(lower_lip.y * h)

            mouth_opening = lower_y - upper_y
            # Position de la bouche
            mouth_x = int(face_landmarks[13].x * w)
            mouth_y = int(face_landmarks[13].y * h)

            cv2.circle(
                  frame,
                  (mouth_x, mouth_y),
                   10,
                 (255, 0, 0),
                  -1
                )

            threshold = 15

            if mouth_opening > threshold:
              text = "BOUCHE OUVERTE"
            else:
             text = "BOUCHE FERMEE"

            cv2.putText(
                frame,
                text,
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Ouverture : {mouth_opening}",
                (30, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
               (255, 255, 255),
               2
            )



    cv2.imshow(
        "Food Eater - Mouth Detection",
        frame
    )


    # Q pour quitter
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


camera.release()
cv2.destroyAllWindows()
landmarker.close()