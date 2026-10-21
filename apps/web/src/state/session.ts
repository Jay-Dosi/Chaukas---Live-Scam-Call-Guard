import { create } from 'zustand';
import type { Language } from '@i18n/useTranslation';
import type { Analysis, Level } from '@api/sessionSocket';
import { useSettingsStore } from '@state/settings';

export interface SessionRecording {
  id: string;
  startTime: number;
  endTime: number;
  durationSecs: number;
  peakLevel: Level;
  tacticsHeard: string[];
  firstCautionMs: number | null;
  firstDangerMs: number | null;
  transcript: string;
}

export interface SessionState {
  level: Level;
  score: number;
  analysis: Analysis | null;
  isListening: boolean;
  transcriptParts: Array<{ id: string; text: string; isFinal: boolean; tMs: number }>;
  alerts: Array<{ level: Level; text: string; tMs: number }>;

  setLevel: (level: Level) => void;
  setScore: (score: number) => void;
  setAnalysis: (analysis: Analysis | null) => void;
  setIsListening: (listening: boolean) => void;
  appendTranscript: (id: string, text: string, isFinal: boolean, tMs: number) => void;
  addAlert: (level: Level, text: string) => void;
  resetSession: () => void;
}

const LEVELS: Level[] = ['calm', 'caution', 'danger', 'critical'];

// Determine level from score based on standard thresholds
// High sensitivity lowers by 8: caution >=22, danger >=47, critical >=72
function scoreToLevel(score: number, sensitivity: 'standard' | 'high'): Level {
  const cautious = sensitivity === 'high';
  if (score >= (cautious ? 72 : 80)) return 'critical';
  if (score >= (cautious ? 47 : 55)) return 'danger';
  if (score >= (cautious ? 22 : 30)) return 'caution';
  return 'calm';
}

export const useSessionStore = create<SessionState>((set, get) => ({
  level: 'calm',
  score: 0,
  analysis: null,
  isListening: false,
  transcriptParts: [],
  alerts: [],

  setLevel: (level) => {
    set({ level });
  },

  setScore: (score) => {
    const sensitivity = useSettingsStore.getState().alertSensitivity;
    const newLevel = scoreToLevel(score, sensitivity);
    set({ score, level: newLevel });
  },

  setAnalysis: (analysis) => {
    set({ analysis });
  },

  setIsListening: (isListening) => {
    set({ isListening });
    if (!isListening) {
      // Session ended — save recording
      const s = get();
      saveRecording(s);
    }
  },

  appendTranscript: (id, text, isFinal, tMs) => {
    set((state) => {
      const idx = state.transcriptParts.findIndex((p) => p.id === id);
      if (idx >= 0) {
        const updated = [...state.transcriptParts];
        updated[idx] = { id, text, isFinal, tMs };
        return { transcriptParts: updated };
      }
      return { transcriptParts: [...state.transcriptParts, { id, text, isFinal, tMs }] };
    });
  },

  addAlert: (level, text) => {
    set((state) => ({
      alerts: [...state.alerts, { level, text, tMs: Date.now() }],
    }));
  },

  resetSession: () => {
    set({
      level: 'calm',
      score: 0,
      analysis: null,
      isListening: false,
      transcriptParts: [],
      alerts: [],
    });
  },
}));

function saveRecording(state: SessionState) {
  try {
    const recordings = JSON.parse(localStorage.getItem('chaukas-sessions') ?? '[]');
    const recording: SessionRecording = {
      id: crypto.randomUUID(),
      startTime: Date.now() - Math.floor(
        state.transcriptParts.reduce((max, t) => Math.max(max, t.tMs), 0),
      ),
      endTime: Date.now(),
      durationSecs: Math.round((Date.now() - (recording.startTime || Date.now())) / 1000),
      peakLevel: state.level,
      tacticsHeard: state.analysis?.signals ?? [],
      firstCautionMs: null,
      firstDangerMs: null,
      transcript: state.transcriptParts.map((t) => t.text).join(' '),
    };
    recordings.push(recording);
    // Keep last 20 sessions
    localStorage.setItem('chaukas-sessions', JSON.stringify(recordings.slice(-20)));
  } catch {
    // Storage unavailable
  }
}
