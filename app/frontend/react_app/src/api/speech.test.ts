import { beforeEach, describe, expect, it, vi } from 'vitest';
import { transcribeRecording } from './speech';

const { apiRequest } = vi.hoisted(() => ({
  apiRequest: vi.fn()
}));

vi.mock('@/api/client', () => ({
  apiRequest
}));

describe('transcribeRecording', () => {
  beforeEach(() => {
    apiRequest.mockReset();
    apiRequest.mockResolvedValue({});
  });

  it('posts the audio as multipart form data without setting Content-Type', async () => {
    const recording = new Blob(['recorded-audio'], { type: 'audio/webm;codecs=opus' });

    await transcribeRecording(recording);

    expect(apiRequest).toHaveBeenCalledOnce();
    const [path, options] = apiRequest.mock.calls[0];
    expect(path).toBe('/speech/transcribe');
    expect(options.method).toBe('POST');
    expect(options).not.toHaveProperty('headers');
    expect(options.body).toBeInstanceOf(FormData);

    const uploadedAudio = options.body.get('audio_file');
    expect(uploadedAudio).toBeInstanceOf(File);
    expect(uploadedAudio.name).toBe('recording.webm');
    expect(uploadedAudio.type).toBe('audio/webm;codecs=opus');
  });
});
