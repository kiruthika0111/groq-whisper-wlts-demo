import os
import json
import tempfile
import gradio as gr
import numpy as np
from groq import Groq
from pydub import AudioSegment
from dotenv import load_dotenv
load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

def process_audio(audio_path, language="en", prompt="", temperature=0.0):
    """
    Process an audio file using Groq's Whisper model to generate word-level timestamps.
    """
    with open(audio_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=file,
            model="whisper-large-v3-turbo",
            prompt=prompt,
            response_format="verbose_json",
            timestamp_granularities=["word", "segment"],
            language=language,
            temperature=temperature
        )
    
    try:
        result_dict = dict(transcription)
    except (TypeError, ValueError):
        try:
            result_json = json.dumps(transcription, default=str)
            result_dict = json.loads(result_json)
        except:
            if hasattr(transcription, 'text'):
                result_dict = {"text": transcription.text, "segments": []}
            else:
                result_dict = {"text": str(transcription), "segments": []}
    
    return (
        result_dict.get("text", "Transcription text not available"),
        result_dict,
        None  
    )

def save_temp_audio(audio_data, sample_rate):
    """Save audio data to a temporary file."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        if isinstance(audio_data, tuple):
            audio_data = audio_data[0]
        
        audio = AudioSegment(
            audio_data.tobytes(),
            frame_rate=sample_rate,
            sample_width=audio_data.dtype.itemsize,
            channels=1
        )
        audio.export(temp_audio.name, format="wav")
        return temp_audio.name

def process_uploaded_audio(audio, language, prompt, temperature):
    """Process audio uploaded through Gradio."""
    if audio is None:
        return "Please upload an audio file.", {"error": "No audio file provided"}, None
    
    try:
        if isinstance(audio, str):
            audio_path = audio
        else:
            audio_path = save_temp_audio(audio[0], audio[1])
        
        try:
            transcription, raw_json, _ = process_audio(
                audio_path,
                language=language,
                prompt=prompt,
                temperature=float(temperature)
            )
            
            if audio_path != audio and os.path.exists(audio_path):
                os.unlink(audio_path)
                
            return transcription, raw_json, None  
        except Exception as e:
            error_message = str(e)
            print(f"Error processing audio: {error_message}")
            return f"Error: {error_message}", {"error": error_message}, None
    except Exception as e:
        error_message = str(e)
        print(f"Error handling audio file: {error_message}")
        return f"Error handling audio file: {error_message}", {"error": error_message}, None


with gr.Blocks(title="Groq Whisper WLTS Demo") as demo:
    gr.Markdown("# Groq Whisper Word-Level Time Stamping Demo")
    gr.Markdown("""
    This demo showcases word-level time stamping (WLTS) using Groq's Whisper model.
    Upload an audio file to get a detailed transcription with timestamps for each word.
    """)

    with gr.Row():
        with gr.Column(scale=1):
            audio_input = gr.Audio(type="filepath", label="Upload Audio")

            with gr.Row():
                language_input = gr.Dropdown(
                    choices=["en", "es", "fr", "de", "it", "pt", "nl", "ja", "zh", "ru", "auto"],
                    value="en",
                    label="Language"
                )
                temperature_input = gr.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    value=0.0,
                    step=0.1,
                    label="Temperature"
                )

            prompt_input = gr.Textbox(
                placeholder="Optional context or prompt to guide transcription",
                label="Prompt"
            )

            process_btn = gr.Button("Transcribe with Word-Level Timestamps")

        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.TabItem("Normal Transcription without timestamps"):
                    transcription_output = gr.Textbox(label="Transcription", lines=10)

                with gr.TabItem("Raw JSON with Word-Level Timestamps"):
                    json_output = gr.JSON(label="Raw JSON Response with Word-Level Timestamps")

    process_btn.click(
        fn=process_uploaded_audio,
        inputs=[audio_input, language_input, prompt_input, temperature_input],
        outputs=[transcription_output, json_output]
    )

    gr.Markdown("""
    ## About This Demo
    
    This demo showcases word-level time stamping (WLTS) using Groq's implementation of the Whisper model.
    Key features:
    
    - **Word-Level Precision**: Get timestamps for each individual word in the transcription.
    - **Raw Data Access**: Export the full JSON data with all timestamp information.
    
    ### How It Works
    
    1. Upload an audio file (WAV, MP3, etc.)
    2. Select the language and adjust settings if needed
    3. Click "Transcribe with Word-Level Timestamps"
    4. View the transcription and raw data
    
    ### Applications
    
    - Subtitle generation with precise word timing
    - Audio search and indexing
    - Accessibility tools for hearing-impaired users
    - Educational tools for language learning
    - Media analysis and research
    
    Created for the Groq WLTS Challenge. [View source code on GitHub](https://github.com/kiruthika0111/groq-whisper-wlts-demo)
    """)

    # Adding the image in the bottom right
    gr.Image("PBG mark1 color.png", elem_id="bottom-right-image", show_label=False)

# Custom CSS to position the image
demo.css = """
#bottom-right-image {
    position: fixed;
    bottom: 10px;
    right: 10px;
    width: 100px;
    height: auto;
    z-index: 1000;
}
"""

if __name__ == "__main__":
    demo.launch()
