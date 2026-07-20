from fastapi.testclient import TestClient

from app.backend.api.main import app


client = TestClient(app)


def test_speech_transcription_returns_placeholder_contract() -> None:
    response = client.post(
        "/speech/transcribe",
        files={"audio_file": ("sample.wav", b"placeholder-audio", "audio/wav")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["transcript_text"] == ""
    assert body["transcript"] == ""
    assert body["source"] == "speech_transcript"
    assert body["requires_clinician_review"] is True
    assert (
        "clinician review before NLP extraction or prediction"
        in body["disclaimer"]
    )
    assert "diagnosis" not in body
    assert "treatment" not in body
