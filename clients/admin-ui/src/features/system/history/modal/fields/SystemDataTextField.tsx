import { Flex, FormControl, Text, VStack } from "fidesui";
import { useField } from "formik";
import _ from "lodash";
import { useEffect, useRef, useState } from "react";

import {
  CustomInputProps,
  Label,
  StringField,
} from "~/features/common/form/inputs";
import { InfoTooltip } from "~/features/common/InfoTooltip";

import { useSelectedHistory } from "../SelectedHistoryContext";

const SystemDataTextField = ({
  label,
  tooltip,
  ...props
}: CustomInputProps & StringField) => {
  const { selectedHistory, formType } = useSelectedHistory();
  const [initialField] = useField(props);
  const field = { ...initialField, value: initialField.value ?? "" };

  const contentRef = useRef<HTMLParagraphElement>(null);
  const [height, setHeight] = useState<number | null>(null);
  const [shouldHighlight, setShouldHighlight] = useState(false);

  useEffect(() => {
    const beforeValue = _.get(selectedHistory?.before, props.name) || "";
    const afterValue = _.get(selectedHistory?.after, props.name) || "";

    // Determine whether to highlight
    setShouldHighlight(!_.isEqual(beforeValue, afterValue));

    const longestValue =
      beforeValue.length > afterValue.length ? beforeValue : afterValue;

    if (contentRef.current) {
      // Temporarily set the value to the longest one to measure height
      contentRef.current.textContent = longestValue;

      // Measure and set the height
      setHeight(contentRef.current.offsetHeight);

      // Reset the value to the actual one
      contentRef.current.textContent = field.value;
    }
  }, [selectedHistory, props.name, field.value]);

  let highlightStyle = {};

  if (shouldHighlight) {
    if (formType === "before") {
      highlightStyle = {
        backgroundColor: "#FFF5F5",
        borderColor: "#E53E3E",
        borderTop: "1px dashed #E53E3E",
        borderBottom: "1px dashed #E53E3E",
      };
    } else {
      highlightStyle = {
        backgroundColor: "#F0FFF4",
        borderColor: "#38A169",
        borderTop: "1px dashed #38A169",
        borderBottom: "1px dashed #38A169",
      };
    }
  }

  return (
    <FormControl
      style={highlightStyle}
      paddingLeft={4}
      paddingRight={4}
      paddingTop={3}
      paddingBottom={3}
      marginTop="-1px !important"
    >
      <VStack alignItems="start">
        <Flex alignItems="center">
          <Label htmlFor={props.id || props.name} fontSize="xs" my={0} mr={1}>
            {label}
          </Label>
          <InfoTooltip label={tooltip} />
        </Flex>
        <Text
          fontSize="14px"
          ref={contentRef}
          style={{ height: `${height}px` }}
        >
          {field.value}
        </Text>
        {formType === "before" && shouldHighlight && (
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
