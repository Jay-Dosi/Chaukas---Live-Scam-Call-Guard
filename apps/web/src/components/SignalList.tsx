import { useTranslation } from '@i18n/useTranslation';
import type { SignalHit, Combo } from '@protocol/index';

interface SignalListProps {
  hits: SignalHit[];
  combos: Combo[];
}

export function SignalList({ hits, combos }: SignalListProps) {
  const { t } = useTranslation();
  if (hits.length === 0) {
    return <p className="signal-list__empty">{t('liveGuard.noSignals')}</p>;
  }

  return (
    <div className="signal-list__container">
      <table className="table table--compact">
        <thead>
          <tr>
            <th>{t('liveGuard.signalTable.tactic')}</th>
            <th>{t('liveGuard.signalTable.weight')}</th>
            <th>{t('liveGuard.signalTable.context')}</th>
            <th>{t('liveGuard.signalTable.matched')}</th>
          </tr>
        </thead>
        <tbody>
          {hits.map((hit) => (
            <tr key={`${hit.segment_id}-${hit.signal_id}`}>
              <td className="signal-list__signal">{hit.label_en} / {hit.label_hi}</td>
              <td className="signal-list__weight mono">{hit.weight.toFixed(1)}{hit.hard && ' •'}</td>
              <td className={`signal-list__context signal-list__context--${hit.context}`}>{hit.context}</td>
              <td className="signal-list__matched mono">"{hit.matched}"</td>
            </tr>
          ))}
        </tbody>
      </table>

      {combos.length > 0 && (
        <div className="signal-list__combos">
          <h3 className="signal-list__combo-title">{t('liveGuard.activeCombinations')}</h3>
          <table className="table table--compact">
            <thead>
              <tr>
                <th>{t('liveGuard.signalTable.comboId')}</th>
                <th>{t('liveGuard.signalTable.bonus')}</th>
              </tr>
            </thead>
            <tbody>
              {combos.map((combo) => (
                <tr key={combo.id}>
                  <td className="mono">{combo.id}</td>
                  <td className="signal-list__weight mono">+{combo.bonus}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}