import type { SignalHit, Combo } from '@protocol/index';

interface SignalListProps {
  hits: SignalHit[];
  combos: Combo[];
}

export function SignalList({ hits, combos }: SignalListProps) {
  if (hits.length === 0) {
    return <p style={{color: 'var(--ink-3)', fontStyle: 'italic', padding: '16px'}}>No signals detected</p>;
  }

  return (
    <div style={{overflowX: 'auto'}}>
      <table className="signal-list">
        <thead>
          <tr>
            <th>Tactic</th>
            <th>Weight</th>
            <th>Context</th>
            <th>Matched Phrase</th>
          </tr>
        </thead>
        <tbody>
          {hits.map((hit, idx) => (
            <tr key={`${hit.segment_id}-${hit.signal_id}-${idx}`}>
              <td className="signal-list__signal">
                {hit.label_en} / {hit.label_hi}
              </td>
              <td className="signal-list__weight">
                {hit.weight.toFixed(1)} {hit.hard && '⬤'}
              </td>
              <td className={`signal-list__context signal-list__context--${hit.context}`}>
                {hit.context}
              </td>
              <td className="signal-list__matched">"{hit.matched}"</td>
            </tr>
          ))}
        </tbody>
      </table>

      {combos.length > 0 && (
        <div style={{marginTop: '16px'}}>
          <h4 style={{fontSize: 'var(--t-sm)', fontWeight: 600, marginBottom: '8px', borderBottom: '2px solid var(--line-strong)', paddingBottom: '4px'}}>
            Active Combinations
          </h4>
          <table className="signal-list">
            <thead>
              <tr>
                <th>Combo ID</th>
                <th>Bonus</th>
              </tr>
            </thead>
            <tbody>
              {combos.map((combo) => (
                <tr key={combo.id}>
                  <td>{combo.id}</td>
                  <td className="signal-list__weight">+{combo.bonus}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}