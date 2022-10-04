import {
  Alert,
  AlertDescription,
  AlertIcon,
  Box,
  useToast,
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
  const errorAlert = (description: string | JSX.Element) => {
    toast({
      isClosable: true,
      position: DEFAULT_POSITION,
      render: () => (
        <Alert status="error">
          <AlertIcon />
          <Box>
            <AlertDescription>{description}</AlertDescription>
          </Box>
        </Alert>
      ),
    });
  };

  /**
   * Display custom success toast notification
   * @param description
   */
  const successAlert = (description: string) => {
    toast({
      isClosable: true,
      position: DEFAULT_POSITION,
      render: () => (
        <Alert status="success" variant="subtle">
          <AlertIcon />
          {description}
        </Alert>
      ),
    });
  };

  return { errorAlert, successAlert };
};
