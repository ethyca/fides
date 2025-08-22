import { ComponentChildren } from "preact";
import DataUseToggle from "../DataUseToggle";
import Divider from "../Divider";
import { Cookies } from "../../lib/consent-types";

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
        {"< Back"}
      </button>
      <div className="fides-modal-notices" style={{ marginTop: "12px" }}>
        {cookiesByNotice.map((item, idx) => {
          const isLast = idx === cookiesByNotice.length - 1;
          return (
            <div key={item.noticeKey}>
              <DataUseToggle
                noticeKey={item.noticeKey}
                title={item.title}
                checked={false}
                onToggle={() => {}}
                includeToggle={false}
              >
                {item.cookies && item.cookies.length > 0 ? (
                  <ul className="fides-cookie-list">
                    {item.cookies.map((c, i) => (
                      <li key={`${item.noticeKey}-${c.name}-${i}`}>{c.name}</li>
                    ))}
                  </ul>
                ) : null}
              </DataUseToggle>
              {!isLast ? <Divider /> : null}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CookieList;
