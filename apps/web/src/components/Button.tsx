import type { ButtonHTMLAttributes, ForwardedRef } from 'react';
import { forwardRef } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  /** Primary action buttons must be at least 56px per PRD */
  large?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', variant = 'primary', large = false, children, ...rest }, ref) => {
    const classes = [
      'btn',
      variant === 'primary' && 'btn-primary',
      variant === 'secondary' && 'btn-secondary',
      variant === 'danger' && 'btn-danger',
      variant === 'ghost' && 'btn-ghost',
      large ? '' : 'min-height-[48px]',
      className,
    ].filter(Boolean).join(' ');

    return (
      <button ref={ref} className={classes} {...rest}>
        {children}
      </button>
    );
  },
);

Button.displayName = 'Button';