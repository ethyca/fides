import React, { useEffect, useRef, useState } from "react";
import { useField } from "formik";
import { FormControl, VStack, Flex, Tag } from "@fidesui/react";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import { useSelectedHistory } from "./SelectedHistoryContext";
import { Label } from "~/features/common/form/inputs";
import _ from "lodash";

const SystemDataTags = ({
  label,
  tooltip,
  ...props
}: {
  label: string;
  tooltip?: string;
  name: string;
}) => {
  const { selectedHistory, formType } = useSelectedHistory();
  const [initialField] = useField(props.name);
  const field = { ...initialField, value: initialField.value ?? [] };

  const contentRef = useRef(null);
  const [height, setHeight] = useState(null);
  const [longestValue, setLongestValue] = useState([]);
  const [shouldHighlight, setShouldHighlight] = useState(false);

  useEffect(() => {
    const beforeValue = _.get(selectedHistory?.before, props.name, []);
    const afterValue = _.get(selectedHistory?.after, props.name, []);

    // Determine whether to highlight
    setShouldHighlight(!_.isEqual(beforeValue, afterValue));

    // Determine the longest value for height calculation
    setLongestValue(
      beforeValue.length > afterValue.length ? beforeValue : afterValue
    );
  }, [selectedHistory, props.name]);

  useEffect(() => {
    if (contentRef.current) {
      setHeight(contentRef.current.offsetHeight);
    }
  }, [longestValue]);

  const highlightStyle = shouldHighlight
    ? formType === "before"
      ? {
          backgroundColor: "#FFF5F5",
          borderColor: "#E53E3E",
          borderTop: "1px dashed #E53E3E",
          borderBottom: "1px dashed #E53E3E",
        }
      : {
          backgroundColor: "#F0FFF4",
          borderColor: "#38A169",
          borderTop: "1px dashed #38A169",
          borderBottom: "1px dashed #38A169",
        }
    : {};

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
          <Label htmlFor={props.name} fontSize="xs" my={0} mr={1}>
            {label}
          </Label>
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Flex>
        <Flex
          wrap="wrap"
          alignItems="flex-start"
          ref={contentRef}
          style={{ minHeight: `${height}px` }}
        >
          {(height ? field.value : longestValue).map((value, index) => (
            <Tag key={index} colorScheme="gray" size="md" m={1}>
              {value}
            </Tag>
          ))}
        </Flex>
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

export default SystemDataTags;
