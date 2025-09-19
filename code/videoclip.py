import os
from moviepy.editor import VideoFileClip

def split_video_by_seconds(input_path, output_folder, segment_duration=10, step_size=5):

    os.makedirs(output_folder, exist_ok=True)
    video = VideoFileClip(input_path)
    total_duration = video.duration

    i = 0
    start_time = 0
    while start_time < total_duration:
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
        segment.close()
        i += 1
        start_time += step_size
    video.close()

def batch_split_videos(input_folder, output_folder, segment_duration=10, step_size=5):

    for file_name in os.listdir(input_folder):
        if file_name.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv')):
            video_path = os.path.join(input_folder, file_name)
            output_dir = os.path.join(output_folder, os.path.splitext(file_name)[0])
            split_video_by_seconds(video_path, output_dir, segment_duration, step_size)

if __name__ == '__main__':

    input_folder = r"/path"  
    output_dir = r"/patht"    
    segment_duration = 10  
    step_size = 5          

    batch_split_videos(input_folder, output_dir, segment_duration, step_size)
