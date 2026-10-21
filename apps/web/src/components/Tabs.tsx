import { forwardRef } from 'react';

export interface TabsProps {
  children: React.ReactNode;
  activeTab: string;
  onChange: (tab: string) => void;
  className?: string;
}

export function Tabs({ children, activeTab, onChange, className = '' }: TabsProps) {
  return (
    <div className={`tabs ${className}`} role="tablist">
      {React.Children.map(children, (child) => {
        if (!React.isValidElement(child)) return null;
        return React.cloneElement(child, {
          isActive: child.props.id === activeTab,
          onClick: () => onChange(child.props.id),
        });
      })}
    </div>
  );
}

export interface TabProps {
  id: string;
  children: React.ReactNode;
  isActive?: boolean;
  onClick?: () => void;
  className?: string;
}

export const Tab = forwardRef<HTMLButtonElement, TabProps>(
  ({ id, children, isActive = false, onClick, className = '' }, ref) => (
    <button
      ref={ref}
      role="tab"
      aria-selected={isActive}
      id={`tab-${id}`}
      className={`tabs__item ${isActive ? 'tabs__item--active' : ''} ${className}`}
      onClick={onClick}
    >
      {children}
    </button>
  )
);
Tab.displayName = 'Tab';

export interface TabPanelProps {
  id: string;
  children: React.ReactNode;
  className?: string;
}

export function TabPanel({ id, children, className = '' }: TabPanelProps) {
  return (
    <div role="tabpanel" id={`panel-${id}`} className={className}>
      {children}
    </div>
  );
}