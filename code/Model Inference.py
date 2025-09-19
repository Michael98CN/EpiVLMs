# =========================================
# Model Inference Pseudocode
# =========================================

import os, time

# ---------- Symptoms ----------
SYMPTOMS = ["tonic", "clonic", "versive", "manual_automatisms", "staring"]

# ---------- Model registry (per symptom) ----------
MODEL_ID = {
    "tonic":  "/path/to/ft_tonic",
    "clonic": "/path/to/ft_clonic",
    "versive": "/path/to/ft_versive",
    "manual_automatisms": "/path/to/ft_automatisms",
    "staring": "/path/to/ft_staring",
}

# ---------- Runtime options ----------
FPS_CLIP = 4.0
SEG_SECONDS = 5
TEMPERATURE = 0.1
MAX_NEW_TOKENS = 1024

# ---------- Abstract prompts (placeholders only) ----------
SYSTEM_PROMPT = "<SYSTEM_PROMPT>"

# e.g., dict-like access: OBSERVE_PROMPT['clonic'] -> string
OBSERVE_PROMPT = {sym: f"<OBSERVE_PROMPT[{sym}]>" for sym in SYMPTOMS}
DECIDE_PROMPT  = {sym: f"<DECIDE_PROMPT[{sym}]>"  for sym in SYMPTOMS}

# ========== Framework hooks (to be implemented in real code) ==========
def load_model_and_processor(model_id):
    """Return (model, processor) for a given model_id."""
    return "<model>", "<processor>"

def build_messages(system_prompt, user_prompt_text, media_path, fps=None):
    """Return chat messages list with optional system role and media attachment."""
    msgs = []
    if system_prompt:
        msgs.append({"role":"system","content":[{"type":"text","text":system_prompt}]})
    content = [{"type":"text","text":user_prompt_text}]
    if media_path:
        # video or image keyed by caller
        media_type = "image" if media_path.endswith((".png",".jpg",".jpeg",".bmp",".webp")) else "video"
        item = {"type": media_type, media_type: media_path}
        if media_type == "video" and fps is not None:
            item["fps"] = fps
        content.append(item)
    msgs.append({"role":"user","content":content})
    return msgs

def append_turn(messages, role, text):
    """Append a plain text turn to existing messages."""
    messages.append({"role":role, "content":[{"type":"text","text":text}]})

def generate_once(model, processor, messages, temperature, max_new_tokens):
    """One forward generation; returns decoded assistant text."""
    return "<assistant_text>"

def list_segments(video_dir):
    """Return sorted list of segment files (clips for motor; frames for staring)."""
    files = sorted(os.listdir(video_dir))
    return [os.path.join(video_dir, f) for f in files]

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

# ========== Inference for one symptom & one video ==========
def infer_video_for_symptom(symptom, model, processor, video_dir, out_txt):
    """
    - staring: expect static frames folder; others: short clips folder.
    - Two-turn dialogue per segment: OBSERVE -> DECIDE (carry previous answer into context).
    - Record per-segment and total timing.
    """
    ensure_dir(os.path.dirname(out_txt))
    segments = list_segments(video_dir)
    t0_video = time.time()

    with open(out_txt, "w", encoding="utf-8") as fout:
        if SYSTEM_PROMPT:
            fout.write(SYSTEM_PROMPT + "\n")

        for idx, seg_path in enumerate(segments):
            seg_t0 = time.time()

            # 1) OBSERVE
            fps = None if symptom == "staring" else FPS_CLIP
            msgs = build_messages(SYSTEM_PROMPT, OBSERVE_PROMPT[symptom], seg_path, fps=fps)
            ans1 = generate_once(model, processor, msgs, TEMPERATURE, MAX_NEW_TOKENS)

            header = f"*** {idx*SEG_SECONDS}–{(idx+1)*SEG_SECONDS}s {os.path.basename(seg_path)} ***\n"
            fout.write(header)
            fout.write(f"User1: {OBSERVE_PROMPT[symptom]}\nAssistant1: {ans1}\n")

            # 2) DECIDE
            append_turn(msgs, "assistant", ans1)  # carry previous answer as context
            append_turn(msgs, "user", DECIDE_PROMPT[symptom])
            ans2 = generate_once(model, processor, msgs, TEMPERATURE, MAX_NEW_TOKENS)

            seg_dt = time.time() - seg_t0
            fout.write(f"User2: {DECIDE_PROMPT[symptom]}\nAssistant2: {ans2}\n")
            fout.write(f"Time for this inference: {seg_dt:.2f} seconds\n")

    total_dt = time.time() - t0_video
    with open(out_txt, "a", encoding="utf-8") as fout:
        fout.write(f"\nTotal time for this video: {total_dt:.2f} seconds\n")

# ========== Driver ==========
def main():
    # Choose symptom
    SYM = "clonic"  # or any in SYMPTOMS

    # Load per-symptom model
    model_id = MODEL_ID[SYM]
    model, processor = load_model_and_processor(model_id)

    # Dataset roots (folder per video, containing segments/frames)
    ROOT = "/path/to/segmented_data_root"
    TEST_VIDEOS = ["VideoID_001", "VideoID_002"]

    for vid in TEST_VIDEOS:
        video_dir = os.path.join(ROOT, vid)
        if os.path.isdir(video_dir):
            out_txt = f"results/{SYM}/{vid}.txt"
            infer_video_for_symptom(SYM, model, processor, video_dir, out_txt)

if __name__ == "__main__":
    main()
