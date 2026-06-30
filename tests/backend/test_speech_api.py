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
    assert body == {
        "transcript": "",
        "confidence": None,
        "language": "en-US",
        "is_placeholder": True,
        "message": (
            "Speech-to-text contract is ready. Azure Speech integration will "
            "be added in the next implementation phase."
        ),
    }
