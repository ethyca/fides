import { TypedUseSelectorHook, useDispatch, useSelector } from "react-redux";

import type { AppDispatch, RootState } from "./store";

export const useAppDispatch: () => AppDispatch = useDispatch;
// eslint-disable-next-line import/prefer-default-export
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
