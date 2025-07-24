import { AntSpace as Space, AntTag as Tag } from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import styles from "~/features/common/table/cells/Cells.module.scss";
import { useUpdateAssetsDataUseMutation } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import ConsentCategorySelect from "~/features/data-discovery-and-detection/action-center/ConsentCategorySelect";
import isConsentCategory from "~/features/data-discovery-and-detection/action-center/utils/isConsentCategory";
import { StagedResourceAPIResponse } from "~/types/api/models/StagedResourceAPIResponse";
import { isErrorResult } from "~/types/errors";

const DiscoveredAssetDataUseCell = ({
  asset,
  readonly,
}: {
  asset: StagedResourceAPIResponse;
  readonly?: boolean;
}) => {
  const [isAdding, setIsAdding] = useState(false);

  const [updateAssetsDataUseMutation] = useUpdateAssetsDataUseMutation();
  const { successAlert, errorAlert } = useAlert();

  const { getDataUseDisplayName } = useTaxonomies();

  const currentDataUses =
    asset.user_assigned_data_uses || asset.data_uses || [];

  const handleAddDataUse = async (newDataUse: string) => {
    const result = await updateAssetsDataUseMutation({
      monitorId: asset.monitor_config_id!,
      urnList: [asset.urn],
      dataUses: [...currentDataUses, newDataUse],
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error));
    } else {
      successAlert(
        `Consent category added to ${asset.resource_type} "${asset.name}" .`,
        `Confirmed`,
      );
    }
    setIsAdding(false);
  };

  const handleDeleteDataUse = async (useToDelete: string) => {
    const result = await updateAssetsDataUseMutation({
      monitorId: asset.monitor_config_id!,
      urnList: [asset.urn],
      dataUses: currentDataUses.filter((use) => use !== useToDelete),
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error));
    } else {
      successAlert(
        `Consent category removed from ${asset.resource_type} "${asset.name}".`,
        `Confirmed`,
      );
    }
  };

  const dataUses = asset.user_assigned_data_uses?.length
    ? asset.user_assigned_data_uses
    : asset.data_uses;

  const consentUses = dataUses?.filter((use) => isConsentCategory(use));

  if (readonly) {
    return (
      <Space direction="vertical">
        {consentUses?.map((d) => (
          <Tag key={d} color="white">
            {getDataUseDisplayName(d)}
          </Tag>
        ))}
      </Space>
    );
  }

  return (
    <>
      {!isAdding && (
        <Space wrap>
          {consentUses?.map((d) => (
            <Tag
              key={d}
              data-testid={`data-use-${d}`}
              color="white"
              closable
              onClose={() => handleDeleteDataUse(d)}
              closeButtonLabel="Remove data use"
            >
              {getDataUseDisplayName(d)}
            </Tag>
          ))}
          <Tag
            onClick={() => setIsAdding(true)}
            data-testid="taxonomy-add-btn"
            addable
            aria-label="Add data use"
          />
        </Space>
      )}
      {isAdding && (
        <div
          className={styles.cellBleed}
          style={{ backgroundColor: "var(--fides-color-white)" }}
        >
          <ConsentCategorySelect
            selectedTaxonomies={consentUses || []}
            onSelect={handleAddDataUse}
            onBlur={() => setIsAdding(false)}
            open
          />
        </div>
      )}
    </>
  );
};

export default DiscoveredAssetDataUseCell;
