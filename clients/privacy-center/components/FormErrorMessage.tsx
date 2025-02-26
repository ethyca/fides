import {
  Box,
  FormErrorMessage as ChakraFormErrorMessage,
  forwardRef,
  useFormControlContext,
} from "fidesui";

/**
 * This is a thin wrapper around Chakra's FormErrorMessage that leaves room for the error message
 * even when the field is valid. This prevents the form from changing height when validation runs,
 * which can be annoying on blur.
 *
 * Chakra Source:
 * https://github.com/chakra-ui/chakra-ui/blob/%40chakra-ui/react%401.8.8/packages/form-control/src/form-error.tsx
 */
export const FormErrorMessage: typeof ChakraFormErrorMessage = forwardRef(
  (props, ref) => {
    const field = useFormControlContext();
    if (!field?.isInvalid) {
      return <Box mt={2} minH={4} />;
    }

    return <ChakraFormErrorMessage ref={ref} {...props} />;
  },
);
