import { TypedUseSelectorHook, useSelector } from 'react-redux';

import type { RootState } from './store';

// eslint-disable-next-line import/prefer-default-export
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
