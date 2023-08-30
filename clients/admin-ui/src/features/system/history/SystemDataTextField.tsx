import { FormControl, VStack, Flex, Text } from "@fidesui/react";
import { useField } from "formik";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import {
  CustomInputProps,
  StringField,
  Label,
} from "~/features/common/form/inputs";
import { useSelectedHistory } from "./SelectedHistoryContext";
import { useEffect, useRef, useState } from "react";
import _ from "lodash";

const SystemDataTextField = ({
  label,
  tooltip,
  ...props
}: CustomInputProps & StringField) => {
  const { selectedHistory, formType } = useSelectedHistory();
  const [initialField] = useField(props);
  const field = { ...initialField, value: initialField.value ?? "" };

  const contentRef = useRef(null);
  const [height, setHeight] = useState(null);

  useEffect(() => {
    const beforeValue = _.get(selectedHistory?.before, props.name, "");
    const afterValue = _.get(selectedHistory?.after, props.name, "");
    const longestValue =
      beforeValue.length > afterValue.length ? beforeValue : afterValue;

    // Temporarily set the value to the longest one to measure height
    contentRef.current.textContent = longestValue;

    // Measure and set the height
    if (contentRef.current) {
      setHeight(contentRef.current.offsetHeight);
    }

    // Reset the value to the actual one
    contentRef.current.textContent = field.value;
  }, [selectedHistory, props.name, field.value]);

  const highlightStyle =
    formType === "before"
      ? { backgroundColor: "#FFF5F5", borderColor: "#E53E3E" }
      : { backgroundColor: "#F0FFF4", borderColor: "#38A169" };

  return (
    <FormControl
      style={highlightStyle}
      paddingLeft={4}
      paddingRight={4}
      paddingTop={3}
      paddingBottom={3}
      borderTop="1px dashed"
      borderBottom="1px dashed"
      marginTop="-1px !important"
    >
      <VStack alignItems="start">
        <Flex alignItems="center">
          <Label htmlFor={props.id || props.name} fontSize="xs" my={0} mr={1}>
            {label}
          </Label>
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Flex>
        <Text
          ref={contentRef}
          style={{ color: "#718096", height: `${height}px` }}
        >
          {field.value}
        </Text>
        {formType === "before" && (
          <div
            style={{
              position: "absolute",
              right: "-22px",
              top: "50%",
              transform: "translateY(-50%)",
            }}
          >
            →
          </div>
        )}
      </VStack>
    </FormControl>
  );
};

export default SystemDataTextField;
