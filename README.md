# txt2podcast

txt2podcast is a Python tool that converts text into an engaging podcast-style audio file. It uses AI to generate a conversational script, designs the delivery, creates SSML (Speech Synthesis Markup Language), and synthesizes speech with background music.

## Features

- Generate podcast scripts from text input
- Design sentence delivery for natural-sounding conversations
- Create SSML for advanced speech synthesis
- Synthesize speech using Azure Cognitive Services
- Add background music to the final audio output

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/txt2podcast.git
   cd txt2podcast
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env.local` file in the project root and add the following:
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key
   AZURE_SPEECH_KEY=your_azure_speech_key
   AZURE_SPEECH_REGION=your_azure_speech_region
   ```

## Usage

txt2podcast provides several commands for different stages of the podcast generation process:

1. Generate a complete podcast:
   ```
   python txt2podcast.py generate <input_source> <output_file> [--debug] [--music MUSIC_FILE]
   ```

2. Generate a script:
   ```
   python txt2podcast.py generate-script <input_source> <output_file> [--debug]
   ```

3. Design sentence delivery:
   ```
   python txt2podcast.py design-delivery <input_file> <output_file> [--debug]
   ```

4. Generate SSML:
   ```
   python txt2podcast.py generate-ssml <input_file> <output_file> [--debug]
   ```

5. Synthesize speech:
   ```
   python txt2podcast.py synthesize-speech <input_file> <output_file>
   ```

Replace `<input_source>` with a file path or URL, and `<output_file>` with the desired output file path.

## Examples

1. Generate a complete podcast from a URL:
   ```
   python txt2podcast.py generate https://example.com/article.html output_podcast.mp3 --music background.mp3
   ```

2. Generate a script from a local text file:
   ```
   python txt2podcast.py generate-script input_article.txt output_script.txt --debug
   ```

3. Design sentence delivery for an existing script:
   ```
   python txt2podcast.py design-delivery script.txt delivery_design.yaml
   ```

4. Generate SSML from a delivery design:
   ```
   python txt2podcast.py generate-ssml delivery_design.yaml output_ssml.xml --debug
   ```

5. Synthesize speech from an SSML file:
   ```
   python txt2podcast.py synthesize-speech input_ssml.xml output_speech.wav
   ```

6. Generate a podcast with debug mode and custom background music:
   ```
   python txt2podcast.py generate long_article.txt final_podcast.mp3 --debug --music custom_music.mp3
   ```

## License

MIT