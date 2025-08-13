from pydub import AudioSegment
from faster_whisper import WhisperModel
import librosa
import soundfile as sf
from tempfile import NamedTemporaryFile

def transcribe_audio(input_wav):
    audio_data, sample_rate = librosa.load(input_wav, sr=16000)
    intervals = librosa.effects.split(audio_data, top_db=30)

    model = WhisperModel("large", device="cuda")
    all_text = []

    for start, end in intervals:
        duration = (end - start) / sample_rate
        if duration < 1.0:
            continue

        chunk = audio_data[start:end]
        with NamedTemporaryFile(suffix=".wav", delete=True) as temp_audio:
            sf.write(temp_audio.name, chunk, sample_rate)
            segments, _ = model.transcribe(temp_audio.name, language="en")
            chunk_text = "".join([seg.text for seg in segments])
            all_text.append(chunk_text)

    return " ".join(all_text)
