"""
voice_input.py
Records audio from the microphone and saves it as a temporary WAV file,
ready to be sent to Groq's Whisper API for transcription.

Used by the CLI (chatbot.py) and GUI (chatbot_gui.py) versions.
The Web App version doesn't need this — the browser records audio itself
via the MediaRecorder API (see flask_app/static/script.js) and just POSTs
the resulting blob to the /transcribe endpoint.
"""

import tempfile

import sounddevice as sd
from scipy.io.wavfile import write as write_wav

SAMPLE_RATE = 16000  # Whisper works fine with 16kHz mono audio


def record_audio(duration: float = 5.0, sample_rate: int = SAMPLE_RATE) -> str:
    """
    Records `duration` seconds of audio from the default microphone
    and writes it to a temporary .wav file.

    Returns the filesystem path to that temp file. The caller is
    responsible for deleting it afterwards (e.g. with os.remove()).
    """
    print(f"🎙️  Recording for {duration:.0f} seconds... speak now!")
    recording = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
    )
    sd.wait()  # blocks until the recording is done
    print("✅ Recording finished, transcribing...")

    tmp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    write_wav(tmp_file.name, sample_rate, recording)
    return tmp_file.name
