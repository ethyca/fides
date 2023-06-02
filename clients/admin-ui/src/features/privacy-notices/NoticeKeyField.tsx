import { useFormikContext } from "formik";
import snakeCase from "lodash.snakecase";
import { useEffect } from "react";

import { CustomTextInput } from "~/features/common/form/inputs";
import { PrivacyNoticeResponse } from "~/types/api";

const NoticeKeyField = ({ isEditing }: { isEditing: boolean }) => {
  const { values, setFieldValue } = useFormikContext<PrivacyNoticeResponse>();

  useEffect(() => {
    if (!isEditing) {
      const noticeKey = snakeCase(values.name);
      setFieldValue("notice_key", noticeKey);
    }
  }, [values.name, isEditing, setFieldValue]);

  return (
    <CustomTextInput
      name="notice_key"
      label="Key used in Fides cookie"
      variant="stacked"
    />
  );
};

export default NoticeKeyField;
