import { h } from "preact";

import { ConsentMechanism, PrivacyNotice } from "../../lib/consent-types";
import { DEFAULT_LOCALE, I18n, messageExists } from "../../lib/i18n";

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


  /**
   * TODO: function docs
   */
  const extractTranslations = (notice: PrivacyNotice): { title?: string, description?: string } => {
    const titleMessageId = `exp.notices.${notice.id}.title`;
    const descriptionMessageId = `exp.notices.${notice.id}.description`;
    if (messageExists(i18n, titleMessageId) && messageExists(i18n, descriptionMessageId)) {
      const title = i18n.t(titleMessageId);
      const description = i18n.t(descriptionMessageId);
      return { title, description };
    } else {
      // Prefer the default ("en") translation, otherwise fallback to the first translation found
      const fallbackTranslation = notice.translations.find(e => e.language === "en") || notice.translations[0];
      if (fallbackTranslation) {
        // TODO: update preferences reporting...
        const title = fallbackTranslation.title;
        const description = fallbackTranslation.description;
        return { title, description };
      }
    }
    return { title: undefined, description: undefined }
  };

  return (
    <div>
      {notices.map((notice, idx) => {
        const { title, description } = extractTranslations(notice);
        const checked = enabledNoticeKeys.indexOf(notice.notice_key) !== -1;
        const isLast = idx === notices.length - 1;
        const noticeKey = notice.notice_key;
        return (
          <div>
            <DataUseToggle
              noticeKey={noticeKey}
              title={title}
              checked={checked}
              onToggle={handleToggle}
              gpcBadge={
                <GpcBadgeForNotice
                  i18n={i18n}
                  notice={notice}
                  value={checked}
                />
              }
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
