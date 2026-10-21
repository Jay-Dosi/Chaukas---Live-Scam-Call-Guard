import { createContext, useContext, useCallback, useState, ReactNode, ReactElement, createElement } from 'react';
import type { EnTranslations } from './en';
import type { HiTranslations } from './hi';

import { en } from './en';
import { hi } from './hi';

type Language = 'en' | 'hi';

export const translations: Record<Language, EnTranslations | HiTranslations> = {
  en,
  hi,
};

interface TranslationContextValue {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (key: string) => string;
}

const TranslationContext = createContext<TranslationContextValue | null>(null);

function deepGet(obj: unknown, path: string): string {
  const keys = path.split('.');
  let current: unknown = obj;
  for (const k of keys) {
    if (current && typeof current === 'object' && k in current) {
      current = (current as Record<string, unknown>)[k];
    } else {
      return '';
    }
  }
  return typeof current === 'string' ? current : '';
}

function useBaseTranslation(lang: Language) {
  const dict = translations[lang] ?? en;
  return useCallback(
    (key: string): string => {
      const val = deepGet(dict, key);
      if (val) return val;
      const enVal = deepGet(en, key);
      return enVal || key;
    },
    [dict],
  );
}

export function TranslationProvider({ children }: { children: ReactNode }): ReactElement {
  const stored = localStorage.getItem('chaukas-lang') as Language | null;
  const [lang, setLang] = useState<Language>(stored ?? 'en');

  const t = useBaseTranslation(lang);

  const setLangWithStorage = useCallback(
    (l: Language) => {
      setLang(l);
      localStorage.setItem('chaukas-lang', l);
      document.documentElement.lang = l === 'hi' ? 'hi-IN' : 'en';
    },
    [],
  );

  const contextValue: TranslationContextValue = {
    lang,
    setLang: setLangWithStorage,
    t,
  };

  return createElement(
    TranslationContext.Provider,
    { value: contextValue },
    children
  );
}

export function useTranslation(): TranslationContextValue {
  const ctx = useContext(TranslationContext);
  if (!ctx) {
    throw new Error('useTranslation must be used within TranslationProvider');
  }
  return ctx;
}