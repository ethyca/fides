import {
  Alert,
  AlertDescription,
  AlertIcon,
  AlertTitle,
  Box,
  CloseButton,
  useToast,
} from "@fidesui/react";
import { CSSProperties } from "react";
import { v4 as uuid } from "uuid";

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
    id: string = uuid(),
    title?: string,
    duration?: number | null | undefined,
    containerStyle?: CSSProperties
  ) => {
    if (toast.isActive(id)) {
      return;
    }
    toast({
      id,
      containerStyle,
      duration,
      position: DEFAULT_POSITION,
      render: () => (
        <Alert status="error">
          <AlertIcon />
          <Box>
            {title && <AlertTitle>{title}</AlertTitle>}
            <AlertDescription>{description}</AlertDescription>
          </Box>
          <CloseButton
            alignSelf="flex-start"
            size="sm"
            position="relative"
            right={-1}
            top={-1}
            onClick={() => {
              toast.close(id);
            }}
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
    id: string = uuid(),
    title?: string,
    duration?: number | null | undefined,
    containerStyle?: CSSProperties
  ) => {
    if (toast.isActive(id)) {
      return;
    }
    toast({
      id,
      containerStyle,
      duration,
      position: DEFAULT_POSITION,
      render: () => (
        <Alert status="success" variant="subtle">
          <AlertIcon />
          <Box>
            {title && <AlertTitle>{title}</AlertTitle>}
            <AlertDescription>{description}</AlertDescription>
          </Box>
          <CloseButton
            alignSelf="flex-start"
            size="sm"
            position="relative"
            right={-1}
            top={-1}
            onClick={() => {
              toast.close(id);
            }}
          />
        </Alert>
      ),
    });
  };

  return { errorAlert, successAlert };
};
