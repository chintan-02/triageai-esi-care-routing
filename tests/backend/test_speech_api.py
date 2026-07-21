from pathlib import Path
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.backend.api.main import app
from app.backend.services import prediction_service, speech_service


client = TestClient(app)


def test_speech_transcription_accepts_multipart_and_handles_missing_credentials(
    monkeypatch,
) -> None:
    monkeypatch.setattr(speech_service.settings, "AZURE_SPEECH_KEY", "")
    monkeypatch.setattr(speech_service.settings, "AZURE_SPEECH_REGION", "")
    azure_transcriber = Mock()
    prediction = Mock()
    monkeypatch.setattr(
        speech_service,
        "_transcribe_file_with_azure",
        azure_transcriber,
    )
    monkeypatch.setattr(prediction_service, "predict_esi_for_intake", prediction)

    response = client.post(
        "/speech/transcribe",
        files={"audio_file": ("sample.wav", b"placeholder-audio", "audio/wav")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["transcript_text"] == ""
    assert body["transcript"] == ""
    assert body["source"] == "azure_speech_unconfigured"
    assert body["requires_clinician_review"] is True
    assert body["is_placeholder"] is True
    assert body["message"] == (
        "Azure Speech is not configured. Add AZURE_SPEECH_KEY and "
        "AZURE_SPEECH_REGION to enable transcription."
    )
    assert (
        "clinician review before NLP extraction or prediction"
        in body["disclaimer"]
    )
    assert "diagnosis" not in body
    assert "treatment" not in body
    azure_transcriber.assert_not_called()
    prediction.assert_not_called()


def test_speech_transcription_uses_mockable_azure_service_and_deletes_upload(
    monkeypatch,
) -> None:
    monkeypatch.setattr(speech_service.settings, "AZURE_SPEECH_KEY", "test-key")
    monkeypatch.setattr(speech_service.settings, "AZURE_SPEECH_REGION", "test-region")
    observed_path: Path | None = None

    def fake_azure_transcription(
        audio_path: Path,
        *,
        speech_key: str,
        speech_region: str,
    ) -> str:
        nonlocal observed_path
        observed_path = audio_path
        assert audio_path.exists()
        assert audio_path.read_bytes() == b"valid-audio"
        assert speech_key == "test-key"
        assert speech_region == "test-region"
        return "Patient reports dizziness since this morning."

    monkeypatch.setattr(
        speech_service,
        "_transcribe_file_with_azure",
        fake_azure_transcription,
    )

    response = client.post(
        "/speech/transcribe",
        files={"audio_file": ("recording.wav", b"valid-audio", "audio/wav")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["transcript_text"] == "Patient reports dizziness since this morning."
    assert body["transcript"] == body["transcript_text"]
    assert body["confidence"] is None
    assert body["language"] == "en-US"
    assert body["source"] == "azure_speech"
    assert body["requires_clinician_review"] is True
    assert body["is_placeholder"] is False
    assert body["message"] == (
        "Transcript generated. Clinician review is required before NLP "
        "extraction or prediction."
    )
    assert "clinician review before NLP extraction or prediction" in body["disclaimer"]
    assert observed_path is not None
    assert not observed_path.exists()


def test_speech_transcription_normalizes_invalid_audio_failure(monkeypatch) -> None:
    monkeypatch.setattr(speech_service.settings, "AZURE_SPEECH_KEY", "test-key")
    monkeypatch.setattr(speech_service.settings, "AZURE_SPEECH_REGION", "test-region")
    azure_transcriber = Mock(side_effect=RuntimeError("provider details"))
    monkeypatch.setattr(
        speech_service,
        "_transcribe_file_with_azure",
        azure_transcriber,
    )

    response = client.post(
        "/speech/transcribe",
        files={"audio_file": ("invalid.wav", b"invalid-audio", "audio/wav")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["transcript_text"] == ""
    assert body["transcript"] == ""
    assert body["source"] == "azure_speech_error"
    assert body["requires_clinician_review"] is True
    assert body["is_placeholder"] is True
    assert body["message"] == (
        "Audio could not be transcribed. Confirm the file contains supported "
        "audio and try again."
    )
    assert "provider details" not in response.text
