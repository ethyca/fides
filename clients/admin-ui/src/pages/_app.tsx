import React from 'react';
import type { AppProps } from 'next/app';
import { SessionProvider } from 'next-auth/react';
import { ChakraProvider } from '@chakra-ui/react';
import theme from '../theme';
import { wrapper } from '../app/store';

import '@fontsource/inter/400.css';
import '@fontsource/inter/500.css';
import '@fontsource/inter/700.css';

if (process.env.NEXT_PUBLIC_MOCK_API) {
  // eslint-disable-next-line global-require
  require('../mocks');
}

const MyApp = ({ Component, pageProps }: AppProps) => (
  <SessionProvider>
    <ChakraProvider theme={theme}>
      <Component {...pageProps} />
    </ChakraProvider>
  </SessionProvider>
);

export default wrapper.withRedux(MyApp);
