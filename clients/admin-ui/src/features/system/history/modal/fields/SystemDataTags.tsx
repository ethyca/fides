import { AntTag as Tag, Flex, FormControl, VStack } from "fidesui";
import { useField } from "formik";
import _ from "lodash";
import React, { useEffect, useRef, useState } from "react";

import { Label } from "~/features/common/form/inputs";
import QuestionTooltip from "~/features/common/QuestionTooltip";

import { useSelectedHistory } from "../SelectedHistoryContext";

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

  const contentRef = useRef<HTMLDivElement | null>(null);
  const [height, setHeight] = useState<number | null>(null);
  const [longestValue, setLongestValue] = useState([]);
  const [shouldHighlight, setShouldHighlight] = useState(false);

  useEffect(() => {
    const beforeValue = _.get(selectedHistory?.before, props.name) || [];
    const afterValue = _.get(selectedHistory?.after, props.name) || [];

    // Determine whether to highlight
    setShouldHighlight(!_.isEqual(beforeValue, afterValue));

    // Determine the longest value for height calculation
    setLongestValue(
      beforeValue.length > afterValue.length ? beforeValue : afterValue,
    );
  }, [selectedHistory, props.name]);

  useEffect(() => {
    if (contentRef.current) {
      setHeight(contentRef.current.offsetHeight);
    }
  }, [longestValue]);

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
          {(height ? field.value : longestValue).map(
            (value: any, index: number) => (
              // eslint-disable-next-line react/no-array-index-key
              <Tag key={index} color="marble" className="m-1">
                {typeof value === "object" ? value.fides_key : value}
              </Tag>
            ),
          )}
        </Flex>
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

export default SystemDataTags;
