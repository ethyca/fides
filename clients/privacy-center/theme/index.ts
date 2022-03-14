import { extendTheme } from '@fidesui/react';

const theme = extendTheme({
  styles: {
    global: {
      body: {
        bg: 'gray.50',
      },
    },
  },
  shadows: {
    'complimentary-2xl':
      '0 0 0 1px #C1A7F9, 0px 25px 50px -12px rgba(0, 0, 0, 0.25)',
  },
});

export default theme;
