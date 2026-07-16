"""
voice_input.py
Records audio from the microphone using simple energy-based voice activity
detection (VAD): recording starts immediately and stops automatically once
the person has spoken and then gone quiet for a bit — instead of always
recording for a fixed, arbitrary duration regardless of how long the
message actually was.

Used by the CLI (chatbot.py) and GUI (chatbot_gui.py) versions.
The Web App version doesn't need this — the browser already records with a
manual start/stop click via the MediaRecorder API (see
flask_app/static/script.js) and just POSTs the resulting blob to the
/transcribe endpoint; there was never a fixed-duration limitation there.
"""

import tempfile

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write as write_wav

SAMPLE_RATE = 16000       # Whisper works fine with 16kHz mono audio
BLOCK_DURATION = 0.1      # seconds per analysis block — short enough to feel responsive
SILENCE_THRESHOLD = 300   # RMS amplitude (int16 scale) below which a block counts as "quiet"
SILENCE_DURATION = 1.2    # seconds of continuous quiet after speech before stopping
MAX_DURATION = 15.0       # hard cap so a noisy room or a stuck-open mic can't record forever


def _block_rms(block: np.ndarray) -> float:
    """Root-mean-square amplitude of one audio block — a simple, fast proxy
    for "how loud is this" that needs nothing beyond numpy (already pulled
    in transitively by scipy, which was already a dependency here)."""
    return float(np.sqrt(np.mean(block.astype(np.float32) ** 2)))


def record_audio(
    sample_rate: int = SAMPLE_RATE,
    silence_threshold: float = SILENCE_THRESHOLD,
    silence_duration: float = SILENCE_DURATION,
    max_duration: float = MAX_DURATION,
) -> str:
    """
    Records audio from the default microphone with simple voice activity
    detection: recording starts immediately, and stops automatically once
    the person has spoken and then been quiet for `silence_duration`
    seconds — or after `max_duration` seconds regardless, as a safety net
    against a stuck-open mic or a persistently noisy room.

    This is deliberately a plain RMS-amplitude threshold, not a full
    ML-based VAD (e.g. webrtcvad or Silero). That's enough to solve the
    actual problem — stop recording once the person's done talking —
    without adding a new dependency, including one that's historically
    been finicky to install on Windows specifically (webrtcvad needs a C
    compiler there, the exact kind of environment friction this project
    has already run into more than once today).

    Returns the filesystem path to the resulting temp .wav file. The caller
    is responsible for deleting it afterwards (e.g. with os.remove()).
    """
    block_size = int(sample_rate * BLOCK_DURATION)
    silence_blocks_needed = int(silence_duration / BLOCK_DURATION)
    max_blocks = int(max_duration / BLOCK_DURATION)

    recorded_blocks = []
    consecutive_silent_blocks = 0
    speech_detected = False

    print("🎙️  Dengarkan... (bicara sekarang, berhenti otomatis begitu kamu diam)")

    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16") as stream:
        for _ in range(max_blocks):
            block, _overflowed = stream.read(block_size)
            recorded_blocks.append(block)

            if _block_rms(block) > silence_threshold:
                speech_detected = True
                consecutive_silent_blocks = 0
            else:
                consecutive_silent_blocks += 1

            # Only start counting silence as "done talking" AFTER some
            # speech has actually been heard — otherwise the person just
            # hasn't started yet, which isn't the same as being finished.
            if speech_detected and consecutive_silent_blocks >= silence_blocks_needed:
                break

    print("✅ Selesai merekam.")

    audio = np.concatenate(recorded_blocks, axis=0)

    tmp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    write_wav(tmp_file.name, sample_rate, audio)
    return tmp_file.name