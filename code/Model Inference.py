import base64
import re
import torch
import numpy as np
import os
import time  # Importing the time module to measure execution time

from io import BytesIO
from PIL import Image
from docx import Document
from qwen_vl_utils import process_vision_info
from tqdm import tqdm
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor


def encode_image(image_path):
    """
    Encode image as base64.
    Replace 'image_path' with your actual image file path.
    """
    with Image.open(image_path) as img:
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')


def encode_video(video_path):
    """
    Encode video as base64.
    Replace 'video_path' with your actual video file path.
    """
    with open(video_path, "rb") as video_file:
        return base64.b64encode(video_file.read()).decode("utf-8")


def docx2str(path):
    """
    Read a .docx file and return its contents as text.
    Replace 'path' with your actual .docx file path.
    """
    doc = Document(path)
    paras = [par.text for par in doc.paragraphs]
    text = '\n'.join(paras)
    return text


def txt2str(path):
    """
    Read a .txt file and return its contents as text.
    Replace 'path' with your actual .txt file path.
    """
    with open(path, "r", encoding='utf-8') as f:
        return f.read()


def load_model(model_id):
    """
    Load the model and processor for inference.
    Replace 'model_id' with your model directory or Hugging Face model path.
    """
    model_name = os.path.basename(model_id)
    print(model_name)

    # Load the model with specific data type and device mapping
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    # Load the processor
    processor = AutoProcessor.from_pretrained(model_id)

    return model, processor


def generate_chat_completion_qwen(model, processor, context, temperature=0.1):
    """
    Generate a chat completion using the provided model and context.
    """
    text = processor.apply_chat_template(
        context, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(context)
    inputs = processor(text=[text], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt")
    inputs = inputs.to("cuda")

    generated_ids = model.generate(
        **inputs,
        temperature=temperature,
        max_new_tokens=132000
    )

    generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
    output_text = processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True,
                                         clean_up_tokenization_spaces=False)

    del image_inputs, video_inputs, inputs, generated_ids, generated_ids_trimmed
    torch.cuda.empty_cache()

    return output_text[0]


def main(model, proc, system_prompt, user_prompt1, user_prompt2, video_path, save_path=None):
    """
    Run inference on each video segment and output results to a .txt file.
    Replace 'video_path' with your video folder and 'save_path' to store results.
    """
    print(f'Processing {video_path}')

    if save_path == None:
        save_path = f'results/{os.path.split(video_path)[1]}.txt'
    if not os.path.exists(os.path.dirname(save_path)):
        os.makedirs(os.path.dirname(save_path))

    if system_prompt != None:
        system_message = {"role": "system", "content": [{"type": "text", "text": system_prompt}]}
        print(system_prompt)

    video_clips = os.listdir(video_path)
    video_clips.sort()

    # Initialize a variable to track the total time for the video inference
    video_start_time = time.time()

    with open(save_path, 'w', encoding='utf-8') as f:
        if system_prompt != None: f.write(system_prompt)
        with tqdm(total=len(video_clips), desc='Processing Progress', ncols=80) as pbar:
            for seg_idx, seg_name in enumerate(video_clips):
                data_path = os.path.join(video_path, seg_name)
                
                # Start the timer for the current segment inference
                segment_start_time = time.time()

                query = {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{user_prompt1}"},
                        {"type": "video", "video": f"{data_path}", "fps": 4.0, },
                    ]}

                message = [system_message, query] if system_prompt != None else [query]

                completion = generate_chat_completion_qwen(model, proc, message)

                # Calculate the inference time for this segment
                segment_end_time = time.time()
                segment_duration = segment_end_time - segment_start_time

                print('\n***********************************************'
                      f' {seg_idx * 5} - {seg_idx * 5 + 5} seconds {seg_name} '
                      '***********************************************')
                print(f'User: {user_prompt1}\nAssistant: {completion}\n')

                # Log the inference time for the segment
                f.write('\n***********************************************'
                        f' {seg_idx * 5} - {seg_idx * 5 + 5} seconds {seg_name} '
                        '***********************************************\n')
                f.write(f'User: {user_prompt1}\nAssistant: {completion}\n')
                f.write(f"Time for this inference: {segment_duration:.2f} seconds\n")

                if user_prompt2 != None:
                    answer = {"role": "assistant", "content": [{"type": "text", "text": f"{completion}"}]}
                    new_query = {"role": "user", "content": [{"type": "text", "text": f"{user_prompt2}"}]}
                    message.extend([answer, new_query])

                    completion = generate_chat_completion_qwen(model, proc, message)
                    print(f'User: {user_prompt2}\nAssistant: {completion}\n')
                    f.write(f'User: {user_prompt2}\nAssistant: {completion}\n')

        # Calculate the total time for the video
        video_end_time = time.time()
        video_duration = video_end_time - video_start_time

        # Log the total time for the video
        f.write(f"\nTotal time for this video: {video_duration:.2f} seconds\n")
        
        pbar.update(1)


if __name__ == '__main__':
    # Replace this path with your model's directory or Hugging Face model repo
    model_id = '/path/models'
    model, proc = load_model(model_id)

    system_prompt = 'You are an expert in epilepsy.'
    user_prompt1 = "Observe the patient in the video. Are there any abnormal postures, such as sustained elevation or unusual extension of the arms or legs, that may indicate a tonic seizure? Please answer concisely in one sentence."


    # Replace 'root_folder' with your root directory containing videos
    root_folder = '/path/data'
    
    # Replace with the list of videos you want to process
    test_videos = ['video1','video2']

    for video in test_videos:
        if os.path.isdir(os.path.join(root_folder, video)):
            video_path = os.path.join(root_folder, video)
            # Modify save path as needed
            save_path = f'results_tonic/results_validation_20250814/{os.path.split(video_path)[1]}.txt'
            main(model, proc, system_prompt, user_prompt1, user_prompt2, video_path, save_path)
