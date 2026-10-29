import { create } from 'zustand';
import type { Language } from '@i18n/useTranslation';

export type TextSize = 'normal' | 'large' | 'extra-large';
export type AlertSensitivity = 'standard' | 'high';
export type CallLanguage = 'en-IN' | 'hi-IN' | 'auto';

interface SettingsState {
  uiLanguage: Language;
  callLanguage: CallLanguage;
  familyContactName: string;
  familyContactNumber: string;
  alertSensitivity: AlertSensitivity;
  textSize: TextSize;
  voiceAlerts: boolean;
  detailsViewDefault: boolean;

  setUiLanguage: (lang: Language) => void;
  setCallLanguage: (lang: CallLanguage) => void;
  setFamilyContactName: (name: string) => void;
  setFamilyContactNumber: (number: string) => void;
  setAlertSensitivity: (s: AlertSensitivity) => void;
  setTextSize: (s: TextSize) => void;
  setVoiceAlerts: (v: boolean) => void;
  setDetailsViewDefault: (v: boolean) => void;
  loadFromStorage: () => void;
  saveToStorage: () => void;
  reset: () => void;
}

const STORAGE_KEY = 'chaukas-settings';

function getDefaultSettings(): Omit<
  Pick<
    SettingsState,
    | 'uiLanguage'
    | 'callLanguage'
    | 'alertSensitivity'
    | 'textSize'
    | 'voiceAlerts'
    | 'detailsViewDefault'
  >,
  ''
> {
  return {
    uiLanguage: 'en',
    callLanguage: 'auto',
    alertSensitivity: 'standard',
    textSize: 'normal',
    voiceAlerts: true,
    detailsViewDefault: false,
  };
}

// Apply text size to document
function applyTextSize(size: TextSize) {
  const root = document.documentElement;
  root.setAttribute('data-size', size);
}

const defaultSettings = getDefaultSettings();

export const useSettingsStore = create<SettingsState>((set, get) => ({
  uiLanguage: defaultSettings.uiLanguage,
  callLanguage: defaultSettings.callLanguage,
  familyContactName: '',
  familyContactNumber: '',
  alertSensitivity: defaultSettings.alertSensitivity,
  textSize: defaultSettings.textSize,
  voiceAlerts: defaultSettings.voiceAlerts,
  detailsViewDefault: defaultSettings.detailsViewDefault,

  setUiLanguage: (uiLanguage) =>
    set({ uiLanguage }),

  setCallLanguage: (callLanguage) =>
    set({ callLanguage }),

  setFamilyContactName: (familyContactName) =>
    set({ familyContactName }),

  setFamilyContactNumber: (familyContactNumber) =>
    set({ familyContactNumber }),

  setAlertSensitivity: (alertSensitivity) =>
    set({ alertSensitivity }),

  setTextSize: (textSize) => {
    applyTextSize(textSize);
    set({ textSize });
  },

  setVoiceAlerts: (voiceAlerts) => set({ voiceAlerts }),

  setDetailsViewDefault: (detailsViewDefault) => set({ detailsViewDefault }),

  loadFromStorage: () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        set(parsed);
        applyTextSize(get().textSize);
      }
    } catch {
      // Ignore corrupt storage
    }
  },

  saveToStorage: () => {
    try {
      const state = get();
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(state),
      );
    } catch {
      // Storage full or unavailable
    }
  },

  reset: () => {
    localStorage.removeItem(STORAGE_KEY);
    set(defaultSettings);
    applyTextSize(defaultSettings.textSize);
  },
}));

export function deleteAllData() {
  localStorage.removeItem(STORAGE_KEY);
  localStorage.removeItem('chaukas-lang');
  localStorage.removeItem('chaukas-sessions');
}