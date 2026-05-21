// PROTOTYPE — delete with TCF history
import { useRouter } from "next/router";

import FixedLayout from "~/features/common/FixedLayout";
import {
  MOCK_TCF_EXPERIENCE_ID,
  MOCK_TCF_EXPERIENCE_NAME,
} from "~/features/privacy-experience/version-history/mockHistory";
import { TCFVersionHistory } from "~/features/privacy-experience/version-history/TCFVersionHistory";

const TCFVersionHistoryPage = () => {
  const router = useRouter();
  const rawId = router.query.id;
  const experienceId = Array.isArray(rawId) ? rawId[0] : rawId;

  const resolvedName =
    experienceId === MOCK_TCF_EXPERIENCE_ID ? MOCK_TCF_EXPERIENCE_NAME : "TCF";

  return (
    <FixedLayout title={`${resolvedName} version history`}>
      <TCFVersionHistory
        experienceId={experienceId ?? MOCK_TCF_EXPERIENCE_ID}
        experienceName={resolvedName}
      />
    </FixedLayout>
  );
};

export default TCFVersionHistoryPage;
