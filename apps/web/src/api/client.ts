import type { Level } from '@protocol/index';

export interface HealthData {
  stt: { provider: string; streaming: boolean; langs: string[] };
  tts: { provider: string; voices: string[] };
  llm: { enabled: boolean; model: string | null };
  bolna?: { configured: boolean; agent_id: string | null };
  ffmpeg: boolean;
  version: string;
}

export interface ScenarioBrief {
  id: string;
  title: Record<string, string>;
  lang: string;
  label: 'scam' | 'genuine';
  tactics: string[];
  expect?: { dangerByTurn?: number; criticalByTurn?: number };
}

export interface ScenarioFull extends ScenarioBrief {
  disclosure: Record<string, string>;
  nodes: Record<string, ScenarioNode>;
  terminals: Record<string, ScenarioTerminal>;
}

export interface ScenarioNode {
  caller: { text: string; tactic: string[] };
  voice: string;
  next: Array<{ when: string; to: string }>;
}

export interface ScenarioTerminal {
  outcome: 'safe' | 'unsafe';
  debrief: string;
}

export interface BenchmarkRequest {
  noise_wer: number;
  sensitivity: string;
  danger_threshold?: number;
  seed?: number;
}

export interface BenchmarkResult {
  summary: BenchmarkSummary;
  per_tactic: BenchmarkTactic[];
  cases: BenchmarkCase[];
  sweep: BenchmarkSweepPoint[];
}

export interface BenchmarkSummary {
  recall_at_danger: number;
  false_alarm_rate: number;
  median_time_to_danger: number;
  p90_time_to_danger: number;
  total_cases: number;
  scam_cases: number;
  genuine_cases: number;
}

export interface BenchmarkTactic {
  tactic: string;
  detected: number;
  total: number;
  rate: number;
}

export interface BenchmarkCase {
  id: string;
  label: string;
  lang: string;
  tactics: string[];
  result: 'pass' | 'fail';
  score: number;
  level: Level;
  time_to_danger: number | null;
  explanation: string;
}

export interface BenchmarkSweepPoint {
  threshold: number;
  detection_rate: number;
  false_alarm_rate: number;
}

// Fetch /api/health with retry
export async function fetchHealth(): Promise<HealthData> {
  const res = await fetch('/api/health', { cache: 'no-store' });
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

// Fetch scenario list
export async function fetchScenarios(): Promise<ScenarioBrief[]> {
  const res = await fetch('/api/scenarios');
  if (!res.ok) throw new Error(`Failed to load scenarios: ${res.status}`);
  return res.json();
}

// Fetch a single scenario by ID
export async function fetchScenario(id: string): Promise<ScenarioFull> {
  const res = await fetch(`/api/scenarios/${id}`);
  if (!res.ok) throw new Error(`Failed to load scenario ${id}: ${res.status}`);
  return res.json();
}

// TTS endpoint
export async function fetchTts(text: string, lang: string, voice?: string): Promise<Blob> {
  const body: Record<string, unknown> = { text, lang };
  if (voice) body.voice = voice;
  const res = await fetch('/api/tts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (res.status === 204) throw new Error('TTS disabled');
  if (!res.ok) throw new Error(`TTS failed: ${res.status}`);
  return res.blob();
}

interface AudioQueueItem {
  text: string;
  lang: string;
  voice?: string;
  resolve: () => void;
}

const audioQueue: AudioQueueItem[] = [];
let isProcessingQueue = false;
let currentAudio: HTMLAudioElement | null = null;

/**
 * Cancel and stop all currently playing and queued TTS speech.
 */
export function stopAllTtsAudio(): void {
  audioQueue.length = 0;
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
  isProcessingQueue = false;
}

/**
 * Play speech audio aloud sequentially using server TTS (Sarvam Bulbul)
 * with browser speechSynthesis fallback. Queues incoming lines to prevent overlapping.
 */
export async function playTtsAudio(text: string, lang: string = 'en-IN', voice?: string): Promise<void> {
  if (!text || !text.trim()) return;

  return new Promise<void>((resolve) => {
    audioQueue.push({ text, lang, voice, resolve });
    drainAudioQueue();
  });
}

async function drainAudioQueue(): Promise<void> {
  if (isProcessingQueue) return;
  const item = audioQueue.shift();
  if (!item) return;

  isProcessingQueue = true;

  // 1. Try server TTS (Sarvam Bulbul)
  try {
    const blob = await fetchTts(item.text, item.lang, item.voice);
    if (blob && blob.size > 0) {
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);
      currentAudio = audio;

      await new Promise<void>((done) => {
        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          done();
        };
        audio.onerror = () => {
          URL.revokeObjectURL(audioUrl);
          done();
        };
        audio.play().catch(() => done());
      });

      currentAudio = null;
      item.resolve();
      isProcessingQueue = false;
      drainAudioQueue();
      return;
    }
  } catch (err) {
    console.warn('Server TTS unavailable, falling back to browser speech synthesis:', err);
  }

  // 2. Browser speech synthesis fallback
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    try {
      const utter = new SpeechSynthesisUtterance(item.text);
      utter.lang = item.lang.startsWith('hi') ? 'hi-IN' : 'en-US';
      utter.rate = 1.0;

      await new Promise<void>((done) => {
        utter.onend = () => done();
        utter.onerror = () => done();
        window.speechSynthesis.speak(utter);
      });
    } catch (e) {
      console.warn('Browser speechSynthesis failed:', e);
    }
  }

  item.resolve();
  isProcessingQueue = false;
  drainAudioQueue();
}

// Upload audio file for analysis
export async function uploadAudio(file: File): Promise<{ job_id: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch('/api/upload', {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}

// Run benchmark
export async function runBenchmark(req: BenchmarkRequest): Promise<BenchmarkResult> {
  const res = await fetch('/api/benchmark', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Benchmark failed: ${res.status}`);
  return res.json();
}

// Trigger outbound phone call via Bolna AI
export async function triggerBolnaCall(
  recipientPhoneNumber: string,
  scenarioId: string,
): Promise<{ status: string; execution_id: string; message: string }> {
  const res = await fetch('/api/bolna/call', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      recipient_phone_number: recipientPhoneNumber,
      scenario_id: scenarioId,
    }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: `Error ${res.status}` }));
    throw new Error(data.detail || 'Bolna call request failed');
  }
  return res.json();
}
