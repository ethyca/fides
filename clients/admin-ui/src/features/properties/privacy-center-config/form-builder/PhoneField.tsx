import { useStateBinding } from "@json-render/react";
import { Form } from "fidesui";
import React from "react";
import PhoneInput from "react-phone-number-input";
import FLAG_ICONS from "react-phone-number-input/flags";

import styles from "./PhoneField.module.css";

interface IdentityFieldProps {
  required: boolean;
  "data-element-id"?: string;
}

export const PhoneField = ({ props }: { props: IdentityFieldProps }) => {
  const [value, setValue] = useStateBinding<string>("/form/phone");
  const elementId = props["data-element-id"];

  const content = (
    <Form.Item label="Phone" required={props.required}>
      <div
        className={styles.wrapper}
        style={{
          display: "flex",
          alignItems: "center",
          border: "1px solid #d9d9d9",
          borderRadius: 6,
          padding: "4px 11px",
          backgroundColor: "#fff",
          transition: "border-color 0.2s",
          cursor: "text",
        }}
      >
        <PhoneInput
          flags={FLAG_ICONS}
          defaultCountry="US"
          value={value ?? ""}
          onChange={(v) => setValue(v ?? "")}
          aria-label="Phone"
          placeholder="000 000 0000"
          data-testid="field-phone"
          style={{ width: "100%", display: "flex", alignItems: "center" }}
        />
      </div>
    </Form.Item>
  );

  if (!elementId) {
    return content;
  }
  return <span data-element-id={elementId}>{content}</span>;
};
