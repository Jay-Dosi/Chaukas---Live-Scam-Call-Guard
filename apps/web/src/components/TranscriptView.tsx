import React from 'react';
import { useTranslation } from '@i18n/useTranslation';
import type { SignalHit } from '@protocol/index';

interface TranscriptViewProps {
  segments: Array<{ id: string; text: string; isFinal: boolean; tMs: number }>;
  hits: SignalHit[];
  showDetails: boolean;
}

export function TranscriptView({ segments, hits, showDetails }: TranscriptViewProps) {
  const { t } = useTranslation();

  // Build hit map by segment ID
  const hitsBySegment = new Map<string, SignalHit[]>();
  for (const hit of hits) {
    const arr = hitsBySegment.get(hit.segment_id) || [];
    arr.push(hit);
    hitsBySegment.set(hit.segment_id, arr);
  }

  const renderSegment = (seg: { id: string; text: string; isFinal: boolean; tMs: number }) => {
    const segmentHits = hitsBySegment.get(seg.id) || [];
    const text = seg.text;
    let displayText: React.ReactNode = text;

    if (showDetails && segmentHits.length > 0) {
      // Sort hits by span_start
      const sortedHits = [...segmentHits].sort((a, b) => a.span_start - b.span_start);
      let lastEnd = 0;
      const parts: React.ReactNode[] = [];

      for (const hit of sortedHits) {
        if (hit.span_start > lastEnd) {
          parts.push(text.slice(lastEnd, hit.span_start));
        }
        parts.push(
          <span
            key={`${hit.segment_id}-${hit.signal_id}`}
            className={`transcript__highlight transcript__highlight--${hit.context}`}
          >
            {text.slice(hit.span_start, hit.span_end)}
            <span className={`transcript__badge transcript__badge--${hit.context}`}>
              {hit.label_en}
            </span>
          </span>
        );
        lastEnd = hit.span_end;
      }
      if (lastEnd < text.length) {
        parts.push(text.slice(lastEnd));
      }
      displayText = parts;
    }

    const mins = Math.floor(seg.tMs / 60000);
    const secs = Math.floor((seg.tMs % 60000) / 1000).toString().padStart(2, '0');
    const timeStr = `${mins}:${secs}`;

    return (
      <div key={seg.id} className="transcript__segment">
        <div className="transcript__meta">
          <span className="transcript__speaker">{seg.isFinal ? 'CALLER' : '...'}</span>
          <span className="transcript__time">{timeStr}</span>
        </div>
        <div className="transcript__text">
          {displayText}
        </div>
      </div>
    );
  };

  return (
    <div className="transcript" role="log" aria-label={t('liveGuard.transcriptLabel')}>
      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '12px'}}>
        <h3 style={{fontSize: 'var(--t-md)', fontWeight: 600}}>{t('liveGuard.transcriptLabel')}</h3>
      </div>
      {segments.length === 0 ? (
        <p style={{color: 'var(--ink-3)', fontStyle: 'italic'}}>{t('liveGuard.noAudio')}</p>
      ) : (
        segments.map(renderSegment)
      )}
    </div>
  );
}