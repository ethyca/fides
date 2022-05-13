import { TypedUseSelectorHook, useSelector } from 'react-redux';

import type { AppState } from './store';

// eslint-disable-next-line import/prefer-default-export
export const useAppSelector: TypedUseSelectorHook<AppState> = useSelector;
