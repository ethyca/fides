import {
  FormControl,
  FormErrorMessage,
  FormLabel,
  forwardRef,
  Input,
  VStack,
} from "@fidesui/react";
import { FieldHookConfig, useField } from "formik";

const ChipEmailInput = forwardRef(
  ({ ...props }: FieldHookConfig<string>, ref) => {
    const [field, meta] = useField(props);

    return (
      <FormControl
        alignItems="baseline"
        display="inline-flex"
        isRequired
        isInvalid={!!(meta.error && meta.touched)}
      >
        <FormLabel fontSize="md" htmlFor="email" w="30%">
          Email
        </FormLabel>
        <VStack align="flex-start" w="inherit">
          {/* @ts-ignore */}
          <Input {...field} {...props} ref={ref} />
          <FormErrorMessage>{meta.error}</FormErrorMessage>
        </VStack>
      </FormControl>
    );
  }
);

export default ChipEmailInput;
