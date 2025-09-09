import { ComponentChildren } from "preact";

import { Cookies } from "../../lib/consent-types";
import DataUseToggle from "../DataUseToggle";

export type CookieRecord = {
  title: string;
  description?: ComponentChildren;
};

const VendorAssetDisclosure = ({
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
          <strong>{cookiesByNotice[0].title} Vendors</strong>
        </div>
      ) : null}
      <div className="fides-modal-notices" style={{ marginTop: "12px" }}>
        {(() => {
          // Group cookies across notices by system (vendor) name
          const vendorToCookies = new Map<string, Cookies[]>();
          cookiesByNotice.forEach((group) => {
            (group.cookies || []).forEach((cookie) => {
              const vendorName = cookie.system_name || "Other";
              const arr = vendorToCookies.get(vendorName) || [];
              arr.push(cookie);
              vendorToCookies.set(vendorName, arr);
            });
          });

          const vendorGroups = Array.from(vendorToCookies.entries());

          return vendorGroups.map(([vendorName, vendorCookies]) => {
            const hasRetentionInfo = vendorCookies.some(
              (ck) => ck.duration != null && ck.duration !== "",
            );
            return (
              <div key={`vendor-${vendorName}`}>
                <DataUseToggle
                  noticeKey={`vendor-${vendorName}`}
                  title={vendorName}
                  checked={false}
                  onToggle={() => {}}
                  includeToggle={false}
                >
                  <table className="fides-vendor-details-table">
                    <thead>
                      <tr>
                        <th width={hasRetentionInfo ? "80%" : undefined}>Cookies</th>
                        {hasRetentionInfo ? (
                          <th width="20%" style={{ textAlign: "right" }}>
                            Retention
                          </th>
                        ) : null}
                      </tr>
                    </thead>
                    <tbody>
                      {vendorCookies.map((ck) => (
                        <tr key={`${vendorName}-${ck.name}`}>
                          <td>
                            <div>Name: {ck.name}</div>
                            {ck.description ? (
                              <div>Description: {ck.description}</div>
                            ) : null}
                          </td>
                          {hasRetentionInfo ? (
                            <td style={{ textAlign: "right" }}>
                              {ck.duration ? ck.duration : "-"}
                            </td>
                          ) : null}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </DataUseToggle>
              </div>
            );
          });
        })()}
      </div>
    </div>
  );
};

export default VendorAssetDisclosure;
