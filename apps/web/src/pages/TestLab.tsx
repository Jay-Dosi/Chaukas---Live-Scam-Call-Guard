import { useEffect, useState } from 'react';
import { useTranslation } from '@i18n/useTranslation';
import { fetchScenarios, fetchScenario, runBenchmark } from '@api/client';
import type { ScenarioBrief, ScenarioFull } from '@api/client';

export function TestLabPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<'scenarios' | 'fireDrill' | 'benchmark'>('scenarios');
  const [scenarios, setScenarios] = useState<ScenarioBrief[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<ScenarioFull | null>(null);
  const [viewMode, setViewMode] = useState<'script' | 'split'>('script');

  useEffect(() => {
    fetchScenarios().then(setScenarios).catch(console.error);
  }, []);

  const handleScenarioClick = async (id: string) => {
    const full = await fetchScenario(id);
    setSelectedScenario(full);
    setViewMode('split');
  };

  const renderScenariosTab = () => (
    <div>
      <div style={{display: 'flex', gap: '12px', marginBottom: '16px'}}>
        <button className={`btn ${viewMode === 'script' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setViewMode('script')}>
          {t('testLab.scenarios.runInjection')}
        </button>
        <button className={`btn ${viewMode === 'split' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setViewMode('split')}>
          {t('testLab.scenarios.runAcoustic')}
        </button>
      </div>

      <table className="table">
        <thead>
          <tr>
            <th>Title</th>
            <th>Language</th>
            <th>Label</th>
            <th>Tactics</th>
            <th>Expected Danger Turn</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {scenarios.map((s) => (
            <tr key={s.id}>
              <td>{s.title[t('common.language') === 'hi' ? 'hi' : 'en'] || s.title.en}</td>
              <td>{s.lang}</td>
              <td>
                <span style={{
                  padding: '2px 8px',
                  borderRadius: 'var(--radius)',
                  fontSize: 'var(--t-xs)',
                  fontWeight: 600,
                  background: s.label === 'scam' ? 'var(--danger-bg)' : 'var(--calm-bg)',
                  color: s.label === 'scam' ? 'var(--danger)' : 'var(--calm)',
                }}>
                  {t(`testLab.scenarios.labels.${s.label}`)}
                </span>
              </td>
              <td>{s.tactics.join(', ')}</td>
              <td>{s.expect?.dangerByTurn ?? '—'}</td>
              <td>
                <button className="btn btn-primary" onClick={() => handleScenarioClick(s.id)} style={{minWidth: '100px'}}>
                  {t('common.run')}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  const renderFireDrillTab = () => (
    <div className="card" style={{maxWidth: '700px'}}>
      <h2>{t('testLab.fireDrill.title')}</h2>
      <p style={{color: 'var(--ink-2)', marginBottom: '24px'}}>{t('testLab.fireDrill.disclosure.text')}</p>
      <div className="form__group" style={{marginBottom: '16px'}}>
        <label className="form__label">{t('testLab.fireDrill.chooseScenario')}</label>
        <select className="form__input" onChange={(e) => handleScenarioClick(e.target.value)}>
          <option value="">{t('common.select')}</option>
          {scenarios.filter(s => s.label === 'scam').map((s) => (
            <option key={s.id} value={s.id}>
              {s.title[t('common.language') === 'hi' ? 'hi' : 'en'] || s.title.en}
            </option>
          ))}
        </select>
      </div>
      <div className="form__group">
        <label className="form__label">{t('testLab.fireDrill.chooseLanguage')}</label>
        <select className="form__input">
          <option value="hi-IN">{t('common.hindi')}</option>
          <option value="en-IN">{t('common.english')}</option>
          <option value="auto">Hinglish (Auto)</option>
        </select>
      </div>
      <Button variant="primary" large style={{marginTop: '16px'}} disabled={!selectedScenario}>
        {t('testLab.fireDrill.disclosure.acknowledge')}
      </Button>
    </div>
  );

  const renderBenchmarkTab = () => (
    <div className="card" style={{maxWidth: '900px'}}>
      <h2>{t('testLab.benchmark.title')}</h2>
      <div style={{display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '24px', alignItems: 'flex-end'}}>
        <div className="form__group" style={{flex: 1, minWidth: '200px'}}>
          <label className="form__label">{t('testLab.benchmark.controls.noiseLevel')}</label>
          <input type="range" className="form__input" min="0" max="0.4" step="0.1" value={0} />
        </div>
        <div className="form__group" style={{flex: 1, minWidth: '200px'}}>
          <label className="form__label">{t('testLab.benchmark.controls.sensitivity')}</label>
          <select className="form__input">
            <option value="standard">{t('setup.sections.sensitivityStandard')}</option>
            <option value="high">{t('setup.sections.sensitivityHigh')}</option>
          </select>
        </div>
        <Button variant="primary" large onClick={async () => {}}>
          {t('testLab.benchmark.controls.runButton')}
        </Button>
      </div>

      <div className="summary-strip">
        <div className="summary-strip__item">
          <div className="summary-strip__value">—</div>
          <div className="summary-strip__label">{t('testLab.benchmark.summary.recall')}</div>
        </div>
        <div className="summary-strip__item">
          <div className="summary-strip__value">—</div>
          <div className="summary-strip__label">{t('testLab.benchmark.summary.falseAlarms')}</div>
        </div>
        <div className="summary-strip__item">
          <div className="summary-strip__value">—</div>
          <div className="summary-strip__label">{t('testLab.benchmark.summary.medianTimeToDanger')}</div>
        </div>
        <div className="summary-strip__item">
          <div className="summary-strip__value">—</div>
          <div className="summary-strip__label">{t('testLab.benchmark.summary.cases')}</div>
        </div>
      </div>

      <div className="card" style={{marginTop: '16px'}}>
        <h3>{t('testLab.benchmark.sweepChart.title')}</h3>
        <div style={{height: '300px', background: 'var(--surface-sunk)', border: '1px solid var(--line)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--ink-3)'}}>
          Threshold sweep chart (SVG implementation needed)
        </div>
      </div>

      <div className="card" style={{marginTop: '16px'}}>
        <h3>{t('testLab.benchmark.perTactic.title')}</h3>
        <table className="table">
          <thead>
            <tr>
              <th>{t('testLab.benchmark.perTactic.tactic')}</th>
              <th>{t('testLab.benchmark.perTactic.detected')}</th>
              <th>{t('testLab.benchmark.perTactic.total')}</th>
              <th>{t('testLab.benchmark.perTactic.rate')}</th>
            </tr>
          </thead>
          <tbody>
            <tr><td colspan="4" style={{textAlign: 'center', color: 'var(--ink-3)'}}>Run benchmark to see results</td></tr>
          </tbody>
        </table>
      </div>

      <div style={{display: 'flex', gap: '12px', marginTop: '16px'}}>
        <Button variant="secondary">{t('testLab.benchmark.export.json')}</Button>
        <Button variant="secondary">{t('testLab.benchmark.export.csv')}</Button>
      </div>
    </div>
  );

  return (
    <div>
      <div className="tabs" role="tablist">
        <button
          role="tab"
          aria-selected={activeTab === 'scenarios'}
          className={`tabs__item ${activeTab === 'scenarios' ? 'tabs__item--active' : ''}`}
          onClick={() => setActiveTab('scenarios')}
        >
          {t('testLab.tabs.scenarios')}
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'fireDrill'}
          className={`tabs__item ${activeTab === 'fireDrill' ? 'tabs__item--active' : ''}`}
          onClick={() => setActiveTab('fireDrill')}
        >
          {t('testLab.tabs.fireDrill')}
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'benchmark'}
          className={`tabs__item ${activeTab === 'benchmark' ? 'tabs__item--active' : ''}`}
          onClick={() => setActiveTab('benchmark')}
        >
          {t('testLab.tabs.benchmark')}
        </button>
      </div>

      {activeTab === 'scenarios' && renderScenariosTab()}
      {activeTab === 'fireDrill' && renderFireDrillTab()}
      {activeTab === 'benchmark' && renderBenchmarkTab()}
    </div>
  );
}