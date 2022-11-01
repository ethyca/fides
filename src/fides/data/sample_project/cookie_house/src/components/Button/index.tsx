import { ReactNode } from 'react';

import css from './style.module.scss';

interface Props {
  children: ReactNode;
  color: 'primary' | 'secondary';
  className?: string;
  type?: 'button' | 'submit';
  disabled?: boolean;
  onClick?: () => void;
}
const Button = ({
  children,
  color,
  className,
  type = 'button',
  disabled,
  onClick,
}: Props) => (
    <button 
        type={type}
        onClick={onClick}
        className={css.button + ' ' + css[color] + ' ' + (className ?? '')}
        disabled={disabled}
    >
        {children}
    </button>
);

export default Button;