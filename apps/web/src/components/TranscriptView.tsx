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
            <span className="transcript__badge">
              {hit.context === 'asserted' ? hit.label_en : hit.label_hi}
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
        <div className="transcript__time mono">{timeStr}</div>
        <div className="transcript__content">
          <span className="transcript__speaker">{seg.isFinal ? 'CALLER' : '...'}</span>
          <div className="transcript__text">{displayText}</div>
        </div>
      </div>
    );
  };

  return (
    <div className="transcript" role="log" aria-label={t('liveGuard.transcriptLabel')}>
      <div className="transcript__header">
        <h3 className="transcript__title">{t('liveGuard.transcriptLabel')}</h3>
      </div>
      {segments.length === 0 ? (
        <p className="transcript__empty">{t('liveGuard.noAudio')}</p>
      ) : (
        segments.map(renderSegment)
      )}
    </div>
  );
}