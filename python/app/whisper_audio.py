import whisper

class WhisperProcessor:
    def __init__(self, model_path='base', fp16=False):
        self.model = whisper.load_model(model_path)
        self.option = whisper.DecodingOptions(fp16=fp16)

    def audio_to_text(self, audio_content):
        
        audio = whisper.load_audio(audio_content)
        audio = whisper.pad_or_trim(audio)

        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)

        _, probs = self.model.detect_language(mel)
        language = f"Detected Language: {max(probs, key=probs.get)}"

        result = whisper.decode(self.model, mel, self.option)

        return result.text, language