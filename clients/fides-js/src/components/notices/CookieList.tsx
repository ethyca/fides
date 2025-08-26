import { ComponentChildren } from "preact";

import { Cookies } from "../../lib/consent-types";
import DataUseToggle from "../DataUseToggle";
import Divider from "../Divider";

export type CookieRecord = {
  title: string;
  description?: ComponentChildren;
};

const CookieList = ({
  cookiesByNotice,
  onBack,
}: {
  cookiesByNotice: Array<{
    noticeKey: string;
    title: string;
    cookies: Cookies[];
  }>;
  onBack: () => void;
}) => {
  return (
    <div>
      <button
        type="button"
        className="fides-link-button"
        onClick={onBack}
        aria-label="Back"
      >
        <span
          className="fides-flex-center fides-back-link"
          style={{ marginBottom: "12px" }}
        >
          Back
        </span>
      </button>
      {cookiesByNotice.length >= 1 ? (
        <div style={{ marginTop: "8px", marginBottom: "8px" }}>
          <strong>{cookiesByNotice[0].title} Cookies</strong>
        </div>
      ) : null}
      <div className="fides-modal-notices" style={{ marginTop: "12px" }}>
        {cookiesByNotice.map((group, groupIdx) => {
          const isLastGroup = groupIdx === cookiesByNotice.length - 1;
          const groupCookies = group.cookies || [];
          if (groupCookies.length === 0) {
            return null;
          }
          return (
            <div key={group.noticeKey}>
              {groupCookies.map((c, i) => {
                const isLastCookieInGroup = i === groupCookies.length - 1;
                const showDivider = !(isLastCookieInGroup && isLastGroup);
                return (
                  <div key={`${group.noticeKey}-${c.name}-${i}`}>
                    <DataUseToggle
                      noticeKey={`${group.noticeKey}-${c.name}-${i}`}
                      title={c.name}
                      checked={false}
                      onToggle={() => {}}
                      includeToggle={false}
                    >
                      <div className="fides-cookie-details">
                        <div style={{ marginBottom: "8px" }}>
                          <strong>Duration:</strong> A few hours
                        </div>
                        {c.description ? (
                          <div>
                            <strong>Description:</strong> {c.description}
                          </div>
                        ) : null}
                      </div>
                    </DataUseToggle>
                    {showDivider ? <Divider /> : null}
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CookieList;
