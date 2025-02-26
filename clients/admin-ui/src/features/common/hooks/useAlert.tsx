import {
  Alert,
  AlertDescription,
  AlertIcon,
  AlertTitle,
  Box,
  CloseButton,
  useToast,
  UseToastOptions,
} from "fidesui";
import { MouseEventHandler } from "react";

/**
 * Custom hook for toast notifications
 * @returns
 */
export const useAlert = () => {
  const toast = useToast();
  const DEFAULT_POSITION = "top";

  /**
   * Display custom error toast notification
   * @param description
   */
  const errorAlert = (
    description: string | JSX.Element,
    title?: string,
    addedOptions?: UseToastOptions,
  ) => {
    const options = {
      ...addedOptions,
      position: addedOptions?.position || DEFAULT_POSITION,
      render: ({
        onClose,
      }: {
        onClose: MouseEventHandler<HTMLButtonElement> | undefined;
      }) => (
        <Alert alignItems="normal" status="error" data-testid="error-alert">
          <AlertIcon />
          <Box>
            {title && <AlertTitle>{title}</AlertTitle>}
            <AlertDescription>{description}</AlertDescription>
          </Box>
          <CloseButton
            onClick={onClose}
            position="relative"
            right={0}
            size="sm"
            top={-1}
          />
        </Alert>
      ),
    };

    if (addedOptions?.id && toast.isActive(addedOptions.id)) {
      toast.update(addedOptions.id, options);
    } else {
      toast(options);
    }
  };

  /**
   * Display custom success toast notification
   * @param description
   */
  const successAlert = (
    description: string,
    title?: string,
    addedOptions?: UseToastOptions,
  ) => {
    const options = {
      ...addedOptions,
      position: addedOptions?.position || DEFAULT_POSITION,
      render: ({
        onClose,
      }: {
        onClose: MouseEventHandler<HTMLButtonElement> | undefined;
      }) => (
        <Alert
          alignItems="normal"
          status="success"
          variant="subtle"
          data-testid="success-alert"
        >
          <AlertIcon />
          <Box>
            {title && <AlertTitle>{title}</AlertTitle>}
            <AlertDescription>{description}</AlertDescription>
          </Box>
          <CloseButton
            onClick={onClose}
            position="relative"
            right={0}
            size="sm"
            top={-1}
          />
        </Alert>
      ),
    };
    if (addedOptions?.id && toast.isActive(addedOptions.id)) {
      toast.update(addedOptions.id, options);
    } else {
      toast(options);
    }
  };

  return { errorAlert, successAlert };
};
