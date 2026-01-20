/**
 * Redux Middleware for RTK Query Error Logging
 *
 * This middleware intercepts rejected RTK Query actions and handles error
 * notifications based on the `error_notification_mode` application config.
 *
 * Modes:
 * - "console_only": Logs errors to browser console (default)
 * - "toast": Shows EnhancedErrorToast with details + logs to console
 *
 * Configuration:
 * Set via environment variable: FIDES__ADMIN_UI__ERROR_NOTIFICATION_MODE=toast
 */

import { isRejectedWithValue, Middleware } from "@reduxjs/toolkit";
import { createChakraStandaloneToast as createStandaloneToast } from "fidesui";

import EnhancedErrorToast from "~/features/common/errors/EnhancedErrorToast";
import { parseRTKErrorAction } from "~/features/common/helpers";
import { DEFAULT_TOAST_PARAMS } from "~/features/common/toast";
import { selectApplicationConfig } from "~/features/config-settings/config-settings.slice";
import { errorSlice } from "~/features/error/error.slice";
import { ErrorNotificationMode } from "~/types/api";

/**
 * Logs Redux errors to the browser console.
 */
const printReduxError = (action: unknown) =>
  // eslint-disable-next-line no-console
  console.error("Admin UI encountered the following error: ", action);

const { toast } = createStandaloneToast({
  defaultOptions: DEFAULT_TOAST_PARAMS,
});

/**
 * Shows an enhanced error toast with parsed error details.
 * Uses toast ID for deduplication - same endpoint errors update existing toast.
 */
const showEnhancedErrorToast = (action: unknown) => {
  const errorProps = parseRTKErrorAction(action);

  // Use endpoint as toast ID to prevent spam from repeated failures
  const toastId = `error-${errorProps.endpoint}`;

  toast({
    id: toastId,
    status: "error",
    duration: null, // User must dismiss manually. After we have it on storage, lets give it 5 secs
    isClosable: true,
    render: ({ onClose }) =>
      EnhancedErrorToast({
        status: errorProps.status,
        message: errorProps.message,
        endpoint: errorProps.endpoint,
        rawData: errorProps.rawData,
        onClose,
      }),
  });

  // Still log to console for DevTools debugging
  printReduxError(action);
};

/**
 * Error handling functions mapped by notification mode.
 */
const errorLoggingFunctions: Record<
  ErrorNotificationMode,
  (action: unknown) => void
> = {
  console_only: printReduxError,
  toast: showEnhancedErrorToast,
};

/**
 * RTK Query error logging middleware.
 *
 * Intercepts rejected RTK Query actions and:
 * 1. Stores error in Redux for history (BOTH modes)
 * 2. Routes to appropriate handler based on error_notification_mode config
 */
export const rtkQueryErrorLogger: Middleware =
  (store) => (next) => (action) => {
    if (isRejectedWithValue(action)) {
      // Parse the error action to extract useful info
      const errorProps = parseRTKErrorAction(action);

      // Store error in Redux history (works for BOTH modes)
      store.dispatch(
        errorSlice.actions.addError({
          status: errorProps.status,
          message: errorProps.message,
          endpoint: errorProps.endpoint,
          rawData: errorProps.rawData,
        }),
      );

      // Get notification mode from config
      const applicationState = selectApplicationConfig({ api_set: false })(
        store.getState(),
      );
      const loggingMode =
        applicationState?.admin_ui?.error_notification_mode ??
        ErrorNotificationMode.CONSOLE_ONLY;

      // Handle based on mode (toast or console)
      errorLoggingFunctions[loggingMode](action);
    }
    next(action);
  };
