/**
 * Browser speech helpers for the telephony voice simulator.
 * Uses backend OpenAI TTS when configured, otherwise Web Speech API.
 */
import { synthesizeSpeech } from '../services/api'

export function speakText(text, language = 'en') {
  if (!window.speechSynthesis || !text?.trim()) return false

  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = language === 'ml' ? 'ml-IN' : 'en-IN'
  utterance.rate = 1
  window.speechSynthesis.speak(utterance)
  return true
}

export async function speakTextWithBackend(text, language = 'en') {
  if (!text?.trim()) return { ok: false, provider: 'none' }

  try {
    const result = await synthesizeSpeech(text, language)
    if (result?.audio_base64) {
      const mime = result.content_type || 'audio/mpeg'
      const audio = new Audio(`data:${mime};base64,${result.audio_base64}`)
      await audio.play()
      return { ok: true, provider: result.provider || 'openai' }
    }
  } catch {
    // Fall through to browser TTS
  }

  const ok = speakText(text, language)
  return { ok, provider: ok ? 'browser' : 'none' }
}

export function speakTextPromise(text, language = 'en') {
  return new Promise((resolve) => {
    if (!window.speechSynthesis || !text?.trim()) {
      resolve(false)
      return
    }

    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = language === 'ml' ? 'ml-IN' : 'en-IN'
    utterance.rate = 0.95 // slightly slower for clearer articulation
    utterance.volume = 1
    utterance.pitch = 1
    utterance.onend = () => resolve(true)
    utterance.onerror = () => resolve(false)
    window.speechSynthesis.speak(utterance)
  })
}

let activeAudio = null

export async function cancelActiveAudio() {
  if (activeAudio) {
    try {
      activeAudio.pause()
      activeAudio.src = ""
    } catch (e) {}
    activeAudio = null
  }
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel()
    // After bot speech finishes, pause briefly to avoid clipping before listening again
    await new Promise(resolve => setTimeout(resolve, 300));
  }
}

export function speakAudioUriPromise(audioUri) {
  return new Promise((resolve) => {
    if (!audioUri) {
      resolve(false);
      return;
    }
    const audio = new Audio(audioUri);
    activeAudio = audio;
    audio.onended = () => {
      if (activeAudio === audio) activeAudio = null;
      resolve(true);
    };
    audio.onerror = () => {
      if (activeAudio === audio) activeAudio = null;
      resolve(false);
    };
    audio.play().catch(() => {
      if (activeAudio === audio) activeAudio = null;
      resolve(false);
    });
  });
}

export async function speakTextWithBackendPromise(text, language = 'en') {
  if (!text?.trim()) return { ok: false, provider: 'none' }

  try {
    const result = await synthesizeSpeech(text, language)
    if (result?.audio_base64) {
      const mime = result.content_type || 'audio/mpeg'
      const audioUri = `data:${mime};base64,${result.audio_base64}`
      const ok = await speakAudioUriPromise(audioUri)
      return { ok, provider: result.provider || 'openai' }
    }
  } catch {
    // Fall through to browser TTS
  }

  const ok = await speakTextPromise(text, language)
  return { ok, provider: ok ? 'browser' : 'none' }
}

export function isSpeechRecognitionSupported() {
  return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition)
}

export function createSpeechRecognition(language = 'en') {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return null;

  const recognition = new SpeechRecognition();
  recognition.lang = language === 'ml' ? 'ml-IN' : 'en-IN';
  recognition.interimResults = false; // disable interim for full phrases
  recognition.continuous = false; // single utterance per start
  // If user starts speaking while bot is talking, cancel the bot audio to simulate human interruption.
  recognition.onspeechstart = () => {
    // Cancel any currently playing audio or speech synthesis.
    cancelActiveAudio();
  };
  return recognition;
}

export async function recordAudioBlob(durationMs = 5000) {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  const recorder = new MediaRecorder(stream)
  const chunks = []

  return new Promise((resolve, reject) => {
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) chunks.push(event.data)
    }
    recorder.onerror = () => reject(new Error('Recording failed'))
    recorder.onstop = async () => {
      stream.getTracks().forEach((track) => track.stop())
      const blob = new Blob(chunks, { type: recorder.mimeType || 'audio/webm' })
      resolve(blob)
    }
    recorder.start()
    setTimeout(() => {
      if (recorder.state !== 'inactive') recorder.stop()
    }, durationMs)
  })
}

export function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}
