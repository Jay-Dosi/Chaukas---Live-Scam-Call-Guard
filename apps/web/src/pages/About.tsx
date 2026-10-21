import { useTranslation } from '@i18n/useTranslation';

export function AboutPage() {
  const { t } = useTranslation();

  const sections = [
    {
      title: t('about.sections.whatItListensFor.title'),
      content: t('about.sections.whatItListensFor.text'),
    },
    {
      title: t('about.sections.tactics.title'),
      list: t('about.sections.tactics.list'),
    },
    {
      title: t('about.sections.limitations.title'),
      list: t('about.sections.limitations.list'),
    },
    {
      title: t('about.sections.howScoringWorks.title'),
      paragraphs: [
        t('about.sections.howScoringWorks.text1'),
        t('about.sections.howScoringWorks.text2'),
      ],
    },
    {
      title: t('about.sections.privacy.title'),
      content: t('about.sections.privacy.text'),
    },
    {
      title: t('about.sections.help.title'),
      content: t('about.sections.help.text'),
    },
  ];

  return (
    <div style={{maxWidth: '800px'}}>
      <h1>{t('about.title')}</h1>
      <p style={{color: 'var(--ink-2)', marginBottom: '32px', fontSize: 'var(--t-lg)'}}>
        {t('liveGuard.disclaimer')}
      </p>

      {sections.map((section, idx) => (
        <div key={idx} style={{marginBottom: '40px'}}>
          <h2 style={{fontSize: 'var(--t-xl)', fontWeight: 600, marginBottom: '16px', paddingBottom: '8px', borderBottom: '2px solid var(--line-strong)'}}>
            {section.title}
          </h2>

          {section.content && (
            <p style={{lineHeight: '1.8', color: 'var(--ink-2)', marginBottom: '16px', fontSize: 'var(--t-md)'}}>
              {section.content}
            </p>
          )}

          {section.paragraphs && section.paragraphs.map((p, i) => (
            <p key={i} style={{lineHeight: '1.8', color: 'var(--ink-2)', marginBottom: '16px', fontSize: 'var(--t-md)'}}>
              {p}
            </p>
          ))}

          {section.list && (
            <ul style={{lineHeight: '1.8', color: 'var(--ink-2)', marginLeft: '24px', fontSize: 'var(--t-md)'}}>
              {section.list.map((item, i) => (
                <li key={i} style={{marginBottom: '12px'}}>
                  {typeof item === 'object' && 'name' in item ? (
                    <>
                      <strong>{item.name}:</strong> {item.desc}
                    </>
                  ) : (
                    item
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}

      <div style={{paddingTop: '24px', borderTop: '2px solid var(--line-strong)', color: 'var(--ink-3)', fontSize: 'var(--t-sm)'}}>
        <p>Chaukas v0.1.0 — Live Scam-Call Guard and Test Lab</p>
        <p>Built for India. Languages: Hindi, English, Hinglish.</p>
      </div>
    </div>
  );
}