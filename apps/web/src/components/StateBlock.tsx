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

const SEGMENTS = 8;

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

  const filledSegments = Math.round((score / 100) * SEGMENTS);
  const reasonText = reason || t(`liveGuard.reason.${level}`);

  return (
    <div
      className={`state-block state-block--${level}`}
      role="region"
      aria-live={level === 'danger' || level === 'critical' ? 'assertive' : 'polite'}
    >
      {/* Risk state word — hero size, always visible */}
      <div className="state-block__header">
        <h2 className="state-block__level">{levelLabels[level]}</h2>
        <div className="state-block__meta">
          <span className="mono">{score}/100</span>
          <span className="mono">{duration}</span>
        </div>
      </div>

      {/* Segmented risk bar — flat, no gauge */}
      <div
        className="risk-bar"
        role="progressbar"
        aria-valuenow={score}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={t('liveGuard.riskLabel')}
      >
        {Array.from({ length: SEGMENTS }, (_, i) => (
          <div
            key={i}
            className={`risk-bar__segment${i < filledSegments ? ' risk-bar__segment--filled' : ''}`}
          />
        ))}
      </div>

      {/* Reason text — concrete, not marketing */}
      <p className="state-block__reason">{reasonText}</p>

      {/* Actions — min 56px touch targets for older adults */}
      <div className="state-block__actions">
        {isListening && (
          <button className="btn btn--secondary btn--lg" onClick={onStop}>
            {t('liveGuard.stopButton')}
          </button>
        )}
        {(level === 'danger' || level === 'critical') && (
          <>
            <button className="btn btn--danger btn--lg" onClick={onCall1930}>
              {t('liveGuard.sessionSummary.call1930')}
            </button>
            <button className="btn btn--danger btn--lg" onClick={onAlertFamily}>
              {t('liveGuard.sessionSummary.alertFamily')}
            </button>
          </>
        )}
      </div>

      {/* Details toggle — checkbox, not a pill */}
      <div className="state-block__details-toggle">
        <label>
          <input type="checkbox" checked={showDetails} onChange={onToggleDetails} />
          <span>{showDetails ? t('liveGuard.hideDetails') : t('liveGuard.showDetails')}</span>
        </label>
      </div>
    </div>
  );
}