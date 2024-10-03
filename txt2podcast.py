import os
import azure.cognitiveservices.speech as speechsdk
import anthropic
import re
import yaml
from typing import List, Dict
import click
from dotenv import load_dotenv
import requests
from urllib.parse import urlparse
from pydub import AudioSegment
import logging

load_dotenv(".env.local")

def fetch_content_from_url(url: str) -> str:
    jina_url = "https://r.jina.ai/" + url
    response = requests.get(jina_url)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to fetch content from URL. Status code: {response.status_code}")

def read_input(input_source: str) -> str:
    parsed_url = urlparse(input_source)
    if parsed_url.scheme and parsed_url.netloc:
        # It's a URL
        return fetch_content_from_url(input_source)
    else:
        # It's a file path
        with open(input_source, "r", encoding="utf-8") as file:
            return file.read()

def generate_script_content(text: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    prompt = f"""
    Analyze the following text and convert it into an engaging, emotional, and insightful podcast script in Chinese (Mandarin):

    {text}

    Create the script following these key guidelines:
    1. Language: The entire script must be in Chinese (Mandarin), except for the names Sophia and Justin.
    2. Content: Maintain the depth and insights from the original text, but present them in a more accessible and emotional way.
    3. Tone: Keep it very conversational, natural, and emotionally expressive, as if two close friends are discussing the topic.
    4. Simplify: Break down complex ideas into digestible bits. Use analogies and relatable examples when appropriate.
    5. Interaction: Include frequent moments where the host and expert react emotionally to each other, ask questions, or offer different perspectives.
    6. Engagement: Regularly address the listeners directly or pose thought-provoking questions to keep them emotionally involved.
    7. Structure: Start with an exciting topic overview, maintain a dynamic flow of ideas, and end with emotionally impactful key takeaways.
    8. Language: Use clear, everyday Chinese while retaining important technical terms. Explain jargon when necessary, using emotional analogies if possible.
    9. Humor and Emotion: Include frequent light moments, witty remarks, and emotional reactions. Don't shy away from expressing excitement, surprise, or even mild frustration when appropriate.
    10. Examples: Incorporate vivid, emotionally resonant real-world examples and relevant anecdotes to illustrate points.
    11. Neutrality: While maintaining objectivity on controversial issues, don't be afraid to express emotional reactions to different viewpoints.
    12. Names: Always use the English names "Sophia" and "Justin" for the host and expert, respectively. Do not translate or transliterate these names.
    13. Natural dialogue: Avoid unnecessary addressing of each other by name. Sophia may occasionally use Justin's name, but Justin should never call Sophia by name.
    14. Justin's responses: Justin should respond directly and emotionally to questions or comments without using Sophia's name. He should use context and natural conversation flow instead.
    15. Length limit: The script must contain no more than 24 total exchanges between Sophia and Justin combined. This is to ensure the final SSML doesn't exceed technical limitations.

    Roles:
    SOPHIA: The host. Curious, engaging, and emotionally expressive. Guides the conversation with enthusiasm, asks insightful questions, and often offers a layperson's perspective with genuine emotional reactions. May occasionally use Justin's name.
    JUSTIN: The expert guest. Knowledgeable but approachable and emotionally open. Explains concepts clearly with passion, provides analysis and context with excitement, and isn't afraid to admit when something is complex or surprising. Never calls Sophia by name.

    Format the script as follows:
    SOPHIA: [Sophia's lines in Chinese, including emotional cues like laughter or gasps in parentheses]
    JUSTIN: [Justin's lines in Chinese, including emotional cues like excitement or thoughtful pauses in parentheses]

    Aim for a balance where listeners feel they're gaining valuable insights while enjoying an engaging, emotionally rich, and natural conversation. Make it informative, listenable, and emotionally resonant!

    Do not include any audio cues or SSML tags in this script.
    Remember to always use "Sophia" and "Justin" as the names, keeping them in English even though the rest of the script is in Chinese.
    Ensure that Justin never addresses Sophia by name in his responses.
    Strictly adhere to the 45 exchange limit to avoid technical issues in later processing.
    """

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=8192,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    script = response.content[0].text

    # Debug: Save the generated script to a file
    with open("debug_script.txt", "w", encoding="utf-8") as debug_file:
        debug_file.write(script)

    return script

def design_sentence_delivery(script: str) -> List[Dict[str, str]]:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    prompt = f"""
    Analyze the following podcast script and design how each sentence should be delivered:

    {script}

    For each sentence, provide:
    1. speaker (SOPHIA or JUSTIN)
    2. sentence (the sentence itself, without quotes)
    3. style (one of: cheerful, empathetic, friendly, narration-professional)
    4. styledegree (a number between 0.01 and 2.0, default is 1.0)
    5. rate (a percentage between -10% and +20%)
    6. pitch (a percentage between -5% and +5%)

    Style guidelines:
    - DO NOT add addtional controls to most sentences. If you use default values, just don't include the field.
    - Keep a fast rate for the entire podcast. Add additional 10% to the rate for each sentence.
    - Maintain consistent style for consecutive sentences from the same speaker, unless there's a clear emotional shift.
    - Use styledegree sparingly, with most values between 0.8 and 1.5. Only use higher values (up to 2.0) for exceptional emphasis.
    - Adjust pitch and rate minimally. Use these adjustments sparingly and only when necessary for emphasis or to convey specific emotions.
    - Use speaking styles wisely to make the conversation engaging, ensuring changes are natural and appropriate to the content.
    - Include laughter text like "haha" or "hehe" where it's clearly appropriate to the conversation.

    Return the result as a YAML array of objects, each containing the above information.
    Your response must be a valid YAML array and nothing else. Do not include any explanations, code block markers, or text outside the YAML array.
    Do not use quotes for the sentence field unless absolutely necessary (e.g., if the sentence contains a colon).
    """

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=8192,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Debug: Save the raw response to a file
    with open("debug_delivery_response.txt", "w", encoding="utf-8") as debug_file:
        debug_file.write(response.content[0].text)

    try:
        # Remove any potential code block markers
        yaml_content = re.sub(r'^```yaml\s*|\s*```$', '', response.content[0].text, flags=re.MULTILINE).strip()
        
        # Try to parse the YAML response
        delivery_design = yaml.safe_load(yaml_content)
        
        # Validate that it's a list of dictionaries
        if not isinstance(delivery_design, list) or not all(isinstance(item, dict) for item in delivery_design):
            raise ValueError("Response is not a list of dictionaries")
        
        # Debug: Save the parsed delivery design to a file
        with open("debug_delivery_design.yaml", "w", encoding="utf-8") as debug_file:
            yaml.dump(delivery_design, debug_file, allow_unicode=True, default_flow_style=False)

        return delivery_design
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        print("Raw response:", response.content[0].text)
        raise
    except ValueError as e:
        print(f"Invalid response format: {e}")
        print("Raw response:", response.content[0].text)
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        print("Raw response:", response.content[0].text)
        raise

def generate_ssml_content(delivery_design: List[Dict[str, str]]) -> str:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    prompt = f"""
    Generate SSML (Speech Synthesis Markup Language) content based on the following delivery design:

    {yaml.dump(delivery_design, allow_unicode=True)}

    Guidelines for SSML generation:
    1. Use the <speak> tag as the root element with appropriate xmlns attributes.
    2. Use <voice> tags to switch between speakers (SOPHIA and JUSTIN).
    3. Use <mstts:express-as> tags for different speaking styles.
    4. Use <prosody> tags for rate and pitch adjustments.
    5. Use <break> tags where specified in the delivery design.
    6. Ensure proper nesting of all tags.
    7. Use "zh-CN-XiaoxiaoMultilingualNeural" voice for SOPHIA and "zh-CN-YunyiMultilingualNeural" for JUSTIN.
    8. The entire SSML should be in Chinese (Mandarin), except for the names Sophia and Justin.

    Additional natural conversation style guidelines:
    9. Implement varied speech rates using <prosody rate> tags:
       - Increase rate for excited or urgent statements (e.g., "+10.00%")
       - Slightly increase for casual remarks (e.g., "+5.00%")
    10. Use dynamic pitch adjustments with <prosody pitch> and <prosody contour> tags:
       - Implement slight pitch drops at the end of statements or questions
       - Vary pitch to emphasize certain words or express emotions
    11. Create seamless transitions using <mstts:ttsbreak strength="none" /> between phrases that should flow together
    12. Insert natural pauses with <mstts:ttsbreak /> tags to mimic speech rhythms and thinking pauses
    13. Use <phoneme> tags for words requiring specific pronunciation or emphasis
    14. Incorporate subtle emotional cues through pitch and rate variations
    15. Include natural interjections like "嗯", "啊", "哦" with appropriate intonation, but use sparingly
    16. Implement slight overlaps or quick responses where appropriate to mimic natural conversation flow

    Return only the generated SSML content, without any explanations or additional text.
    """

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=8192,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    ssml = response.content[0].text.strip()

    # Debug: Save the generated SSML to a file
    with open("debug_ssml.xml", "w", encoding="utf-8") as debug_file:
        debug_file.write(ssml)

    return ssml

def ssml_to_speech(ssml, output_file):
    speech_config = speechsdk.SpeechConfig(
        subscription=os.environ.get("AZURE_SPEECH_KEY"),
        region=os.environ.get("AZURE_SPEECH_REGION"),
    )

    audio_config = speechsdk.audio.AudioConfig(filename=output_file)
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=audio_config
    )

    speech_synthesis_result = speech_synthesizer.speak_ssml_async(ssml).get()
    if speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"Error details: {cancellation_details.error_details}")
    

def is_url(string):
    parsed = urlparse(string)
    return bool(parsed.scheme and parsed.netloc)

def add_background_music(speech_file: str, music_file: str, output_file: str):
    # Load the speech and music files
    speech = AudioSegment.from_wav(speech_file)
    speech = AudioSegment.silent(duration=2000) + speech + AudioSegment.silent(duration=2000)
    music = AudioSegment.from_mp3(music_file)

    # Prepare the intro
    intro_duration = 10000  # 10 seconds
    crossfade_duration = 5000  # 5 seconds
    outro_duration = 10000  # 10 seconds

    intro = music[:intro_duration]
    outro = music[len(music)-outro_duration:].fade_out(2000)

    # Prepare the background music
    final_audio = intro.append(speech, crossfade=crossfade_duration).append(outro, crossfade=crossfade_duration)

    # Export the final audio to a new file
    final_audio.export(output_file, format="mp3")
    return output_file

def generate_script_internal(input_source: str, output_file: str, debug: bool = False) -> None:
    text = read_input(input_source)
    script = generate_script_content(text)
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(script)
    if debug:
        with open("debug_script.txt", "w", encoding="utf-8") as debug_file:
            debug_file.write(script)
    print(f"Script generated and saved to {output_file}")

def design_delivery_internal(input_file: str, output_file: str, debug: bool = False) -> None:
    with open(input_file, "r", encoding="utf-8") as file:
        script = file.read()
    delivery_design = design_sentence_delivery(script)
    with open(output_file, "w", encoding="utf-8") as file:
        yaml.dump(delivery_design, file, allow_unicode=True, default_flow_style=False)
    if debug:
        with open("debug_delivery_design.yaml", "w", encoding="utf-8") as debug_file:
            yaml.dump(delivery_design, debug_file, allow_unicode=True, default_flow_style=False)
    print(f"Delivery design saved to {output_file}")

def generate_ssml_internal(input_file: str, output_file: str, debug: bool = False) -> None:
    with open(input_file, "r", encoding="utf-8") as file:
        delivery_design = yaml.safe_load(file)
    ssml = generate_ssml_content(delivery_design)
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(ssml)
    if debug:
        with open("debug_ssml.xml", "w", encoding="utf-8") as debug_file:
            debug_file.write(ssml)
    print(f"SSML generated and saved to {output_file}")

def synthesize_speech_internal(input_file: str, output_file: str) -> None:
    with open(input_file, "r", encoding="utf-8") as file:
        ssml = file.read()
    ssml_to_speech(ssml, output_file)
    print(f"Speech synthesized and saved to {output_file}")

@click.group()
def cli():
    pass

@cli.command()
@click.argument('input_source', type=click.STRING)
@click.argument('output_file', type=click.Path())
@click.option('--debug', is_flag=True, help='Enable debug mode to save intermediate files')
def generate_script(input_source, output_file, debug):
    """Generate a script from the input text."""
    generate_script_internal(input_source, output_file, debug)

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.option('--debug', is_flag=True, help='Enable debug mode to save intermediate files')
def design_delivery(input_file, output_file, debug):
    """Design sentence delivery for the script."""
    design_delivery_internal(input_file, output_file, debug)

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.option('--debug', is_flag=True, help='Enable debug mode to save intermediate files')
def generate_ssml(input_file, output_file, debug):
    """Generate SSML from the delivery design."""
    generate_ssml_internal(input_file, output_file, debug)

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
def synthesize_speech(input_file, output_file):
    """Synthesize speech from SSML."""
    synthesize_speech_internal(input_file, output_file)

@cli.command()
@click.argument('input_source', type=click.STRING)
@click.argument('output_file', type=click.Path())
@click.option('--debug', is_flag=True, help='Enable debug mode to save intermediate files')
@click.option('--music', type=click.Path(exists=True), default='background.mp3', help='Path to background music file')
def generate(input_source, output_file, debug, music):
    """Generate a podcast from text and add background music (all steps)."""
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

    # Generate script
    script_file = "temp_script.txt"
    generate_script_internal(input_source, script_file, debug)
    logging.info(f"Script generated: {script_file}")

    # Design delivery
    delivery_file = "temp_delivery.yaml"
    design_delivery_internal(script_file, delivery_file, debug)
    logging.info(f"Delivery design created: {delivery_file}")

    # Generate SSML
    ssml_file = "temp_ssml.xml"
    generate_ssml_internal(delivery_file, ssml_file, debug)
    logging.info(f"SSML generated: {ssml_file}")

    # Synthesize speech
    speech_file = "temp_speech.wav"
    synthesize_speech_internal(ssml_file, speech_file)
    logging.info(f"Speech synthesized: {speech_file}")

    # Add background music
    final_output = add_background_music(speech_file, music, output_file)
    logging.info(f"Background music added. Final output: {final_output}")

    # Clean up temporary files
    for temp_file in [script_file, delivery_file, ssml_file, speech_file]:
        os.remove(temp_file)
        logging.debug(f"Temporary file removed: {temp_file}")

    print(f"Full podcast generation complete. Final output saved to {final_output}")

if __name__ == "__main__":
    cli()