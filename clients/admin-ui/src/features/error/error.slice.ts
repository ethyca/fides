/**
 * Error History Slice
 *
 * Stores the last N API errors for debugging purposes.
 * FDEs can access this history to diagnose issues that occurred before
 * they connected to a customer's machine.
 */

import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";

/**
 * Maximum number of errors to store in history.
 * Older errors are removed when this limit is exceeded.
 */
const MAX_ERROR_ENTRIES = 10;

/**
 * Maximum characters for rawData storage.
 * Large payloads are truncated to prevent memory issues.
 */
const MAX_RAW_DATA_LENGTH = 5000;

/**
 * Represents a single error entry in the history.
 */
export interface ErrorLogEntry {
  /** Unique identifier for this error entry */
  id: string;
  /** Unix timestamp when the error occurred */
  timestamp: number;
  /** HTTP status code or error type (e.g., 404, 500, "PARSING_ERROR") */
  status: number | string | undefined;
  /** Human-readable error message */
  message: string;
  /** The API endpoint that failed */
  endpoint: string;
  /** Full JSON payload for debugging */
  rawData: string;
}

/**
 * Payload for adding a new error (id and timestamp are auto-generated).
 */
export type AddErrorPayload = Omit<ErrorLogEntry, "id" | "timestamp">;

interface ErrorState {
  errors: ErrorLogEntry[];
}

const initialState: ErrorState = {
  errors: [],
};

export const errorSlice = createSlice({
  name: "error",
  initialState,
  reducers: {
    /**
     * Adds a new error to the history.
     * Maintains FIFO order with newest entries first.
     * Automatically removes oldest entries when MAX_ERROR_ENTRIES is exceeded.
     */
    addError(state, { payload }: PayloadAction<AddErrorPayload>) {
      // Truncate rawData if too large to prevent memory issues
      const truncatedRawData =
        payload.rawData && payload.rawData.length > MAX_RAW_DATA_LENGTH
          ? `${payload.rawData.substring(0, MAX_RAW_DATA_LENGTH)}\n\n[truncated - ${payload.rawData.length} chars total]`
          : (payload.rawData ?? "");

      const newEntry: ErrorLogEntry = {
        id: `error-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
        timestamp: Date.now(),
        ...payload,
        rawData: truncatedRawData,
      };

      // Add to beginning (newest first)
      state.errors.unshift(newEntry);

      // Remove oldest entries if over limit
      if (state.errors.length > MAX_ERROR_ENTRIES) {
        state.errors = state.errors.slice(0, MAX_ERROR_ENTRIES);
      }
    },

    /**
     * Clears all errors from history.
     */
    clearErrors(state) {
      state.errors = [];
    },
  },
});

// Export actions
export const { addError, clearErrors } = errorSlice.actions;

// Selectors
export const selectErrorState = (state: RootState) => state.error;

export const selectErrors = createSelector(
  [selectErrorState],
  (errorState) => errorState?.errors ?? [],
);

export const selectErrorCount = createSelector(
  [selectErrors],
  (errors) => errors.length,
);

export const { reducer } = errorSlice;
