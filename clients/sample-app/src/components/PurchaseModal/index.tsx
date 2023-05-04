import React, {
  memo, useEffect, useRef, useState,
} from 'react';
import { useForm } from 'react-hook-form';
import { Product, UserData } from '../../types';
import Button from '../Button';
import css from './style.module.scss';
  
interface Props {
  product: Product | null; 
  isOpen: boolean;
  onRequestClose: () => void;
  onSubmit: (data: UserData) => Promise<void>;
}
  
const Modal = ({
  product,
  isOpen,
  onRequestClose,
  onSubmit,
}: Props) => {
  const [fadeClassName, setFadeClassName] = useState('');
  const [isVisible, setIsVisible] = useState(isOpen);
  const ref = useRef<HTMLDivElement | null>(null);
  const { register, handleSubmit, formState: { isValid } } = useForm<UserData>({ mode: 'onChange' });
  
  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
      setFadeClassName(css.fadeIn);
    } else {
      const element = ref.current;
      setFadeClassName(css.fadeOut);
  
      const onAnimationEnd = () => {
        setIsVisible(false);
        element?.removeEventListener('animationend', onAnimationEnd);
      };
  
      element?.addEventListener('animationend', onAnimationEnd);
  
      return () => element?.removeEventListener('animationend', onAnimationEnd);
    }
  
    return () => {};
  }, [isOpen]);
  
  return (
    <div className={`${css.modalWrapper} ${fadeClassName} ${isVisible ? '' : css.displayNone}`} ref={ref}>
      <form
        tabIndex={-1}
        aria-modal="true"
        role="dialog"
        className={css.modal}
        // eslint-disable-next-line @typescript-eslint/no-misused-promises
        onSubmit={handleSubmit(onSubmit)}
      >
       <h2>Submit Your Order</h2>
       <p>All fields required</p>
       <div>
        <input type="text" placeholder='Name*' {...register('name', { required: true })} />
        <input type="text" placeholder='Street*' {...register('street', { required: true })} />
        <input type="text" placeholder='City*' {...register('city', { required: true })} />
        <input type="text" placeholder='State*' {...register('state', { required: true })} />
        <input type="text" placeholder='Zip*' {...register('zip', { required: true })} />
        <input type="email" placeholder='Email*' {...register('email', { required: true })} />
       </div>
       <div className={css.buttons}>
        <Button color="secondary" onClick={onRequestClose}>Cancel</Button>
        <Button color="primary" type="submit" disabled={!isValid}>Purchase</Button>
       </div>
      </form>
    </div>
  );
};
  
export default memo(Modal);
  