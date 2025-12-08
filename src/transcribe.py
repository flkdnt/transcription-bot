import logging
import os

def transcribe_file(file, output):

    if(file == None):
        raise ValueError(f"Error! No file at Filepath {file}")

    # faster_whisper configuration
    ## Other Options: "int8_float16", "int8"
    compute_type = "int8"
    ## Devices: "cuda", "cpu"
    device = "cpu"
    ## Model Size
    ## Options: "base"," tiny", "small", "medium", "large-v3"
    model_size = "large-v3"

    # Run
    logger.info(f"Starting Transcription on {file}...")
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        segment_list = []
        
        segments, info = model.transcribe(file, beam_size=5, vad_filter=True)

        logger.info(f"Detected language '{info.language}' with probability %{info.language_probability}")

        for segment in segments:
            cleaned_segment = ((segment.text).strip(' \t\n\r'))
            segment_list.append(cleaned_segment)
            logger.debug(cleaned_segment)
        
        with open( output,'w' ) as f:
            for item in segment_list:
                f.write( f"{item}\n" )

    except Exception as e:
        logging.error = f"Error Transcribing Audio: {e}"
        raise RuntimeError("Error transcribing.")
        return None
    
    return segments


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Setup Audio Project
    ## Setup Root Audio Directory
    audio_dir = "downloads"
    #os.makedirs(audio_dir, exist_ok=True)
    ## Setup Project Directory
    audio_project = "Amazon_Bedrock_AgentCore_and_Claude_-_Transforming_business_with_agentic_AI_Amazon_Web_Services"
    #os.makedirs(f"{audio_dir}/{audio_project}", exist_ok=True)
    ## Vars for Audio File
    audio_file = "video.wav"
    transcript_file = "transcript.txt"
    audio_path = f"/home/dante/dev/GitHub/transcription-bot/{audio_dir}/{audio_project}/{audio_file}"
    transcript_path = f"/home/dante/dev/GitHub/transcription-bot/{audio_dir}/{audio_project}/{transcript_file}"

    # Transcribe
    transcribe_file(audio_path, transcript_path)
