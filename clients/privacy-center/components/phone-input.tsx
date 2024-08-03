import "react-phone-number-input/style.css";

import { Input, InputProps } from "fidesui";
import dynamic from "next/dynamic";
// Importing the flag icons causes them to be bundled into the app instead of loaded from an outside
// domain. See: https://gitlab.com/catamphetamine/react-phone-number-input#including-all-flags
import FLAG_ICONS from "react-phone-number-input/flags";

const ReactPhoneNumberInput = dynamic(
  () => import("react-phone-number-input"),
  {
    ssr: false,
  },
);

/**
 * Wraps the PhoneInput component from react-phone-number-input in a Chakra Input
 * with common default props.
 */
export const PhoneInput = (props: InputProps) => (
  <Input
    as={ReactPhoneNumberInput}
    flags={FLAG_ICONS}
    type="tel"
    focusBorderColor="primary.500"
    placeholder="000 000 0000"
    defaultCountry="US"
    {...props}
  />
);
