import os
import cv2
from PIL import Image

def resize_and_save_as_jpg(src_img_path, dst_img_path, max_size=384):

    with Image.open(src_img_path) as img:
        img = img.convert('RGB')
        w, h = img.size
        if max(w, h) > max_size:
            scale = max_size / max(w, h)
            new_w, new_h = int(w * scale), int(h * scale)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        img.save(dst_img_path, 'JPEG', quality=95)

def extract_keyframes_from_video(video_path, output_dir, frames_per_second=2, batch_size=10, resize=384):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video file {video_path}.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps

    print(f"Processing video: {video_name}, FPS: {fps}, Total Frames: {total_frames}")


    frame_interval_ms = 1000 / frames_per_second  
    timestamps = [i * frame_interval_ms for i in range(int(duration * 1000 // frame_interval_ms))]

    batch_count = 1
    saved_frames = 0
    global_frame_count = 0

    video_output_dir = os.path.join(output_dir, video_name)
    os.makedirs(video_output_dir, exist_ok=True)
    current_batch_folder = os.path.join(video_output_dir, f"batch_{batch_count}")
    os.makedirs(current_batch_folder, exist_ok=True)

    for ms in timestamps:
        cap.set(cv2.CAP_PROP_POS_MSEC, ms)
        ret, frame = cap.read()
        if not ret:
            continue

        if saved_frames == batch_size:
            batch_count += 1
            current_batch_folder = os.path.join(video_output_dir, f"batch_{batch_count}")
            os.makedirs(current_batch_folder, exist_ok=True)
            saved_frames = 0

        tmp_name = os.path.join(current_batch_folder, "tmp.png")
        cv2.imwrite(tmp_name, frame)
        #0-9
        #dst_img_name = f"{saved_frames:05d}.jpg"
        #0-660
        dst_img_name = f"{global_frame_count:05d}.jpg"
        dst_img_path = os.path.join(current_batch_folder, dst_img_name)
        try:
            resize_and_save_as_jpg(tmp_name, dst_img_path, max_size=resize)
            os.remove(tmp_name)
        except Exception as e:
            print(f"Error processing {tmp_name}: {e}")
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
        saved_frames += 1
        global_frame_count += 1

    cap.release()
    print(f"Extraction complete for {video_name}: {global_frame_count} frames saved.")


def process_all_videos_in_folder(input_folder, output_folder, frames_per_second=2, batch_size=10, resize=384):

    if not os.path.exists(input_folder):
        print(f"Error: Input folder {input_folder} does not exist.")
        return
    os.makedirs(output_folder, exist_ok=True)
    for file_name in os.listdir(input_folder):
        video_path = os.path.join(input_folder, file_name)

        if os.path.isfile(video_path) and file_name.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv')):
            video_name = os.path.splitext(file_name)[0]
            video_output_dir = os.path.join(output_folder, video_name)

            if os.path.exists(video_output_dir) and len(os.listdir(video_output_dir)) > 0:
                print(f"Skipping {file_name}: already processed.")
                continue
            extract_keyframes_from_video(video_path, output_folder, frames_per_second, batch_size, resize)
        else:
            print(f"Skipping non-video file: {file_name}")


if __name__ == '__main__':
    input_videos_folder = r"/path"
    output_frames_folder = r"/path"
    frames_per_second = 2         
    batch_size = 10               
    resize = 1920                  
    process_all_videos_in_folder(input_videos_folder, output_frames_folder, frames_per_second, batch_size, resize)
