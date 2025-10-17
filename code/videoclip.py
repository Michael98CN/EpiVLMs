import os
import math
import uuid
from moviepy.editor import VideoFileClip


def split_video_by_seconds(input_path, output_folder, segment_duration=5):


    os.makedirs(output_folder, exist_ok=True)


    video = VideoFileClip(input_path)
    total_duration = video.duration


    num_segments = min(math.floor(total_duration / segment_duration), 60)


    for i in range(num_segments):
        start_time = i * segment_duration
        end_time = start_time + segment_duration


        if end_time > total_duration:
            end_time = total_duration


        segment = video.subclip(start_time, end_time)


        output_path = os.path.join(output_folder, f"segment_{i + 1:03d}.avi")


        segment.write_videofile(
            output_path,
            codec='libx264',  
            audio_codec='aac',  
            logger=None  
        )

        print(f"save: {output_path}")


    video.close()

def split_video_by_seconds_multi(input_path, output_folder, segment_duration=5, file_lock=None):


    os.makedirs(output_folder, exist_ok=True)


    base_name = os.path.basename(input_path).split('.')[0]
    unique_id = f"{base_name}_{uuid.uuid4().hex[:8]}"


    temp_folder = os.path.join(output_folder, f"temp_{unique_id}")
    os.makedirs(temp_folder, exist_ok=True)

    try:

        if file_lock:
            file_lock.acquire()
        try:

            video = VideoFileClip(input_path)
            total_duration = video.duration
        except Exception as e:
            print(f'ddd{e}')
        finally:
            if file_lock:
                file_lock.release()


        num_segments = min(math.floor(total_duration / segment_duration), 60)


        for i in range(num_segments):
            start_time = i * segment_duration
            end_time = start_time + segment_duration


            if end_time > total_duration:
                end_time = total_duration


            segment = video.subclip(start_time, end_time)


            output_path = os.path.join(output_folder, f"segment_{i + 1:03d}.avi")


            if file_lock:
                file_lock.acquire()
            try:
                segment.write_videofile(
                    output_path,
                    codec='libx264',  
                    audio_codec='aac',  
                    temp_audiofile=os.path.join(temp_folder, f"temp_audio_{i}.m4a"),
                    remove_temp=True,  
                    verbose=False  
                )
            except Exception as e:
                print(f'sss{e}')
            finally:
                if file_lock:
                    file_lock.release()

            print(f"save: {output_path}")
            segment.close()  

    except Exception as e:
        print(f"segment error: {str(e)}")
        raise
    finally:
        if os.path.exists(temp_folder):
            import shutil
            try:
                shutil.rmtree(temp_folder)
            except Exception as e:
                print(f"error: {str(e)}")


        if 'video' in locals() and video:
            video.close()
def batch_split_videos(input_folder, output_folder, segment_duration=5):

    for file_name in os.listdir(input_folder):
        if file_name.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv')):
            video_path = os.path.join(input_folder, file_name)
            output_dir = os.path.join(output_folder, os.path.splitext(file_name)[0])
            split_video_by_seconds(video_path, output_dir, segment_duration)




if __name__ == '__main__':
    input_folder = r"/path"  
    output_dir = r"/path"  
    segment_duration = 5
    for file_name in os.listdir(input_folder):
        file_path = os.path.join(input_folder, file_name)
        if os.path.isfile(file_path) and file_name.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv')):
            video_output_dir = os.path.join(output_dir, os.path.splitext(file_name)[0])
            split_video_by_seconds(file_path, video_output_dir, segment_duration)

