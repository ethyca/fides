import { setupWorker } from 'msw';

import { handlers } from './handlers';

// eslint-disable-next-line import/prefer-default-export
export const worker = setupWorker(...handlers);
