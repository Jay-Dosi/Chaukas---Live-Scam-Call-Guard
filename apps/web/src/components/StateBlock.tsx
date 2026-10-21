import { useTranslation } from '@i18n/useTranslation';
import type { Level } from '@protocol/index';

interface StateBlockProps {
  level: Level;
  score: number;
  reason: string;
  duration: string;
  onStop: () => void;
  onCall1930: () => void;
  onAlertFamily: () => void;
  showDetails: boolean;
  onToggleDetails: () => void;
  isListening: boolean;
}

export function StateBlock({
  level,
  score,
  reason,
  duration,
  onStop,
  onCall1930,
  onAlertFamily,
  showDetails,
  onToggleDetails,
  isListening,
}: StateBlockProps) {
  const { t } = useTranslation();

  const levelLabels: Record<Level, string> = {
    calm: t('liveGuard.state.calm'),
    caution: t('liveGuard.state.caution'),
    danger: t('liveGuard.state.danger'),
    critical: t('liveGuard.state.critical'),
  };

  const reasonText = reason || t(`liveGuard.reason.${level}`);

  return (
    <div className={`state-block state-block--${level}`} role="region" aria-live={level === 'danger' || level === 'critical' ? 'assertive' : 'polite'}>
      <div className="state-block__header">
        <h2 className="state-block__level">{levelLabels[level]}</h2>
        <div className="state-block__meta">
          <span>{t('liveGuard.riskLabel')} {score} / 100</span>
          <span>{duration}</span>
        </div>
      </div>

      <div className="meter" role="progressbar" aria-valuenow={score} aria-valuemin={0} aria-valuemax={100} aria-label={t('liveGuard.riskLabel')}>
        {[0,1,2,3,4,5,6,7].map((i) => (
          <div key={i} className={`meter__segment ${i < Math.ceil(score / 12.5) ? 'meter__segment--filled' : ''}`} />
        ))}
        <div className="meter__labels">
          <span>0</span>
          <span>100</span>
        </div>
      </div>

      <p className="state-block__reason">{reasonText}</p>

      <div className="action-bar" style={{display: 'flex', gap: '12px', marginTop: '16px', flexWrap: 'wrap'}}>
        {isListening && (
          <button className="btn btn-secondary" onClick={onStop} style={{minHeight: '56px', flex: '1', minWidth: '140px'}}>
            {t('liveGuard.stopButton')}
          </button>
        )}
        {(level === 'danger' || level === 'critical') && (
          <>
            <button className="btn btn-danger" onClick={onCall1930} style={{minHeight: '56px', flex: '1', minWidth: '140px'}}>
              {t('liveGuard.sessionSummary.call1930')}
            </button>
            <button className="btn btn-danger" onClick={onAlertFamily} style={{minHeight: '56px', flex: '1', minWidth: '140px'}}>
              {t('liveGuard.sessionSummary.alertFamily')}
            </button>
          </>
        )}
      </div>

      <div style={{marginTop: '16px'}}>
        <label style={{display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer'}}>
          <input
            type="checkbox"
            checked={showDetails}
            onChange={onToggleDetails}
            style={{width: '18px', height: '18px', accentColor: 'var(--action)'}}
          />
          <span>{showDetails ? t('liveGuard.hideDetails') : t('liveGuard.showDetails')}</span>
        </label>
      </div>
    </div>
  );
}