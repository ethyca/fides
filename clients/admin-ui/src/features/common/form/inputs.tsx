import {
  Box,
  FormControl,
  FormErrorMessage,
  FormLabel,
  Grid,
  Input,
  Select,
} from "@fidesui/react";
import { FieldHookConfig, useField } from "formik";

import QuestionTooltip from "~/features/common/QuestionTooltip";

interface InputProps {
  label: string;
  tooltip?: string;
}

export const CustomTextInput = ({
  label,
  tooltip,
  ...props
}: InputProps & FieldHookConfig<string>) => {
  const [field, meta] = useField(props);
  const { type, placeholder } = props;
  const isInvalid = !!(meta.touched && meta.error);
  return (
    <FormControl isInvalid={isInvalid}>
      <Grid templateColumns="1fr 3fr">
        <FormLabel htmlFor={props.id || props.name} size="sm">
          {label}
        </FormLabel>
        <Box display="flex" alignItems="center">
          <Input
            {...field}
            type={type}
            placeholder={placeholder}
            size="sm"
            mr="2"
          />
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Box>
      </Grid>
      {isInvalid ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
    </FormControl>
  );
};

export const CustomSelect = ({
  label,
  tooltip,
  ...props
}: InputProps & FieldHookConfig<string>) => {
  const [field, meta] = useField(props);
  const isInvalid = !!(meta.touched && meta.error);
  return (
    <FormControl isInvalid={isInvalid}>
      <Grid templateColumns="1fr 3fr">
        <FormLabel htmlFor={props.id || props.name} size="sm">
          {label}
        </FormLabel>
        <Box display="flex" alignItems="center">
          {/* @ts-ignore having trouble getting Formik and Chakra select to be happy together */}
          <Select {...field} {...props} size="sm" mr="2" />
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Box>
      </Grid>
      {isInvalid ? <FormErrorMessage>{meta.error}</FormErrorMessage> : null}
    </FormControl>
  );
};
