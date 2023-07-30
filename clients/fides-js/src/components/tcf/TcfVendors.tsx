import { h } from "preact";
import { TCFVendorRecord } from "../../lib/tcf/types";
import { PrivacyExperience } from "../../lib/consent-types";
import { UpdateEnabledIds } from "./TcfOverlay";
import DataUseToggle from "../DataUseToggle";

const TcfVendors = ({
  allVendors,
  enabledIds,
  onChange,
}: {
  allVendors: PrivacyExperience["tcf_vendors"];
  enabledIds: string[];
  onChange: (payload: UpdateEnabledIds) => void;
}) => {
  if (!allVendors || allVendors.length === 0) {
    // TODO: empty state?
    return null;
  }

  const handleToggle = (vendor: TCFVendorRecord) => {
    if (enabledIds.indexOf(vendor.id) !== -1) {
      onChange({
        newEnabledIds: enabledIds.filter((e) => e === vendor.id),
        modelType: "vendors",
      });
    } else {
      onChange({
        newEnabledIds: [...enabledIds, vendor.id],
        modelType: "vendors",
      });
    }
  };

  return (
    <div>
      {allVendors.map((vendor) => (
        <DataUseToggle
          dataUse={{ key: vendor.id, name: vendor.name }}
          onToggle={() => {
            handleToggle(vendor);
          }}
          checked={enabledIds.indexOf(vendor.id) !== -1}
        />
      ))}
    </div>
  );
};

export default TcfVendors;
