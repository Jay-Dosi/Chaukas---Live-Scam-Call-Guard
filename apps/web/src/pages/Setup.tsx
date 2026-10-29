import { useState } from 'react';
import { useTranslation } from '@i18n/useTranslation';
import { useSettingsStore, deleteAllData } from '@state/settings';
import { Button } from '@components/Button';

export function SetupPage() {
  const { t } = useTranslation();
  const {
    uiLanguage,
    callLanguage,
    familyContactName,
    familyContactNumber,
    alertSensitivity,
    textSize,
    voiceAlerts,
    detailsViewDefault,
    setUiLanguage,
    setCallLanguage,
    setFamilyContactName,
    setFamilyContactNumber,
    setAlertSensitivity,
    setTextSize,
    setVoiceAlerts,
    setDetailsViewDefault,
  } = useSettingsStore();

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [testPlaying, setTestPlaying] = useState(false);

  const handleTestSetup = async () => {
    setTestPlaying(true);
    // Play a test sound
    const audioCtx = new AudioContext();
    const oscillator = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    oscillator.connect(gain);
    gain.connect(audioCtx.destination);
    oscillator.type = 'sine';
    oscillator.frequency.value = 800;
    gain.gain.value = 0.3;
    oscillator.start();
    setTimeout(() => {
      oscillator.stop();
      audioCtx.close();
      setTestPlaying(false);
    }, 500);
  };

  return (
    <div className="form" style={{maxWidth: '700px'}}>
      <h1>{t('setup.title')}</h1>

      <div className="form__group">
        <label className="form__label">{t('setup.sections.uiLanguage')}</label>
        <select className="form__input" value={uiLanguage} onChange={(e) => setUiLanguage(e.target.value as 'en' | 'hi')}>
          <option value="en">{t('common.english')}</option>
          <option value="hi">{t('common.hindi')}</option>
        </select>
      </div>

      <div className="form__group">
        <label className="form__label">{t('setup.sections.callLanguage')}</label>
        <select className="form__input" value={callLanguage} onChange={(e) => setCallLanguage(e.target.value as 'en-IN' | 'hi-IN' | 'auto')}>
          <option value="auto">Auto / Hinglish</option>
          <option value="en-IN">{t('common.english')} (India)</option>
          <option value="hi-IN">{t('common.hindi')} (India)</option>
        </select>
      </div>

      <div className="form__group">
        <label className="form__label">{t('setup.sections.familyContact')}</label>
        <div style={{display: 'grid', gap: '12px'}}>
          <div>
            <label className="form__label">{t('setup.sections.contactName')}</label>
            <input className="form__input" type="text" value={familyContactName} onChange={(e) => setFamilyContactName(e.target.value)} placeholder={t('setup.sections.contactName')} />
          </div>
          <div>
            <label className="form__label">{t('setup.sections.contactNumber')}</label>
            <input className="form__input" type="tel" value={familyContactNumber} onChange={(e) => setFamilyContactNumber(e.target.value)} placeholder={t('setup.sections.contactNumber')} />
          </div>
        </div>
      </div>

      <div className="form__group">
        <label className="form__label">{t('setup.sections.alertSensitivity')}</label>
        <select className="form__input" value={alertSensitivity} onChange={(e) => setAlertSensitivity(e.target.value as 'standard' | 'high')}>
          <option value="standard">{t('setup.sections.sensitivityStandard')}</option>
          <option value="high">{t('setup.sections.sensitivityHigh')}</option>
        </select>
      </div>

      <div className="form__group">
        <label className="form__label">{t('setup.sections.textSize')}</label>
        <select className="form__input" value={textSize} onChange={(e) => setTextSize(e.target.value as 'normal' | 'large' | 'extra-large')}>
          <option value="normal">{t('setup.sections.textSizeNormal')}</option>
          <option value="large">{t('setup.sections.textSizeLarge')}</option>
          <option value="extra-large">{t('setup.sections.textSizeExtraLarge')}</option>
        </select>
      </div>

      <div className="form__group" style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
        <input type="checkbox" id="voiceAlerts" checked={voiceAlerts} onChange={(e) => setVoiceAlerts(e.target.checked)} style={{width: '20px', height: '20px', accentColor: 'var(--action)'}} />
        <label htmlFor="voiceAlerts" style={{fontSize: 'var(--t-md)', fontWeight: 500, cursor: 'pointer'}}>{t('setup.sections.voiceAlerts')}</label>
      </div>

      <div className="form__group" style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
        <input type="checkbox" id="detailsView" checked={detailsViewDefault} onChange={(e) => setDetailsViewDefault(e.target.checked)} style={{width: '20px', height: '20px', accentColor: 'var(--action)'}} />
        <label htmlFor="detailsView" style={{fontSize: 'var(--t-md)', fontWeight: 500, cursor: 'pointer'}}>{t('setup.sections.detailsView')}</label>
      </div>

      <div className="divider" style={{margin: '24px 0'}} />

      <Button variant="secondary" onClick={handleTestSetup} disabled={testPlaying} style={{width: '100%'}}>
        {testPlaying ? t('setup.testPlaying') : t('setup.testSetup')}
      </Button>

      <div className="divider" style={{margin: '24px 0'}} />

      <Button variant="danger" onClick={() => setShowDeleteConfirm(true)} style={{width: '100%'}}>
        {t('setup.deleteAllData')}
      </Button>

      <p style={{marginTop: '16px', color: 'var(--ink-3)', fontSize: 'var(--t-sm)', textAlign: 'center'}}>
        {t('setup.disclaimer')}
      </p>

      {showDeleteConfirm && (
        <div style={{position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100}}>
          <div className="card" style={{maxWidth: '400px', width: '90%'}}>
            <h3>{t('setup.deleteConfirm')}</h3>
            <div style={{display: 'flex', gap: '12px', marginTop: '16px', justifyContent: 'flex-end'}}>
              <Button variant="secondary" onClick={() => setShowDeleteConfirm(false)}>{t('common.cancel')}</Button>
              <Button variant="danger" onClick={() => { deleteAllData(); setShowDeleteConfirm(false); }}>{t('common.confirm')}</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}