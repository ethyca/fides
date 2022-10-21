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
        <Alert status="error">
          <AlertIcon />
          <Box>
            {title && <AlertTitle>{title}</AlertTitle>}
            <AlertDescription>{description}</AlertDescription>
          </Box>
          <CloseButton
            alignSelf="flex-start"
            onClick={onClose}
            position="relative"
            right={-1}
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
        <Alert status="success" variant="subtle">
          <AlertIcon />
          <Box>
            {title && <AlertTitle>{title}</AlertTitle>}
            <AlertDescription>{description}</AlertDescription>
          </Box>
          <CloseButton
            alignSelf="flex-start"
            onClick={onClose}
            position="relative"
            right={-1}
            size="sm"
            top={-1}
          />
        </Alert>
      ),
    });
  };

  return { errorAlert, successAlert };
};
