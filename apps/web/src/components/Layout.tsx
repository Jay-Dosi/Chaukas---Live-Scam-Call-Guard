import { NavLink, Outlet } from 'react-router-dom';
import { Layout as LayoutIcon, Mic, Settings, Info } from 'lucide-react';
import { useTranslation } from '@i18n/useTranslation';

export function Layout({ children }: { children?: React.ReactNode }) {
  const { t, lang } = useTranslation();

  const navItems = [
    { path: '/', label: t('nav.liveGuard'), icon: Mic },
    { path: '/test', label: t('nav.testLab'), icon: LayoutIcon },
    { path: '/setup', label: t('nav.setup'), icon: Settings },
    { path: '/about', label: t('nav.about'), icon: Info },
  ];

  return (
    <div className="layout" lang={lang}>
      <a href="#main" className="skip-link">
        {t('a11y.skipToMain')}
      </a>

      <header className="layout__header" role="banner">
        <h1 className="layout__title">Chaukas</h1>

        <nav className="layout__nav" aria-label={t('a11y.mainNavigation')}>
          {navItems.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              className={({ isActive }) =>
                `layout__nav-item${isActive ? ' layout__nav-item--active' : ''}`
              }
            >
              <Icon size={20} strokeWidth={1.5} aria-hidden="true" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
      </header>

      <main id="main" className="layout__main" role="main">
        {children || <Outlet />}
      </main>

      <nav className="bottom-bar" aria-label={t('a11y.mainNavigation')} role="navigation">
        {navItems.map(({ path, label, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `bottom-bar__item${isActive ? ' bottom-bar__item--active' : ''}`
            }
          >
            <Icon size={20} strokeWidth={1.5} aria-hidden="true" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}