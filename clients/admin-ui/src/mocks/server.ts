import { setupServer } from 'msw/node';

import { handlers } from './handlers';

// eslint-disable-next-line import/prefer-default-export
export const server = setupServer(...handlers);
