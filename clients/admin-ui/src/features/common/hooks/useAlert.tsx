import {
  Alert,
  AlertDescription,
  AlertIcon,
  AlertTitle,
  Box,
  CloseButton,
  useToast,
  UseToastOptions,
} from "@fidesui/react";

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
    options?: UseToastOptions
  ) => {
    toast({
      ...options,
      position: options?.position || DEFAULT_POSITION,
      render: ({ onClose }) => (
        <Alert alignItems="normal" status="error">
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
    });
  };

  /**
   * Display custom success toast notification
   * @param description
   */
  const successAlert = (
    description: string,
    title?: string,
    options?: UseToastOptions
  ) => {
    toast({
      ...options,
      position: options?.position || DEFAULT_POSITION,
      render: ({ onClose }) => (
        <Alert alignItems="normal" status="success" variant="subtle">
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
    });
  };

  return { errorAlert, successAlert };
};
