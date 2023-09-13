import { ButtonGroup } from "@fidesui/react";

import AddCookie from "./AddCookie";
import AddVendor from "./AddVendor";

const AddButtons = ({ includeCookies }: { includeCookies?: boolean }) => (
  <ButtonGroup size="sm" colorScheme="primary">
    <AddVendor />
    {includeCookies ? <AddCookie /> : null}
  </ButtonGroup>
);

export default AddButtons;
