import { useCallback, useEffect, useRef, useState } from 'react';
import css from './style.module.scss';

interface Props {
  trigger: number;
}

const Popup = ({
  trigger,
}: Props) => {
  const [className, setClassName] = useState('');
  const timeoutRef = useRef<NodeJS.Timeout>();

  const onClickClose = useCallback(() => {
    clearTimeout(timeoutRef.current);
    setClassName(css.bounceUp);
  }, []);

  useEffect(() => {
    clearTimeout(timeoutRef.current);
    if (trigger > 0) {
      setClassName(css.bounceInDown);

      timeoutRef.current = setTimeout(() => {
        setClassName(css.bounceUp);
      }, 20000);
    }
  }, [trigger]);

  return (
    <div className={css.popup + ' ' + className}>
        <svg className={css.checkmark} width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8.99996 17.3333C4.39746 17.3333 0.666626 13.6025 0.666626 8.99999C0.666626 4.39749 4.39746 0.666656 8.99996 0.666656C13.6025 0.666656 17.3333 4.39749 17.3333 8.99999C17.3333 13.6025 13.6025 17.3333 8.99996 17.3333ZM8.16913 12.3333L14.0608 6.44082L12.8825 5.26249L8.16913 9.97666L5.81163 7.61916L4.63329 8.79749L8.16913 12.3333Z" fill="white"/>
        </svg>

        <svg className={css.close} onClick={onClickClose} width="10" height="10" viewBox="0 0 10 10" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4.99999 4.05732L8.29999 0.757324L9.24266 1.69999L5.94266 4.99999L9.24266 8.29999L8.29999 9.24266L4.99999 5.94266L1.69999 9.24266L0.757324 8.29999L4.05732 4.99999L0.757324 1.69999L1.69999 0.757324L4.99999 4.05732Z" fill="white"/>
        </svg>

        Thanks for shopping with us. Enjoy your cookies!
    </div>
  );
};

export default Popup;