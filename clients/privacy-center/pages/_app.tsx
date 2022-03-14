import type { AppProps } from 'next/app';
import { SessionProvider } from 'next-auth/react';
import { FidesProvider } from '@fidesui/react';

import '@fontsource/inter/700.css';
import '@fontsource/inter/600.css';
import '@fontsource/inter/500.css';
import '@fontsource/inter/400.css';

import '../config/config.css';

import theme from '../theme';

const MyApp = ({ Component, pageProps }: AppProps) => (
  <SessionProvider>
    <FidesProvider theme={theme}>
      <Component {...pageProps} />
    </FidesProvider>
  </SessionProvider>
);

export default MyApp;
