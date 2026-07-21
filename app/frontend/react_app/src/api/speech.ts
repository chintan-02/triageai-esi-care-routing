import { apiRequest } from '@/api/client';
import type { SpeechTranscriptionResponse } from '@/types/speech';

const extensionByMimeType: Record<string, string> = {
  'audio/aac': 'aac',
  'audio/flac': 'flac',
  'audio/mp4': 'm4a',
  'audio/mpeg': 'mp3',
  'audio/ogg': 'ogg',
  'audio/wav': 'wav',
  'audio/webm': 'webm'
};

function recordingFilename(audio: Blob): string {
  if (audio instanceof File && audio.name.trim()) return audio.name;

  const mimeType = audio.type.split(';', 1)[0].toLowerCase();
  const extension = extensionByMimeType[mimeType] ?? 'webm';
  return `recording.${extension}`;
}

export function transcribeRecording(
  audio: Blob
): Promise<SpeechTranscriptionResponse> {
  const formData = new FormData();
  formData.append('audio_file', audio, recordingFilename(audio));

  return apiRequest<SpeechTranscriptionResponse>('/speech/transcribe', {
    method: 'POST',
    body: formData
  });
}
