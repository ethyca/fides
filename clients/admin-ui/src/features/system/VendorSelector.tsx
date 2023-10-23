import { InputGroup, InputRightElement, Spacer, Text } from "@fidesui/react";
import { useState } from "react";
import {
  CustomCreatableSelect,
  CustomSelect,
  CustomTextInput,
  TextInput,
} from "~/features/common/form/inputs";

const VendorSelector = () => {
  {
    return (
      <InputGroup
        style={{ position: "relative", display: "flex", flex: "flex-start" }}
      >
        <CustomTextInput name="test" variant="stacked" label="Vendor" />
        <InputRightElement style={{ marginTop: "22px" }}>
          <Text>test</Text>
        </InputRightElement>
        <InputRightElement>
          <Spacer />
        </InputRightElement>
      </InputGroup>
    );
  }
};

export default VendorSelector;
