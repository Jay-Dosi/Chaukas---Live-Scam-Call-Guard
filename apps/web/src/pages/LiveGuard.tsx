import { useEffect, useRef, useState } from 'react';
import { Phone, Mic, MicOff, Shield, AlertTriangle } from 'lucide-react';
import { useTranslation } from '@i18n/useTranslation';
import { useSessionStore } from '@state/session';
import { useSettingsStore } from '@state/settings';
import { SessionSocket, startSession, stopSession, muteForAlert } from '@api/sessionSocket';
import { fetchHealth, playTtsAudio } from '@api/client';
import type { HealthData } from '@api/client';
import { StateBlock } from '@components/StateBlock';
import { TranscriptView } from '@components/TranscriptView';
import { SignalList } from '@components/SignalList';
import { RiskTimeline } from '@components/RiskTimeline';
import { Button } from '@components/Button';

export function LiveGuardPage() {
  const { t } = useTranslation();
  const {
    level,
    score,
    analysis,
    isListening,
    transcriptParts,
    setIsListening,
    resetSession,
    setLevel,
    setScore,
    setAnalysis,
    appendTranscript,
    addAlert,
  } = useSessionStore();

  const { voiceAlerts, alertSensitivity } = useSettingsStore();
  const [socket, setSocket] = useState<SessionSocket | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [providers, setProviders] = useState<HealthData | null>(null);
  const [consentGiven, setConsentGiven] = useState(() => {
    try {
      return localStorage.getItem('chaukas_mic_consent') === 'true';
    } catch {
      return false;
    }
  });
  const [showConsent, setShowConsent] = useState(false);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const [startTime, setStartTime] = useState<number | null>(null);
  const durationRef = useRef<number>();
  const isListeningRef = useRef<boolean>(false);
  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const analysisHistoryRef = useRef<Array<{ score: number; level: string; t_ms: number }>>([]);

  // Initialize socket
  useEffect(() => {
    const ws = new SessionSocket();
    setSocket(ws);

    ws.on('ready', (evt) => {
      setProviders(evt.providers as any);
    });

    ws.on('analysis', (evt) => {
      const a = evt.analysis;
      setAnalysis(a);
      setLevel(a.level);
      setScore(a.score);
      analysisHistoryRef.current.push({ score: a.score, level: a.level, t_ms: a.t_ms });
    });

    ws.on('final', (evt) => {
      appendTranscript(evt.id, evt.text, true, evt.t_start_ms);
    });

    ws.on('partial', (evt) => {
      appendTranscript(evt.id, evt.text, false, evt.t_ms);
    });

    ws.on('alert', (evt) => {
      addAlert(evt.level, evt.text_en);
      if (voiceAlerts) {
        speakAlert(evt.text_en);
      }
      // Mute transcript ingestion during alert
      muteForAlert(ws, evt.cooldown_ms);
    });

    ws.on('error', (evt) => {
      console.error('WS error:', evt);
    });

    ws.connect();

    return () => {
      ws.close();
    };
  }, [appendTranscript, setAnalysis, setLevel, setScore, addAlert, voiceAlerts]);

  // Fetch health on mount
  useEffect(() => {
    fetchHealth().then(setProviders).catch(console.error);
  }, []);

  // Duration timer
  useEffect(() => {
    if (isListening && startTime) {
      durationRef.current = setInterval(() => {
        // Duration updates via session store
      }, 1000);
    }
    return () => {
      if (durationRef.current) clearInterval(durationRef.current);
    };
  }, [isListening, startTime]);

  const formatDuration = (ms: number) => {
    const mins = Math.floor(ms / 60000);
    const secs = Math.floor((ms % 60000) / 1000).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  };

  const handleStart = async () => {
    if (!consentGiven) {
      setShowConsent(true);
      return;
    }
    setShowConsent(false);
    try {
      localStorage.setItem('chaukas_mic_consent', 'true');
    } catch {}

    try {
      // 1. Initialize session on backend first
      if (socket) {
        startSession(socket, {
          mode: 'live',
          lang: 'auto',
          sensitivity: alertSensitivity,
          fixture_id: undefined,
        });
      }

      // 2. Request microphone
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: false,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000,
          channelCount: 1,
        },
      });
      mediaStreamRef.current = stream;

      // 3. AudioWorklet for server-side STT (Sarvam)
      try {
        const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
        audioContextRef.current = audioContext;
        await audioContext.audioWorklet.addModule('/audio/capture.worklet.js');

        const workletNode = new AudioWorkletNode(audioContext, 'pcm-processor');
        workletNodeRef.current = workletNode;

        const source = audioContext.createMediaStreamSource(stream);
        source.connect(workletNode);

        workletNode.port.onmessage = (e) => {
          if (e.data.type === 'pcm' && socket) {
            socket.sendBinary(e.data.buffer);
          }
        };
      } catch (workletErr) {
        console.warn('AudioWorklet setup warning (falling back to Web Speech):', workletErr);
      }

      const now = Date.now();
      isListeningRef.current = true;
      setIsListening(true);
      setStartTime(now);

      // 4. Client-side Web Speech API fallback for immediate 0ms live transcription
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        try {
          const recognition = new SpeechRecognition();
          recognition.continuous = true;
          recognition.interimResults = true;
          const { callLanguage } = useSettingsStore.getState();
          recognition.lang = callLanguage === 'hi-IN' ? 'hi-IN' : 'en-IN';

          let turnId = `live_${Date.now()}`;
          recognition.onresult = (evt: any) => {
            const results = evt.results;
            for (let i = evt.resultIndex; i < results.length; i++) {
              const res = results[i];
              const text = res[0]?.transcript?.trim();
              if (!text) continue;
              const isFinal = res.isFinal;
              const segId = `${turnId}_${i}`;
              const elapsedMs = Date.now() - now;

              appendTranscript(segId, text, isFinal, elapsedMs);

              if (socket) {
                socket.send({
                  type: 'text',
                  id: segId,
                  text,
                  is_final: isFinal,
                  t_ms: elapsedMs,
                });
              }
              if (isFinal) {
                turnId = `live_${Date.now()}`;
              }
            }
          };

          recognition.onerror = (e: any) => {
            console.warn('Web Speech fallback notice:', e.error);
          };

          recognition.onend = () => {
            if (isListeningRef.current) {
              try { recognition.start(); } catch {}
            }
          };

          recognition.start();
          recognitionRef.current = recognition;
        } catch (e) {
          console.warn('Web Speech API not available or blocked:', e);
        }
      }
    } catch (err) {
      console.error('Mic error:', err);
      alert(t('errors.micDenied'));
    }
  };

  const handleStop = () => {
    isListeningRef.current = false;

    // Clean up Web Speech
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {}
      recognitionRef.current = null;
    }

    // Clean up media stream tracks
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }

    // Clean up audio
    workletNodeRef.current?.disconnect();
    audioContextRef.current?.close();
    mediaRecorderRef.current?.stop();

    if (socket) stopSession(socket);
    setIsListening(false);
    setStartTime(null);
    resetSession();
  };

  const handleCall1930 = () => {
    window.open('tel:1930', '_self');
  };

  const handleAlertFamily = () => {
    const { familyContactNumber } = useSettingsStore.getState();
    if (familyContactNumber) {
      const msg = encodeURIComponent(`Chaukas Alert: Possible scam call detected at ${new Date().toLocaleTimeString()}. Top tactics: ${analysis?.hits?.map((h) => h.signal_id).join(', ') || 'Unknown'}`);
      window.open(`https://wa.me/${familyContactNumber.replace('+', '')}?text=${msg}`, '_blank');
    }
  };

  const speakAlert = (text: string) => {
    const { callLanguage } = useSettingsStore.getState();
    playTtsAudio(text, callLanguage === 'hi-IN' ? 'hi-IN' : 'en-IN');
  };

  const duration = startTime ? Date.now() - startTime : 0;

  if (showConsent) {
    return (
      <div className="card" style={{maxWidth: '600px', margin: '0 auto'}}>
        <h2>{t('liveGuard.consent.title')}</h2>
        <p>{t('liveGuard.consent.text')}</p>
        <label style={{display: 'flex', alignItems: 'flex-start', gap: '12px', margin: '16px 0', cursor: 'pointer'}}>
          <input
            type="checkbox"
            checked={consentGiven}
            onChange={(e) => {
              setConsentGiven(e.target.checked);
              if (e.target.checked) {
                try { localStorage.setItem('chaukas_mic_consent', 'true'); } catch {}
              }
            }}
          />
          <span>{t('liveGuard.consent.agree')}</span>
        </label>
        <Button
          variant="primary"
          large
          onClick={() => {
            setShowConsent(false);
            setConsentGiven(true);
            try { localStorage.setItem('chaukas_mic_consent', 'true'); } catch {}
            handleStart();
          }}
          disabled={!consentGiven}
        >
          {t('liveGuard.consent.continue')}
        </Button>
        <Button variant="secondary" onClick={() => setShowConsent(false)} style={{marginLeft: '12px'}}>
          {t('common.cancel')}
        </Button>
      </div>
    );
  }

  if (!isListening) {
    return (
      <div className="state-block state-block--calm" style={{textAlign: 'center', maxWidth: '600px', margin: '0 auto'}}>
        <Shield size={64} style={{color: 'var(--calm)', marginBottom: '16px'}} />
        <h2 style={{fontSize: 'var(--t-2xl)', marginBottom: '16px'}}>{t('liveGuard.ready')}</h2>
        <p style={{fontSize: 'var(--t-lg)', color: 'var(--ink-2)', marginBottom: '24px'}}>{t('liveGuard.disclaimer')}</p>
        <ul style={{textAlign: 'left', display: 'inline-block', marginBottom: '24px', color: 'var(--ink-2)'}}>
          {Array.isArray(t('liveGuard.instructions')) &&
            (t('liveGuard.instructions') as string[]).map((inst: string, i: number) => (
              <li key={i} style={{marginBottom: '12px', fontSize: 'var(--t-md)'}}>{inst}</li>
            ))}
        </ul>
        <Button variant="primary" large onClick={handleStart} style={{minWidth: '280px'}}>
          <Mic size={24} style={{marginRight: '8px'}} />
          {t('liveGuard.startButton')}
        </Button>
      </div>
    );
  }

  return (
    <div>
      <StateBlock
        level={level}
        score={score}
        reason={analysis?.reason_en || ''}
        duration={formatDuration(duration)}
        onStop={handleStop}
        onCall1930={handleCall1930}
        onAlertFamily={handleAlertFamily}
        showDetails={showDetails}
        onToggleDetails={() => setShowDetails(!showDetails)}
        isListening={isListening}
      />

      <div style={{marginTop: '16px'}}>
        <TranscriptView
          segments={transcriptParts}
          hits={analysis?.hits || []}
          showDetails={showDetails}
        />
      </div>

      {showDetails && analysis && (
        <div style={{marginTop: '16px', display: 'grid', gap: '16px'}}>
          <div className="card">
            <h3 style={{fontSize: 'var(--t-lg)', fontWeight: 600, marginBottom: '12px', borderBottom: '2px solid var(--line-strong)', paddingBottom: '8px'}}>
              {t('liveGuard.statusPanel.speech')}
            </h3>
            <SignalList hits={analysis.hits} combos={analysis.combos} />
          </div>

          <div className="card">
            <h3 style={{fontSize: 'var(--t-lg)', fontWeight: 600, marginBottom: '12px', borderBottom: '2px solid var(--line-strong)', paddingBottom: '8px'}}>
              Risk Timeline
            </h3>
            <RiskTimeline
              history={analysisHistoryRef.current as any}
              thresholds={{ caution: 30, danger: 55, critical: 80 }}
              width={800}
            />
          </div>

          <div className="status-panel">
            <div className="status-panel__item">
              <span className="status-panel__label">{t('liveGuard.statusPanel.speech')}: </span>
              <span className="status-panel__value">{providers?.stt?.provider || 'Unknown'}</span>
            </div>
            <div className="status-panel__item">
              <span className="status-panel__label">{t('liveGuard.statusPanel.voice')}: </span>
              <span className="status-panel__value">{providers?.tts?.provider || 'Browser'}</span>
            </div>
            <div className="status-panel__item">
              <span className="status-panel__label">{t('liveGuard.statusPanel.secondOpinion')}: </span>
              <span className="status-panel__value">{providers?.llm?.enabled ? 'Enabled' : 'Off'}</span>
            </div>
          </div>
        </div>
      )}

      <div className="action-bar" style={{display: 'flex', gap: '12px', justifyContent: 'center', marginTop: '24px', paddingTop: '16px', borderTop: '1px solid var(--line)'}}>
        <Button variant="secondary" onClick={handleStop} large>
          <MicOff size={24} style={{marginRight: '8px'}} />
          {t('liveGuard.stopButton')}
        </Button>
        {(level === 'danger' || level === 'critical') && (
          <>
            <Button variant="danger" onClick={handleCall1930} large>
              <Phone size={24} style={{marginRight: '8px'}} />
              {t('liveGuard.sessionSummary.call1930')}
            </Button>
            <Button variant="danger" onClick={handleAlertFamily} large>
              <AlertTriangle size={24} style={{marginRight: '8px'}} />
              {t('liveGuard.sessionSummary.alertFamily')}
            </Button>
          </>
        )}
      </div>
    </div>
  );
}