import os
from google.cloud import texttospeech
import json
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def setup_google_credentials():
    """Set up Google Cloud credentials from environment."""
    credentials_json = os.getenv('GOOGLE_CLOUD_CREDENTIALS_JSON')
    if credentials_json:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json.loads(credentials_json), f)
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f.name
            return f.name
    else:
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path:
            return credentials_path
        else:
            raise ValueError("No Google Cloud credentials found in environment variables")


def create_epic_bass_narration_chunks(voice_name: str = "en-US-Neural2-D", voice_label: str = "Neural2-D"):
    """Create an epic fantasy narration with deep bass voice in chunks."""
    
    # CHUNK 1: Opening and atmosphere (under 4000 bytes)
    chunk1_ssml = """
    <speak>
      <!-- Opening: Deep, ominous tone like a prophecy -->
      <prosody rate="0.75" pitch="-6st" volume="+3dB">
        <emphasis level="strong">Winter had come to the Northern Realms.</emphasis>
        <break time="1200ms"/>
        Not the gentle frost of autumn's end,
        <break time="600ms"/>
        but the savage cold that turns men's breath to ice
        <break time="400ms"/>
        and makes the very stones crack with anguish.
      </prosody>
      
      <break time="1500ms"/>
      
      <!-- Building the atmosphere -->
      <prosody rate="0.8" pitch="-5st" volume="+2dB">
        The old men of Ironhold spoke in whispers of the last such winter,
        <break time="500ms"/>
        <prosody rate="0.7">three hundred years past,</prosody>
        <break time="600ms"/>
        when the dead walked beyond the Shadowfall,
        <break time="400ms"/>
        and the ancient kings woke from their tombs beneath the mountain.
      </prosody>
      
      <break time="1200ms"/>
      
      <!-- Introducing the protagonist with gravitas -->
      <prosody rate="0.85" pitch="-4st" volume="+1dB">
        Lord Commander Marcus Blackstone stood upon the ramparts of the Nightfort,
        <break time="500ms"/>
        his weathered face carved by forty winters of war.
        <break time="700ms"/>
        <prosody rate="0.75" pitch="-6st">
          The scar across his left eye throbbed—
          <break time="400ms"/>
          <emphasis level="strong">it always throbbed when darkness gathered.</emphasis>
        </prosody>
      </prosody>
      
      <break time="1000ms"/>
      
      <!-- The approaching threat -->
      <prosody rate="0.8" pitch="-5st" volume="+2dB">
        Below, in the frozen wastes,
        <break time="400ms"/>
        something moved.
        <break time="800ms"/>
        <prosody rate="0.7" pitch="-7st" volume="-1dB">
          Not the shambling gait of men,
          <break time="500ms"/>
          nor the proud march of southern armies.
        </prosody>
        <break time="700ms"/>
        <prosody rate="0.65" pitch="-6st" volume="+3dB">
          <emphasis level="strong">This was older.</emphasis>
          <break time="600ms"/>
          <emphasis level="strong">Hungrier.</emphasis>
          <break time="800ms"/>
        </prosody>
      </prosody>
    </speak>
    """
    
    # CHUNK 2: Dialogue and climax (under 4000 bytes)
    chunk2_ssml = """
    <speak>
      <!-- Character dialogue with different voices -->
      <prosody rate="0.9" pitch="-3st" volume="+1dB">
        "My lord,"
        <break time="300ms"/>
        his lieutenant's voice trembled despite twenty years of service.
        <break time="500ms"/>
        "The men grow restless. They speak of abandoning the wall."
      </prosody>
      
      <break time="800ms"/>
      
      <!-- Commander's response - deeper, authoritative -->
      <prosody rate="0.75" pitch="-7st" volume="+4dB">
        <emphasis level="strong">"Let them speak,"</emphasis>
        <break time="400ms"/>
        Blackstone rumbled, his voice like grinding millstones.
        <break time="600ms"/>
        "Fear loosens tongues.
        <break time="500ms"/>
        But duty...
        <break time="700ms"/>
        <prosody rate="0.6" pitch="-8st">
          duty holds the line when courage fails."
        </prosody>
      </prosody>
      
      <break time="1200ms"/>
      
      <!-- The prophecy/ancient warning -->
      <prosody rate="0.7" pitch="-6st" volume="0dB">
        The words of the Thornwood Prophecy echoed in his mind:
        <break time="800ms"/>
        <prosody rate="0.65" pitch="-7st" volume="-2dB">
          <emphasis level="moderate">"When the last star falls from the northern sky,</emphasis>
          <break time="600ms"/>
          <emphasis level="moderate">when brothers' blood stains the ancient stones,</emphasis>
          <break time="600ms"/>
          <emphasis level="strong">the forgotten kings shall rise,</emphasis>
          <break time="500ms"/>
          <emphasis level="strong">and the realm shall know true winter's bite."</emphasis>
        </prosody>
      </prosody>
      
      <break time="1500ms"/>
      
      <!-- Building to climax -->
      <prosody rate="0.8" pitch="-5st" volume="+2dB">
        A horn sounded in the darkness—
        <break time="400ms"/>
        not the bright brass of Ironhold's watchers,
        <break time="500ms"/>
        but something deeper,
        <break time="400ms"/>
        <prosody rate="0.7" pitch="-7st">
          carved from the bone of things best left buried.
        </prosody>
      </prosody>
      
      <break time="1000ms"/>
      
      <!-- The epic moment -->
      <prosody rate="0.75" pitch="-6st" volume="+4dB">
        Marcus Blackstone drew his ancestral blade,
        <break time="400ms"/>
        its black steel drinking the moonlight.
        <break time="700ms"/>
        <prosody rate="0.6" pitch="-8st" volume="+5dB">
          <emphasis level="strong">"So it begins,"</emphasis>
        </prosody>
        <break time="500ms"/>
        he whispered to the gathering storm.
        <break time="800ms"/>
        <prosody rate="0.65" pitch="-7st" volume="+3dB">
          <emphasis level="strong">"The Long Night has come again."</emphasis>
        </prosody>
      </prosody>
      
      <break time="2000ms"/>
      
      <!-- Closing narration - ominous -->
      <prosody rate="0.7" pitch="-6st" volume="-1dB">
        And in the howling darkness beyond the wall,
        <break time="600ms"/>
        ten thousand eyes of winter blue
        <break time="500ms"/>
        turned toward the last light of men.
      </prosody>
    </speak>
    """
    
    chunks = [
        ("part1_opening", chunk1_ssml),
        ("part2_climax", chunk2_ssml)
    ]
    
    try:
        setup_google_credentials()
        
        print(f"⚔️ Creating Epic Fantasy Narration with {voice_label}")
        print("=" * 60)
        
        output_files = []
        
        for chunk_name, ssml in chunks:
            print(f"\n📜 Processing {chunk_name}...")
            
            # Check byte size
            byte_size = len(ssml.encode('utf-8'))
            print(f"📊 SSML byte size: {byte_size} bytes")
            
            if byte_size > 4000:
                print("⚠️ Warning: Chunk exceeds 4000 bytes!")
                continue
            
            client = texttospeech.TextToSpeechClient()
            synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
            
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name=voice_name,
                ssml_gender=texttospeech.SsmlVoiceGender.MALE
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,  # We control this in SSML
                pitch=0.0,  # We control this in SSML
                volume_gain_db=0.0
            )
            
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            
            output_dir = "audio_output"
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"epic_drama_{voice_label}_{chunk_name}_{timestamp}"
            output_path = os.path.join(output_dir, f"{output_filename}.mp3")
            
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
            
            print(f"✅ Created: {output_path}")
            print(f"🎵 File size: {len(response.audio_content)} bytes")
            output_files.append(output_path)
        
        print(f"\n⚔️ Epic narration complete!")
        print(f"📜 Generated {len(output_files)} audio files")
        return output_files
        
    except Exception as e:
        print(f"❌ Error creating epic narration: {e}")
        return None


def test_multiple_bass_voices():
    """Test different bass voices for epic narration."""
    
    voices_to_test = [
        ("en-US-Neural2-D", "Neural2-D_Deep"),
        ("en-US-Neural2-J", "Neural2-J_Warm"),
        ("en-US-Neural2-A", "Neural2-A_Mature"),
        ("en-US-Wavenet-D", "Wavenet-D_Classic"),
    ]
    
    print("🏰 EPIC FANTASY BASS VOICE COMPARISON")
    print("=" * 60)
    print("Creating Game of Thrones-style narration with different voices\n")
    
    results = []
    for voice_name, voice_label in voices_to_test:
        print(f"\n🎭 Testing {voice_label}...")
        print("-" * 40)
        result = create_epic_bass_narration_chunks(voice_name, voice_label)
        if result:
            results.append((voice_label, result))
        print()
    
    if results:
        print("=" * 60)
        print("⚔️ EPIC NARRATION COMPLETE!")
        print("\n🎧 Listen for:")
        print("  • Depth and gravitas in the opening lines")
        print("  • Authority in Blackstone's dialogue")
        print("  • Ominous tone in the prophecy")
        print("  • Building tension throughout")
        print("\n🏆 Neural2-D should sound the deepest and most 'Game of Thrones'")
        print("   Neural2-J might be warmer but still commanding")
    
    return results


if __name__ == "__main__":
    print("🏰 Google TTS Epic Fantasy Drama Generator")
    print("Creating Game of Thrones-style narration with maximum bass\n")
    
    # Create the epic narration in chunks
    result = create_epic_bass_narration_chunks("en-US-Neural2-D", "Neural2-D")
    
    if result:
        print("\n✅ Epic narration ready!")
        print("\n🎭 Voice Effects Used:")
        print("  • Pitch: -6 to -8 semitones (extremely deep)")
        print("  • Rate: 0.6 to 0.9 (slow and dramatic)")
        print("  • Volume: Dynamic range for emphasis")
        print("  • Pauses: Long breaks for tension")
        print("\n📖 This should sound like a professional audiobook narrator")
        print("   for dark fantasy epics!")
        print("\n💡 Tip: The two audio files can be concatenated for the full story")
    
    # Uncomment to test multiple voices:
    # test_multiple_bass_voices()