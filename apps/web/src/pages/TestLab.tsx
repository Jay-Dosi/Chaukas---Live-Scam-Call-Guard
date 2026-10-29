import { useEffect, useState, useRef, useMemo } from 'react';
import { useTranslation } from '@i18n/useTranslation';
import { fetchScenarios, fetchScenario, runBenchmark, triggerBolnaCall, playTtsAudio, stopAllTtsAudio } from '@api/client';
import type { ScenarioBrief, ScenarioFull, BenchmarkResult } from '@api/client';
import { Button } from '@components/Button';
import type { ServerEvent } from '@protocol/index';

export function TestLabPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<'scenarios' | 'fireDrill' | 'benchmark'>('scenarios');

  // ─────────────────────────────────────────────────────────────
  // 1. Scenarios (Player / Injection) State
  // ─────────────────────────────────────────────────────────────
  const [scenarios, setScenarios] = useState<ScenarioBrief[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('');
  const [selectedScenario, setSelectedScenario] = useState<ScenarioFull | null>(null);
  const [isPlayingScenario, setIsPlayingScenario] = useState(false);
  const [playScenarioAudio, setPlayScenarioAudio] = useState(true);
  const [playerSpeed, setPlayerSpeed] = useState<number>(2.0);
  const [liveTranscript, setLiveTranscript] = useState<Array<{ id: string; text: string; isFinal: boolean }>>([]);
  const [liveScore, setLiveScore] = useState<number>(0);
  const [liveLevel, setLiveLevel] = useState<string>('calm');
  const [liveTactics, setLiveTactics] = useState<string[]>([]);
  const [scenarioSummary, setScenarioSummary] = useState<any | null>(null);
  const playerWsRef = useRef<WebSocket | null>(null);

  // ─────────────────────────────────────────────────────────────
  // 2. Fire-Drill State
  // ─────────────────────────────────────────────────────────────
  const [drillScenarioId, setDrillScenarioId] = useState<string>('');
  const [drillLang, setDrillLang] = useState<string>('en-IN');
  const [drillActive, setDrillActive] = useState<boolean>(false);
  const [drillAwaitingChip, setDrillAwaitingChip] = useState<boolean>(false);
  const [callerLine, setCallerLine] = useState<{ text: string; node_id: string; pressure: number; tactics: string[] } | null>(null);
  const [drillHistory, setDrillHistory] = useState<Array<{ speaker: 'caller' | 'user'; text: string; act?: string }>>([]);
  const [drillResult, setDrillResult] = useState<{ outcome: 'safe' | 'unsafe'; scorecard: any; debrief: any } | null>(null);
  const drillWsRef = useRef<WebSocket | null>(null);

  // Bolna AI Telephony State
  const [bolnaPhone, setBolnaPhone] = useState<string>('');
  const [bolnaLoading, setBolnaLoading] = useState<boolean>(false);
  const [bolnaMessage, setBolnaMessage] = useState<string | null>(null);
  const [bolnaError, setBolnaError] = useState<string | null>(null);

  // ─────────────────────────────────────────────────────────────
  // 3. Benchmark State
  // ─────────────────────────────────────────────────────────────
  const [noiseWer, setNoiseWer] = useState<number>(0.0);
  const [sensitivity, setSensitivity] = useState<'standard' | 'high'>('standard');
  const [benchmarkResult, setBenchmarkResult] = useState<BenchmarkResult | null>(null);
  const [benchmarkLoading, setBenchmarkLoading] = useState<boolean>(false);
  const [caseFilter, setCaseFilter] = useState<'all' | 'scam' | 'genuine' | 'fail'>('all');

  // Load scenarios on mount
  useEffect(() => {
    fetchScenarios().then((list) => {
      setScenarios(list);
      if (list && list.length > 0 && list[0]) {
        setSelectedScenarioId(list[0].id);
        const scamOne = list.find((s) => s.label === 'scam');
        if (scamOne) setDrillScenarioId(scamOne.id);
      }
    }).catch(console.error);
  }, []);

  // When selectedScenarioId changes, fetch full scenario
  useEffect(() => {
    if (selectedScenarioId) {
      fetchScenario(selectedScenarioId).then(setSelectedScenario).catch(console.error);
    }
  }, [selectedScenarioId]);

  // ─────────────────────────────────────────────────────────────
  // Scenario Injection Handlers
  // ─────────────────────────────────────────────────────────────
  const startScenarioReplay = () => {
    if (!selectedScenarioId) return;
    setIsPlayingScenario(true);
    setLiveTranscript([]);
    setLiveScore(0);
    setLiveLevel('calm');
    setLiveTactics([]);
    setScenarioSummary(null);

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/session`;
    const ws = new WebSocket(wsUrl);
    playerWsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'start',
        mode: 'inject',
        scenario_id: selectedScenarioId,
        lang: selectedScenario?.lang || 'en-IN',
        sensitivity: 'standard',
        speed: playerSpeed,
      }));
    };

    ws.onmessage = (event) => {
      try {
        const msg: ServerEvent = JSON.parse(event.data);
        if (msg.type === 'partial') {
          setLiveTranscript((prev) => {
            const idx = prev.findIndex((p) => p.id === msg.id);
            if (idx >= 0) {
              const copy = [...prev];
              copy[idx] = { id: msg.id, text: msg.text, isFinal: false };
              return copy;
            }
            return [...prev, { id: msg.id, text: msg.text, isFinal: false }];
          });
        } else if (msg.type === 'final') {
          setLiveTranscript((prev) => {
            const filtered = prev.filter((p) => p.id !== msg.id);
            return [...filtered, { id: msg.id, text: msg.text, isFinal: true }];
          });
          if (playScenarioAudio) {
            playTtsAudio(msg.text, selectedScenario?.lang || 'en-IN');
          }
        } else if (msg.type === 'analysis') {
          setLiveScore(msg.analysis.score);
          setLiveLevel(msg.analysis.level);
          const tacs = (msg.analysis.hits || []).map((h: any) => h.signal_id);
          setLiveTactics(Array.from(new Set(tacs)));
        } else if (msg.type === 'summary') {
          setScenarioSummary(msg);
          setIsPlayingScenario(false);
        } else if (msg.type === 'closed') {
          setIsPlayingScenario(false);
        }
      } catch (err) {
        console.error('WS parse error:', err);
      }
    };

    ws.onclose = () => {
      setIsPlayingScenario(false);
    };
  };

  const stopScenarioReplay = () => {
    stopAllTtsAudio();
    if (playerWsRef.current) {
      try {
        playerWsRef.current.send(JSON.stringify({ type: 'stop' }));
        playerWsRef.current.close();
      } catch {}
    }
    setIsPlayingScenario(false);
  };

  // ─────────────────────────────────────────────────────────────
  // Fire-Drill Handlers
  // ─────────────────────────────────────────────────────────────
  const startFireDrill = () => {
    if (!drillScenarioId) return;
    setDrillActive(true);
    setDrillResult(null);
    setCallerLine(null);
    setDrillHistory([]);
    setDrillAwaitingChip(false);

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/drill`;
    const ws = new WebSocket(wsUrl);
    drillWsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'start',
        mode: 'drill',
        scenario_id: drillScenarioId,
        lang: drillLang,
        sensitivity: 'standard',
      }));
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'caller') {
          setCallerLine({
            text: msg.text,
            node_id: msg.node_id,
            pressure: msg.pressure,
            tactics: msg.tactics || [],
          });
          setDrillHistory((prev) => [...prev, { speaker: 'caller', text: msg.text }]);
          setDrillAwaitingChip(true);

          // Speak caller lines aloud via Sarvam Bulbul / browser speech synthesis
          playTtsAudio(msg.text, drillLang);
        } else if (msg.type === 'ended') {
          setDrillResult({
            outcome: msg.outcome,
            scorecard: msg.scorecard,
            debrief: msg.debrief,
          });
          setDrillActive(false);
          setDrillAwaitingChip(false);
        }
      } catch (err) {
        console.error('Drill WS error:', err);
      }
    };

    ws.onclose = () => {
      setDrillActive(false);
    };
  };

  const handleSendChip = (act: 'hangup' | 'verify' | 'refuse' | 'question' | 'comply') => {
    if (!drillWsRef.current || drillWsRef.current.readyState !== WebSocket.OPEN) return;
    setDrillAwaitingChip(false);

    const chipLabels: Record<string, string> = {
      hangup: 'Call hung up',
      verify: 'I will verify this independently with my bank/police',
      refuse: 'I refuse to share codes or transfer money',
      question: 'Which official station and officer ID?',
      comply: 'Okay, I will share the code / transfer the money',
    };

    const label = chipLabels[act] || act;
    setDrillHistory((prev) => [...prev, { speaker: 'user', text: label, act }]);
    drillWsRef.current.send(JSON.stringify({ type: 'chip', act }));
  };

  const stopFireDrill = () => {
    stopAllTtsAudio();
    if (drillWsRef.current) {
      try {
        drillWsRef.current.send(JSON.stringify({ type: 'stop' }));
        drillWsRef.current.close();
      } catch {}
    }
    setDrillActive(false);
  };

  const handleTriggerBolnaCall = async () => {
    if (!bolnaPhone.trim()) {
      setBolnaError('Please enter a valid phone number with country code (e.g. +919876543210)');
      return;
    }
    setBolnaLoading(true);
    setBolnaError(null);
    setBolnaMessage(null);
    try {
      const res = await triggerBolnaCall(bolnaPhone.trim(), drillScenarioId || 'courier-customs-en-01');
      setBolnaMessage(res.message);
    } catch (err: any) {
      setBolnaError(err.message || 'Failed to trigger Bolna call');
    } finally {
      setBolnaLoading(false);
    }
  };

  // ─────────────────────────────────────────────────────────────
  // Benchmark Handlers
  // ─────────────────────────────────────────────────────────────
  const handleRunBenchmark = async () => {
    setBenchmarkLoading(true);
    try {
      const res = await runBenchmark({
        noise_wer: noiseWer,
        sensitivity,
      });
      setBenchmarkResult(res);
    } catch (err) {
      console.error('Benchmark failed:', err);
    } finally {
      setBenchmarkLoading(false);
    }
  };

  const exportBenchmarkJson = () => {
    if (!benchmarkResult) return;
    const blob = new Blob([JSON.stringify(benchmarkResult, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chaukas-benchmark-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportBenchmarkCsv = () => {
    if (!benchmarkResult) return;
    const headers = ['id', 'label', 'lang', 'result', 'score', 'level', 'time_to_danger', 'explanation'];
    const rows = benchmarkResult.cases.map((c) => [
      c.id,
      c.label,
      c.lang,
      c.result,
      c.score,
      c.level,
      c.time_to_danger ?? '',
      `"${c.explanation.replace(/"/g, '""')}"`,
    ]);
    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chaukas-cases-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const filteredCases = useMemo(() => {
    if (!benchmarkResult) return [];
    if (caseFilter === 'scam') return benchmarkResult.cases.filter((c) => c.label === 'scam');
    if (caseFilter === 'genuine') return benchmarkResult.cases.filter((c) => c.label === 'genuine');
    if (caseFilter === 'fail') return benchmarkResult.cases.filter((c) => c.result === 'fail');
    return benchmarkResult.cases;
  }, [benchmarkResult, caseFilter]);

  // ─────────────────────────────────────────────────────────────
  // RENDER: Tab 1 - Scenario Player
  // ─────────────────────────────────────────────────────────────
  const renderScenariosTab = () => (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(280px, 1fr) 2fr', gap: '20px' }}>
        {/* Left Column: Scenario Selector & Parameters */}
        <div className="card">
          <h3>{t('scenarios.title')}</h3>
          <div className="form__group" style={{ marginBottom: '14px' }}>
            <label className="form__label">{t('fireDrill.chooseScenario')}</label>
            <select
              className="form__input"
              value={selectedScenarioId}
              onChange={(e) => setSelectedScenarioId(e.target.value)}
              disabled={isPlayingScenario}
            >
              {scenarios.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.id} — {s.title[t('common.language') === 'hi' ? 'hi' : 'en'] || s.title.en}
                </option>
              ))}
            </select>
          </div>

          {selectedScenario && (
            <div style={{ fontSize: 'var(--t-sm)', color: 'var(--ink-2)', marginBottom: '16px', lineHeight: 1.5 }}>
              <div><strong>Language:</strong> {selectedScenario.lang}</div>
              <div><strong>Label:</strong> <span style={{ fontWeight: 600, color: selectedScenario.label === 'scam' ? 'var(--danger)' : 'var(--calm)' }}>{selectedScenario.label.toUpperCase()}</span></div>
              <div><strong>Expected Danger:</strong> Turn {selectedScenario.expect?.dangerByTurn ?? 'N/A'}</div>
              <div><strong>Tactics:</strong> {selectedScenario.tactics?.join(', ')}</div>
            </div>
          )}

          <div className="form__group" style={{ marginBottom: '16px' }}>
            <label className="form__label">Replay Speed</label>
            <select
              className="form__input"
              value={playerSpeed}
              onChange={(e) => setPlayerSpeed(Number(e.target.value))}
              disabled={isPlayingScenario}
            >
              <option value={1.0}>1.0x Realtime</option>
              <option value={2.0}>2.0x Fast</option>
              <option value={4.0}>4.0x Turbo</option>
            </select>
          </div>

          <div className="form__group" style={{ marginBottom: '16px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: 'var(--t-sm)' }}>
              <input
                type="checkbox"
                checked={playScenarioAudio}
                onChange={(e) => setPlayScenarioAudio(e.target.checked)}
              />
              <span>Speak caller lines aloud (Acoustic audio playback)</span>
            </label>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            {!isPlayingScenario ? (
              <Button variant="primary" large onClick={startScenarioReplay} disabled={!selectedScenarioId} style={{ flex: 1 }}>
                {t('scenarios.runInjection')}
              </Button>
            ) : (
              <Button variant="danger" large onClick={stopScenarioReplay} style={{ flex: 1 }}>
                Stop Replay
              </Button>
            )}
          </div>
        </div>

        {/* Right Column: Split Script & Live Ingestion */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', borderBottom: '1px solid var(--line)', paddingBottom: '10px' }}>
            <div>
              <strong>Live Status:</strong>{' '}
              <span style={{
                padding: '2px 8px',
                borderRadius: 'var(--radius)',
                fontWeight: 700,
                fontSize: 'var(--t-xs)',
                background: liveLevel === 'critical' ? 'var(--critical-bg)' : liveLevel === 'danger' ? 'var(--danger-bg)' : liveLevel === 'caution' ? 'var(--caution-bg)' : 'var(--calm-bg)',
                color: liveLevel === 'critical' ? 'var(--critical)' : liveLevel === 'danger' ? 'var(--danger)' : liveLevel === 'caution' ? 'var(--caution)' : 'var(--calm)',
              }}>
                {liveLevel.toUpperCase()} ({liveScore}/100)
              </span>
            </div>
            {liveTactics.length > 0 && (
              <div style={{ fontSize: 'var(--t-xs)', color: 'var(--ink-2)' }}>
                Tactics: <strong>{liveTactics.join(', ')}</strong>
              </div>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', minHeight: '260px' }}>
            {/* Scenario Ground Truth Script */}
            <div>
              <div style={{ fontSize: 'var(--t-xs)', fontWeight: 600, color: 'var(--ink-3)', marginBottom: '8px', textTransform: 'uppercase' }}>
                {t('scenarios.splitView.script')}
              </div>
              <div style={{ maxHeight: '280px', overflowY: 'auto', background: 'var(--surface-sunk)', padding: '10px', border: '1px solid var(--line)' }}>
                {selectedScenario?.nodes ? (
                  Object.entries(selectedScenario.nodes).map(([k, node]) => (
                    <div key={k} style={{ marginBottom: '8px', fontSize: 'var(--t-sm)', borderBottom: '1px dashed var(--line)', paddingBottom: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                      <div style={{ flex: 1 }}>
                        <span style={{ fontWeight: 600, color: 'var(--ink-2)' }}>[{k}]</span> {node.caller.text}
                      </div>
                      <button
                        type="button"
                        onClick={() => playTtsAudio(node.caller.text, selectedScenario.lang)}
                        style={{ border: '1px solid var(--line)', background: 'var(--surface)', padding: '2px 6px', fontSize: 'var(--t-xs)', cursor: 'pointer', whiteSpace: 'nowrap', borderRadius: 'var(--radius)' }}
                        title="Listen to this line"
                      >
                        Play Line
                      </button>
                    </div>
                  ))
                ) : (
                  <div style={{ color: 'var(--ink-3)', fontSize: 'var(--t-sm)' }}>Select a scenario to view script</div>
                )}
              </div>
            </div>

            {/* Live Recognized Transcript */}
            <div>
              <div style={{ fontSize: 'var(--t-xs)', fontWeight: 600, color: 'var(--ink-3)', marginBottom: '8px', textTransform: 'uppercase' }}>
                {t('scenarios.splitView.analysis')}
              </div>
              <div style={{ maxHeight: '280px', overflowY: 'auto', background: 'var(--surface-sunk)', padding: '10px', border: '1px solid var(--line)' }}>
                {liveTranscript.length > 0 ? (
                  liveTranscript.map((item) => (
                    <div key={item.id} style={{ marginBottom: '6px', fontSize: 'var(--t-sm)', color: item.isFinal ? 'var(--ink)' : 'var(--ink-3)' }}>
                      {item.text}
                    </div>
                  ))
                ) : (
                  <div style={{ color: 'var(--ink-3)', fontSize: 'var(--t-sm)' }}>
                    {isPlayingScenario ? 'Streaming transcript...' : 'Click "Send directly" to run'}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Scenario Completion Summary Card */}
          {scenarioSummary && (
            <div style={{ marginTop: '16px', padding: '12px', background: 'var(--surface-sunk)', border: '1px solid var(--line)' }}>
              <div style={{ fontWeight: 600, marginBottom: '6px' }}>Replay Result Summary:</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', fontSize: 'var(--t-sm)' }}>
                <div>Peak: <strong>{scenarioSummary.peak_level.toUpperCase()} ({scenarioSummary.peak_score})</strong></div>
                <div>Caution: <strong>{scenarioSummary.time_to_caution ? `${scenarioSummary.time_to_caution}ms` : '—'}</strong></div>
                <div>Danger: <strong>{scenarioSummary.time_to_danger ? `${scenarioSummary.time_to_danger}ms` : '—'}</strong></div>
                <div>Critical: <strong>{scenarioSummary.time_to_critical ? `${scenarioSummary.time_to_critical}ms` : '—'}</strong></div>
              </div>
              <div style={{ marginTop: '8px', fontSize: 'var(--t-xs)', color: 'var(--ink-2)' }}>
                Detected: <strong>{scenarioSummary.detected_tactics?.join(', ') || 'None'}</strong> | Missed: <strong>{scenarioSummary.missed_tactics?.join(', ') || 'None'}</strong>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // ─────────────────────────────────────────────────────────────
  // RENDER: Tab 2 - Fire Drill UI
  // ─────────────────────────────────────────────────────────────
  const renderFireDrillTab = () => (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      {!drillActive && !drillResult ? (
        /* Pre-Screen Configuration & Disclosure */
        <div className="card">
          <h2>{t('fireDrill.title')}</h2>
          <div style={{ padding: '12px', background: 'var(--caution-bg)', border: '1px solid var(--caution)', margin: '16px 0', fontSize: 'var(--t-sm)', color: 'var(--ink)' }}>
            <strong>{t('fireDrill.disclosure.title')}:</strong> {t('fireDrill.disclosure.text')}
            <div style={{ marginTop: '6px', fontWeight: 600 }}>{t('fireDrill.disclosure.stopWord')}</div>
          </div>

          <div className="form__group" style={{ marginBottom: '14px' }}>
            <label className="form__label">{t('fireDrill.chooseScenario')}</label>
            <select
              className="form__input"
              value={drillScenarioId}
              onChange={(e) => setDrillScenarioId(e.target.value)}
            >
              {scenarios.filter((s) => s.label === 'scam').map((s) => (
                <option key={s.id} value={s.id}>
                  {s.id} — {s.title[t('common.language') === 'hi' ? 'hi' : 'en'] || s.title.en}
                </option>
              ))}
            </select>
          </div>

          <div className="form__group" style={{ marginBottom: '20px' }}>
            <label className="form__label">{t('fireDrill.chooseLanguage')}</label>
            <select
              className="form__input"
              value={drillLang}
              onChange={(e) => setDrillLang(e.target.value)}
            >
              <option value="en-IN">{t('common.english')} (en-IN)</option>
              <option value="hi-IN">{t('common.hindi')} (hi-IN)</option>
              <option value="auto">Hinglish / Auto</option>
            </select>
          </div>

          <Button variant="primary" large onClick={startFireDrill} disabled={!drillScenarioId} style={{ width: '100%' }}>
            {t('fireDrill.disclosure.acknowledge')}
          </Button>

          {/* Real Phone Drill via Bolna AI Telephony */}
          <div className="card" style={{ marginTop: '24px', border: '1px solid var(--line)', background: 'var(--surface-sunk)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ fontSize: 'var(--t-xs)', fontWeight: 700, padding: '2px 8px', background: 'var(--action)', color: 'var(--surface)', borderRadius: 'var(--radius)' }}>
                BOLNA AI
              </span>
              <h3 style={{ margin: 0 }}>Real Phone Drill (Telephony Call)</h3>
            </div>
            <p style={{ fontSize: 'var(--t-sm)', color: 'var(--ink-2)', marginBottom: '14px', lineHeight: 1.5 }}>
              Practice on an actual phone call! Bolna's AI voice agent will place an outbound call to your mobile phone playing the selected scam scenario. Answer on speakerphone, switch to <strong>Live Guard</strong>, and watch Chaukas protect you live!
            </p>

            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'flex-end', marginBottom: '8px' }}>
              <div className="form__group" style={{ flex: 1, minWidth: '220px' }}>
                <label className="form__label">Recipient Phone Number (with country code)</label>
                <input
                  type="tel"
                  className="form__input"
                  placeholder="+919876543210"
                  value={bolnaPhone}
                  onChange={(e) => setBolnaPhone(e.target.value)}
                  disabled={bolnaLoading}
                />
              </div>
              <Button
                variant="secondary"
                large
                onClick={handleTriggerBolnaCall}
                disabled={bolnaLoading || !bolnaPhone.trim()}
                style={{ minWidth: '180px' }}
              >
                {bolnaLoading ? 'Queuing Call...' : 'Call My Phone'}
              </Button>
            </div>

            {bolnaMessage && (
              <div style={{ padding: '10px 12px', background: 'var(--calm-bg)', border: '1px solid var(--calm)', fontSize: 'var(--t-sm)', color: 'var(--calm)', marginTop: '8px' }}>
                <strong>Call Queued!</strong> {bolnaMessage}
              </div>
            )}

            {bolnaError && (
              <div style={{ padding: '10px 12px', background: 'var(--danger-bg)', border: '1px solid var(--danger)', fontSize: 'var(--t-sm)', color: 'var(--danger)', marginTop: '8px' }}>
                <strong>Note:</strong> {bolnaError}
              </div>
            )}
          </div>
        </div>
      ) : drillActive ? (
        /* Active Drill Interactive Call */
        <div className="card" style={{ border: '2px solid var(--action)' }}>
          {/* SIMULATION Banner */}
          <div style={{
            background: 'var(--ink)',
            color: 'var(--surface)',
            padding: '6px 12px',
            textAlign: 'center',
            fontWeight: 700,
            fontSize: 'var(--t-xs)',
            letterSpacing: '1px',
            marginBottom: '16px',
          }}>
            {t('fireDrill.simulationLabel')} — NEVER SHARE REAL OTP OR PASSWORDS
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div style={{ fontSize: 'var(--t-sm)', color: 'var(--ink-2)' }}>
              Node: <strong>{callerLine?.node_id || 'Connecting...'}</strong>
            </div>
            <Button variant="danger" onClick={stopFireDrill}>
              {t('fireDrill.stopButton')}
            </Button>
          </div>

          {/* Dialogue Transcript Stream */}
          <div style={{
            minHeight: '220px',
            maxHeight: '340px',
            overflowY: 'auto',
            background: 'var(--surface-sunk)',
            padding: '14px',
            border: '1px solid var(--line)',
            marginBottom: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
          }}>
            {drillHistory.map((item, idx) => (
              <div
                key={idx}
                style={{
                  alignSelf: item.speaker === 'caller' ? 'flex-start' : 'flex-end',
                  maxWidth: '80%',
                  background: item.speaker === 'caller' ? 'var(--surface)' : 'var(--action-bg, #eef4ff)',
                  border: item.speaker === 'caller' ? '1px solid var(--line)' : '1px solid var(--action)',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius)',
                  fontSize: 'var(--t-sm)',
                }}
              >
                <div style={{ fontSize: 'var(--t-xs)', fontWeight: 600, color: item.speaker === 'caller' ? 'var(--danger)' : 'var(--action)', marginBottom: '2px' }}>
                  {item.speaker === 'caller' ? t('fireDrill.callerLabel') : t('fireDrill.youLabel')}
                </div>
                <div>{item.text}</div>
              </div>
            ))}
          </div>

          {/* Interactive Response Chips */}
          <div>
            <div style={{ fontSize: 'var(--t-xs)', fontWeight: 600, color: 'var(--ink-2)', marginBottom: '8px' }}>
              Your response choices:
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              <Button
                variant="danger"
                onClick={() => handleSendChip('hangup')}
                disabled={!drillAwaitingChip}
              >
                Hang up (Exit Call)
              </Button>
              <Button
                variant="secondary"
                onClick={() => handleSendChip('verify')}
                disabled={!drillAwaitingChip}
              >
                Verify Independently
              </Button>
              <Button
                variant="secondary"
                onClick={() => handleSendChip('refuse')}
                disabled={!drillAwaitingChip}
              >
                Refuse to comply
              </Button>
              <Button
                variant="secondary"
                onClick={() => handleSendChip('question')}
                disabled={!drillAwaitingChip}
              >
                Question Authority
              </Button>
              <Button
                variant="secondary"
                onClick={() => handleSendChip('comply')}
                disabled={!drillAwaitingChip}
                style={{ borderColor: 'var(--danger)', color: 'var(--danger)' }}
              >
                Comply with demand
              </Button>
            </div>
          </div>
        </div>
      ) : (
        /* Debrief Scorecard */
        drillResult && (
          <div className="card">
            <div style={{
              padding: '12px 16px',
              background: drillResult.outcome === 'safe' ? 'var(--calm-bg)' : 'var(--danger-bg)',
              border: `2px solid ${drillResult.outcome === 'safe' ? 'var(--calm)' : 'var(--danger)'}`,
              marginBottom: '16px',
              textAlign: 'center',
            }}>
              <h2 style={{ color: drillResult.outcome === 'safe' ? 'var(--calm)' : 'var(--danger)', margin: 0 }}>
                {drillResult.outcome === 'safe' ? t('fireDrill.outcomes.safe') : t('fireDrill.outcomes.unsafe')}
              </h2>
              <div style={{ fontSize: 'var(--t-sm)', marginTop: '4px' }}>
                Final Defensive Score: <strong>{drillResult.scorecard.score} / 100</strong>
              </div>
            </div>

            <h3>{t('fireDrill.debrief.scorecard')}</h3>
            <table className="table" style={{ marginBottom: '16px' }}>
              <thead>
                <tr>
                  <th>Behavior / Decision</th>
                  <th style={{ textAlign: 'right' }}>Points</th>
                </tr>
              </thead>
              <tbody>
                {drillResult.scorecard.breakdown?.map((item: any, i: number) => (
                  <tr key={i}>
                    <td>{item.rule}</td>
                    <td style={{ textAlign: 'right', fontWeight: 600, color: item.points >= 0 ? 'var(--calm)' : 'var(--danger)' }}>
                      {item.points > 0 ? `+${item.points}` : item.points}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div style={{ padding: '12px', background: 'var(--surface-sunk)', border: '1px solid var(--line)', marginBottom: '16px', fontSize: 'var(--t-sm)' }}>
              <strong>{t('fireDrill.debrief.oneThingToRemember')}:</strong>
              <p style={{ margin: '4px 0 0 0', color: 'var(--ink-2)' }}>{drillResult.debrief.advice}</p>
            </div>

            <Button variant="primary" large onClick={() => { setDrillResult(null); setDrillActive(false); }} style={{ width: '100%' }}>
              Practice Another Scenario
            </Button>
          </div>
        )
      )}
    </div>
  );

  // ─────────────────────────────────────────────────────────────
  // RENDER: Tab 3 - Benchmark UI
  // ─────────────────────────────────────────────────────────────
  const renderBenchmarkTab = () => (
    <div style={{ maxWidth: '950px', margin: '0 auto' }}>
      {/* Benchmark Controls */}
      <div className="card" style={{ marginBottom: '16px' }}>
        <h2>{t('benchmark.title')}</h2>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'flex-end', marginTop: '12px' }}>
          <div className="form__group" style={{ flex: 1, minWidth: '180px' }}>
            <label className="form__label">
              {t('benchmark.controls.noiseLevel')}: <strong>{(noiseWer * 100).toFixed(0)}% WER</strong>
            </label>
            <input
              type="range"
              className="form__input"
              min="0"
              max="0.4"
              step="0.1"
              value={noiseWer}
              onChange={(e) => setNoiseWer(Number(e.target.value))}
              disabled={benchmarkLoading}
            />
          </div>

          <div className="form__group" style={{ flex: 1, minWidth: '160px' }}>
            <label className="form__label">{t('benchmark.controls.sensitivity')}</label>
            <select
              className="form__input"
              value={sensitivity}
              onChange={(e) => setSensitivity(e.target.value as any)}
              disabled={benchmarkLoading}
            >
              <option value="standard">{t('setup.sections.sensitivityStandard')}</option>
              <option value="high">{t('setup.sections.sensitivityHigh')}</option>
            </select>
          </div>

          <Button
            variant="primary"
            large
            onClick={handleRunBenchmark}
            disabled={benchmarkLoading}
            style={{ minWidth: '160px' }}
          >
            {benchmarkLoading ? t('benchmark.controls.running') : t('benchmark.controls.runButton')}
          </Button>
        </div>
      </div>

      {/* Benchmark Result Summary Strip */}
      {benchmarkResult && (
        <>
          <div className="summary-strip" style={{ marginBottom: '16px' }}>
            <div className="summary-strip__item">
              <div className="summary-strip__value" style={{ color: benchmarkResult.summary.recall_at_danger >= 0.85 ? 'var(--calm)' : 'var(--danger)' }}>
                {(benchmarkResult.summary.recall_at_danger * 100).toFixed(1)}%
              </div>
              <div className="summary-strip__label">{t('benchmark.summary.recall')}</div>
            </div>
            <div className="summary-strip__item">
              <div className="summary-strip__value" style={{ color: benchmarkResult.summary.false_alarm_rate <= 0.08 ? 'var(--calm)' : 'var(--danger)' }}>
                {(benchmarkResult.summary.false_alarm_rate * 100).toFixed(1)}%
              </div>
              <div className="summary-strip__label">{t('benchmark.summary.falseAlarms')}</div>
            </div>
            <div className="summary-strip__item">
              <div className="summary-strip__value">
                {benchmarkResult.summary.median_time_to_danger} ms
              </div>
              <div className="summary-strip__label">{t('benchmark.summary.medianTimeToDanger')}</div>
            </div>
            <div className="summary-strip__item">
              <div className="summary-strip__value">
                {benchmarkResult.summary.total_cases}
              </div>
              <div className="summary-strip__label">Cases ({benchmarkResult.summary.scam_cases}s / {benchmarkResult.summary.genuine_cases}g)</div>
            </div>
          </div>

          {/* SVG Threshold Sweep Curve */}
          <div className="card" style={{ marginBottom: '16px' }}>
            <h3>{t('benchmark.sweepChart.title')} (Thresholds 30 to 90)</h3>
            <div style={{ marginTop: '12px' }}>
              <svg viewBox="0 0 600 200" style={{ width: '100%', height: 'auto', background: 'var(--surface-sunk)', border: '1px solid var(--line)' }}>
                {/* Horizontal grid lines */}
                <line x1="40" y1="20" x2="570" y2="20" stroke="var(--line)" strokeWidth="1" />
                <line x1="40" y1="95" x2="570" y2="95" stroke="var(--line)" strokeWidth="1" strokeDasharray="2 2" />
                <line x1="40" y1="170" x2="570" y2="170" stroke="var(--line)" strokeWidth="1" />

                {/* Y-axis labels */}
                <text x="32" y="24" fontSize="10" textAnchor="end" fill="var(--ink-3)">100%</text>
                <text x="32" y="99" fontSize="10" textAnchor="end" fill="var(--ink-3)">50%</text>
                <text x="32" y="174" fontSize="10" textAnchor="end" fill="var(--ink-3)">0%</text>

                {/* Points & Lines for Detection Rate and False Alarm Rate */}
                {(() => {
                  const pts = benchmarkResult.sweep || [];
                  if (pts.length < 2) return null;
                  const getX = (t: number) => 40 + ((t - 30) / (90 - 30)) * 530;
                  const getY = (r: number) => 170 - r * 150;

                  const recallPath = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(p.threshold)} ${getY(p.detection_rate)}`).join(' ');
                  const faPath = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(p.threshold)} ${getY(p.false_alarm_rate)}`).join(' ');

                  return (
                    <>
                      <path d={recallPath} fill="none" stroke="var(--ink)" strokeWidth="2.5" />
                      <path d={faPath} fill="none" stroke="var(--danger)" strokeWidth="2" strokeDasharray="4 3" />
                      {pts.map((p) => (
                        <g key={p.threshold}>
                          <circle cx={getX(p.threshold)} cy={getY(p.detection_rate)} r="3" fill="var(--ink)" />
                          <circle cx={getX(p.threshold)} cy={getY(p.false_alarm_rate)} r="3" fill="var(--danger)" />
                          <text x={getX(p.threshold)} y="185" fontSize="10" textAnchor="middle" fill="var(--ink-3)">{p.threshold}</text>
                        </g>
                      ))}
                    </>
                  );
                })()}
              </svg>
              <div style={{ display: 'flex', gap: '20px', marginTop: '8px', fontSize: 'var(--t-xs)', justifyContent: 'center' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '14px', height: '3px', background: 'var(--ink)' }}></span> {t('benchmark.sweepChart.detectionRate')}
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '14px', height: '2px', borderTop: '2px dashed var(--danger)' }}></span> {t('benchmark.sweepChart.falseAlarmRate')}
                </span>
              </div>
            </div>
          </div>

          {/* Per-Tactic Detection Table */}
          <div className="card" style={{ marginBottom: '16px' }}>
            <h3>{t('benchmark.perTactic.title')}</h3>
            <table className="table" style={{ marginTop: '10px' }}>
              <thead>
                <tr>
                  <th>{t('benchmark.perTactic.tactic')}</th>
                  <th>{t('benchmark.perTactic.detected')}</th>
                  <th>{t('benchmark.perTactic.total')}</th>
                  <th style={{ textAlign: 'right' }}>{t('benchmark.perTactic.rate')}</th>
                </tr>
              </thead>
              <tbody>
                {benchmarkResult.per_tactic.map((tactic) => (
                  <tr key={tactic.tactic}>
                    <td><strong>{tactic.tactic}</strong></td>
                    <td>{tactic.detected}</td>
                    <td>{tactic.total}</td>
                    <td style={{ textAlign: 'right', fontWeight: 600 }}>{(tactic.rate * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Test Cases Table with Filter */}
          <div className="card" style={{ marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h3>{t('benchmark.caseTable.title')} ({filteredCases.length})</h3>
              <div style={{ display: 'flex', gap: '6px' }}>
                {(['all', 'scam', 'genuine', 'fail'] as const).map((f) => (
                  <button
                    key={f}
                    className={`btn ${caseFilter === f ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ padding: '2px 8px', fontSize: 'var(--t-xs)' }}
                    onClick={() => setCaseFilter(f)}
                  >
                    {f.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ maxHeight: '380px', overflowY: 'auto' }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>{t('benchmark.caseTable.id')}</th>
                    <th>{t('benchmark.caseTable.label')}</th>
                    <th>Lang</th>
                    <th>Score</th>
                    <th>Level</th>
                    <th>TTD</th>
                    <th>{t('benchmark.caseTable.result')}</th>
                    <th>Analysis Details</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCases.map((c) => (
                    <tr key={c.id}>
                      <td><strong>{c.id}</strong></td>
                      <td>
                        <span style={{
                          padding: '1px 6px',
                          borderRadius: 'var(--radius)',
                          fontSize: 'var(--t-xs)',
                          background: c.label === 'scam' ? 'var(--danger-bg)' : 'var(--calm-bg)',
                          color: c.label === 'scam' ? 'var(--danger)' : 'var(--calm)',
                        }}>
                          {c.label}
                        </span>
                      </td>
                      <td>{c.lang}</td>
                      <td>{c.score}</td>
                      <td>{c.level}</td>
                      <td>{c.time_to_danger ? `${c.time_to_danger}ms` : '—'}</td>
                      <td>
                        <span style={{
                          padding: '1px 6px',
                          borderRadius: 'var(--radius)',
                          fontWeight: 700,
                          fontSize: 'var(--t-xs)',
                          background: c.result === 'pass' ? 'var(--calm-bg)' : 'var(--danger-bg)',
                          color: c.result === 'pass' ? 'var(--calm)' : 'var(--danger)',
                        }}>
                          {c.result.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ fontSize: 'var(--t-xs)', color: 'var(--ink-2)', maxWidth: '280px' }}>{c.explanation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Export JSON / CSV */}
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            <Button variant="secondary" onClick={exportBenchmarkJson}>
              {t('benchmark.export.json')}
            </Button>
            <Button variant="secondary" onClick={exportBenchmarkCsv}>
              {t('benchmark.export.csv')}
            </Button>
          </div>
        </>
      )}
    </div>
  );

  return (
    <div>
      {/* Top Level Test Lab Tabs */}
      <div className="tabs" role="tablist" style={{ marginBottom: '20px' }}>
        <button
          role="tab"
          aria-selected={activeTab === 'scenarios'}
          className={`tabs__item ${activeTab === 'scenarios' ? 'tabs__item--active' : ''}`}
          onClick={() => { stopAllTtsAudio(); setActiveTab('scenarios'); }}
        >
          {t('scenarios.title')}
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'fireDrill'}
          className={`tabs__item ${activeTab === 'fireDrill' ? 'tabs__item--active' : ''}`}
          onClick={() => { stopAllTtsAudio(); setActiveTab('fireDrill'); }}
        >
          {t('fireDrill.title')}
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'benchmark'}
          className={`tabs__item ${activeTab === 'benchmark' ? 'tabs__item--active' : ''}`}
          onClick={() => { stopAllTtsAudio(); setActiveTab('benchmark'); }}
        >
          {t('benchmark.title')}
        </button>
      </div>

      {activeTab === 'scenarios' && renderScenariosTab()}
      {activeTab === 'fireDrill' && renderFireDrillTab()}
      {activeTab === 'benchmark' && renderBenchmarkTab()}
    </div>
  );
}
