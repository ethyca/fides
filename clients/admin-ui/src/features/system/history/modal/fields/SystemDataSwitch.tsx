import { AntTag as Tag, Flex, FormControl, VStack } from "fidesui";
import { useField } from "formik";
import _ from "lodash";
import { useEffect, useState } from "react";

import {
  CustomInputProps,
  Label,
  StringField,
} from "~/features/common/form/inputs";
import QuestionTooltip from "~/features/common/QuestionTooltip";

import { useSelectedHistory } from "../SelectedHistoryContext";

const SystemDataSwitch = ({
  label,
  tooltip,
  ...props
}: CustomInputProps & StringField) => {
  const { selectedHistory, formType } = useSelectedHistory();
  const [initialField] = useField(props);
  const field = { ...initialField, value: initialField.value };

  const [shouldHighlight, setShouldHighlight] = useState(false);

  useEffect(() => {
    const beforeValue = _.get(selectedHistory?.before, props.name);
    const afterValue = _.get(selectedHistory?.after, props.name);

    // Determine whether to highlight
    setShouldHighlight(beforeValue !== afterValue);
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
      <VStack alignItems="start" minHeight="46px">
        <Flex alignItems="center">
          <Label htmlFor={props.id || props.name} fontSize="xs" my={0} mr={1}>
            {label}
          </Label>
          {tooltip ? <QuestionTooltip label={tooltip} /> : null}
        </Flex>
        {field.value !== undefined && (
          <Tag color="marble" className="m-1">
            {field.value ? "YES" : "NO"}
          </Tag>
        )}
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

export default SystemDataSwitch;
