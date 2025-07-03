/**
 * External Redux Hooks
 *
 * COPIED & ADAPTED FROM: clients/admin-ui/src/app/hooks.ts
 *
 * Provides typed Redux hooks for the external store
 */

import { TypedUseSelectorHook, useDispatch, useSelector } from "react-redux";

import type { ExternalDispatch, ExternalRootState } from "./store";

export const useExternalAppDispatch = () => useDispatch<ExternalDispatch>();
export const useExternalAppSelector: TypedUseSelectorHook<ExternalRootState> =
  useSelector;
