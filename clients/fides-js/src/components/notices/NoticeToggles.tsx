import { h } from "preact";

import { ConsentMechanism, GpcStatus, PrivacyNotice } from "../../lib/consent-types";
import type { I18n } from "../../lib/i18n";

import Divider from "../Divider";

import { GpcBadge } from "../GpcBadge";
import DataUseToggle from "../DataUseToggle";

export interface NoticeToggleProps {
  noticeKey: string;
  title: string;
  description: string;
  consentMechanism: ConsentMechanism;
  gpcStatus: GpcStatus;
}

export const NoticeToggles = ({
  noticeToggles,
  i18n,
  enabledNoticeKeys,
  onChange,
}: {
  noticeToggles: NoticeToggleProps[];
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

  /**
   * TODO (PROD-1597): function docs
   */
  /*
  const extractTranslations = (notice: PrivacyNotice): { title?: string, description?: string } => {
    const titleMessageId = `exp.notices.${notice.id}.title`;
    const descriptionMessageId = `exp.notices.${notice.id}.description`;
    if (messageExists(i18n, titleMessageId) && messageExists(i18n, descriptionMessageId)) {
      const title = i18n.t(titleMessageId);
      const description = i18n.t(descriptionMessageId);
      return { title, description };
    } else {
      // Prefer the default ("en") translation, otherwise fallback to the first translation found
      const fallbackTranslation = notice.translations.find(e => e.language === DEFAULT_LOCALE) || notice.translations[0];
      if (fallbackTranslation) {
        // TODO: update preferences reporting...
        const title = fallbackTranslation.title;
        const description = fallbackTranslation.description;
        return { title, description };
      }
    }
    return { title: undefined, description: undefined }
  };
  */

  return (
    <div>
      {noticeToggles.map((props, idx) => {
        const { noticeKey, title, description, consentMechanism, gpcStatus } = props;
        const checked = enabledNoticeKeys.indexOf(noticeKey) !== -1;
        const isLast = idx === noticeToggles.length - 1;
        return (
          <div>
            <DataUseToggle
              noticeKey={noticeKey}
              title={title}
              checked={checked}
              onToggle={handleToggle}
              gpcBadge={
                <GpcBadge i18n={i18n} status={gpcStatus} />
              }
              disabled={
                consentMechanism === ConsentMechanism.NOTICE_ONLY
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
