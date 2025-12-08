import { useState } from "react";

import { EnableCell } from "~/features/common/table/cells/EnableCell";
import { useLimitedPatchPrivacyNoticesMutation } from "~/features/privacy-notices/privacy-notices.slice";
import { PrivacyNoticeRowType } from "~/features/privacy-notices/table/PrivacyNoticeRowType";

const MODAL_COPY = `Are you sure you want to disable this privacy notice? Disabling this
notice means your users will no longer see this explanation about
your data uses which is necessary to ensure compliance.`;

const NoticeEnableCell = ({ record }: { record: PrivacyNoticeRowType }) => {
  const [patchNoticeMutationTrigger] = useLimitedPatchPrivacyNoticesMutation();
  const [isLoading, setIsLoading] = useState(false);

  const {
    id,
    disabled: noticeIsDisabled,
    systems_applicable: systemsApplicable,
    data_uses: dataUses,
  } = record;

  const onToggle = async (toggle: boolean) => {
    setIsLoading(true);
    const response = await patchNoticeMutationTrigger({
      id,
      disabled: !toggle,
    });
    setIsLoading(false);
    return response;
  };

  const hasDataUses = !!dataUses;

  const toggleIsDisabled =
    (noticeIsDisabled && !systemsApplicable) || !hasDataUses;

  return (
    <EnableCell
      enabled={!noticeIsDisabled}
      isDisabled={toggleIsDisabled}
      onToggle={onToggle}
      title="Disable privacy notice"
      message={MODAL_COPY}
      loading={isLoading}
    />
  );
};

export default NoticeEnableCell;
