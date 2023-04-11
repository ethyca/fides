import { Box } from "@fidesui/react";

import { PrivacyNoticeResponse } from "~/types/api";

import {
  defaultInitialValues,
  transformPrivacyNoticeResponseToCreation,
} from "./form";

const PrivacyNoticeForm = ({
  privacyNotice: passedInPrivacyNotice,
}: {
  privacyNotice?: PrivacyNoticeResponse;
}) => {
  const initialValues = passedInPrivacyNotice
    ? transformPrivacyNoticeResponseToCreation(passedInPrivacyNotice)
    : defaultInitialValues;

  return <Box>{initialValues.name}</Box>;
};

export default PrivacyNoticeForm;
