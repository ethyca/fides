import { TypedUseSelectorHook, useSelector, useDispatch } from "react-redux";

import type { RootState, AppDispatch } from "./store";

export const useAppDispatch: () => AppDispatch = useDispatch;
// eslint-disable-next-line import/prefer-default-export
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
