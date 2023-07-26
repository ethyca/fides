import { h, VNode } from "preact";
import { Attributes } from "../lib/a11y-dialog";
import {
  PrivacyNotice,
  ExperienceConfig,
  FidesOptions,
  ComponentType,
} from "../lib/consent-types";
import NoticeToggles from "./NoticeToggles";
import CloseButton from "./CloseButton";
import GpcInfo from "./GpcInfo";
import TcfTabs from "./Tcf/TcfTabs";

type NoticeKeys = Array<PrivacyNotice["notice_key"]>;

const ConsentModal = ({
  attributes,
  experience,
  notices,
  enabledNoticeKeys,
  onChange,
  buttonGroup,
}: {
  attributes: Attributes;
  experience: ExperienceConfig;
  notices: PrivacyNotice[];
  enabledNoticeKeys: NoticeKeys;
  onClose: () => void;
  onChange: (enabledNoticeKeys: NoticeKeys) => void;
  buttonGroup: VNode;
  options: FidesOptions;
}) => {
  const { container, overlay, dialog, title, closeButton } = attributes;
  const showTcf = experience.component === ComponentType.TCF_OVERLAY;

  return (
    // @ts-ignore A11yDialog ref obj type isn't quite the same
    <div
      data-testid="consent-modal"
      {...container}
      className="fides-modal-container"
    >
      <div {...overlay} className="fides-modal-overlay" />
      <div
        data-testid="fides-modal-content"
        {...dialog}
        className="fides-modal-content"
      >
        <CloseButton ariaLabel="Close modal" onClick={closeButton.onClick} />
        <h1
          data-testid="fides-modal-header"
          {...title}
          className="fides-modal-header"
        >
          {experience.title}
        </h1>
        <p
          data-testid="fides-modal-description"
          className="fides-modal-description"
        >
          {experience.description}
        </p>
        <GpcInfo />
        {showTcf ? (
          <TcfTabs notices={notices} />
        ) : (
          <div className="fides-modal-notices">
            <NoticeToggles
              notices={notices}
              enabledNoticeKeys={enabledNoticeKeys}
              onChange={onChange}
            />
          </div>
        )}
        {buttonGroup}
        {experience.privacy_policy_link_label &&
        experience.privacy_policy_url ? (
          <a
            href={experience.privacy_policy_url}
            rel="noopener noreferrer"
            target="_blank"
            className="fides-modal-privacy-policy"
          >
            {experience.privacy_policy_link_label}
          </a>
        ) : null}
      </div>
    </div>
  );
};

export default ConsentModal;
