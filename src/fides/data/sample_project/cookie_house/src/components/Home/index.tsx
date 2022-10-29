import Image from 'next/image';
import { useCallback, useState } from 'react';
import { Product, UserData } from '../../types';
import Button from '../Button';
import Popup from '../Popup';
import PurchaseModal from '../PurchaseModal';
import css from './style.module.scss';

interface Props {
  products: Product[];
}

const Home = ({ products }: Props) => {
  const [productInPurchase, setProductInPurchase] = useState<Product | null>(null);
  const [popupTrigger, setPopupTrigger] = useState(0);
  const onCloseModal = useCallback(() => {
    setProductInPurchase(null);
  }, []);

  const onSubmit = useCallback(async (data: UserData) => {
    await (await fetch('/api/purchase', {
      method: 'POST',
      body: JSON.stringify(data),
      headers: new Headers({
        'Content-Type': 'application/json',
        Accept: 'application/json',
      }),
    })).json();

    setPopupTrigger(v => v + 1);

    setProductInPurchase(null);
  }, []);

  return (
    <>
        <header className={css.header}>
            <Image src="/logo.svg" width={204} height={68} alt="Logo" />
        </header>
        <main>
            <div className={css.products}>
            {products.map((product) => (
                <div key={product.id} className={css.product}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={product.url} alt={product.name ?? 'Cookie'} />
                    <div className={css.name}>{product.name}</div>
                    <div className={css.description}>{product.description}</div>
                    <div className={css.price}>{product.price}</div>
                    <Button color="primary" 
                      className={css.purchase} 
                      onClick={() => setProductInPurchase(product)}
                    >
                      Purchase
                    </Button>
                </div>
            ))}
            </div>
        </main>
        <footer className={css.footer}>Do not sell my personal Information</footer>
        <PurchaseModal 
          isOpen={!!productInPurchase} 
          onRequestClose={onCloseModal} 
          onSubmit={onSubmit}
          product={productInPurchase} 
        />
        <Popup trigger={popupTrigger} />
    </>
  );
};

export default Home;