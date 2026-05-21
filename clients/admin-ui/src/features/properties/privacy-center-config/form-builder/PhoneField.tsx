import { useStateBinding } from "@json-render/react";
import { Flex, Form } from "fidesui";
import React from "react";
import PhoneInput from "react-phone-number-input";
import FLAG_ICONS from "react-phone-number-input/flags";

import { FieldWrapper, IdentityFieldProps } from "./fieldUtils";
import styles from "./PhoneField.module.scss";

export const PhoneField = ({ props }: { props: IdentityFieldProps }) => {
  const [value, setValue] = useStateBinding<string>("/form/phone");

  return (
    <FieldWrapper elementId={props["data-element-id"]}>
      <Form.Item label="Phone" required={props.required}>
        <Flex align="center" className={styles.wrapper}>
          <PhoneInput
            flags={FLAG_ICONS}
            defaultCountry="US"
            value={value ?? ""}
            onChange={(v) => setValue(v ?? "")}
            aria-label="Phone"
            placeholder="000 000 0000"
            data-testid="field-phone"
            className="w-full"
          />
        </Flex>
      </Form.Item>
    </FieldWrapper>
  );
};
