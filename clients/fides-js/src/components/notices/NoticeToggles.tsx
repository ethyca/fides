import { h } from "preact";

import { ConsentMechanism, PrivacyNotice } from "../../lib/consent-types";
import type { I18n } from "../../lib/i18n";

import Divider from "../Divider";

import { GpcBadgeForNotice } from "../GpcBadge";
import DataUseToggle from "../DataUseToggle";

const NoticeToggles = ({
  notices,
  i18n,
  enabledNoticeKeys,
  onChange,
}: {
  notices: PrivacyNotice[];
  i18n: I18n;
  enabledNoticeKeys: Array<PrivacyNotice["notice_key"]>;
  onChange: (keys: Array<PrivacyNotice["notice_key"]>) => void;
}) => {
  const handleToggle = (noticeKey: PrivacyNotice["notice_key"]) => {
    // Add the notice to list of enabled notices
    if (enabledNoticeKeys.indexOf(noticeKey) === -1) {
      onChange([...enabledNoticeKeys, noticeKey]);
    }
    // Remove the notice from the list of enabled notices
    else {
      onChange(enabledNoticeKeys.filter((n) => n !== noticeKey));
    }
  };

  return (
    <div>
      {notices.map((notice, idx) => {
        const i18nKey = `exp.notices.${notice.id}`;
        const title = i18n.t(`${i18nKey}.title`);
        const description = i18n.t(`${i18nKey}.description`);
        const checked = enabledNoticeKeys.indexOf(notice.notice_key) !== -1;
        const isLast = idx === notices.length - 1;
        // TODO: check
        const dataUse = { key: notice.notice_key, name: notice.name };
        return (
          <div>
            <DataUseToggle
              dataUse={dataUse}
              checked={checked}
              onToggle={handleToggle}
              gpcBadge={<GpcBadgeForNotice notice={notice} value={checked} />}
              disabled={
                notice.consent_mechanism === ConsentMechanism.NOTICE_ONLY
              }
            >
              {description}
            </DataUseToggle>
            {!isLast ? <Divider /> : null}
          </div>
        );
      })}
    </div>
  );
};

export default NoticeToggles;
