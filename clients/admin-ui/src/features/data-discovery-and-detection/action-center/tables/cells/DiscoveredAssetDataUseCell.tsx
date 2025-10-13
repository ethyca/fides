import { AntSpace as Space, AntTag as Tag } from "fidesui";
import { truncate } from "lodash";
import { useEffect, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import styles from "~/features/common/table/cells/Cells.module.scss";
import { TagExpandableCell } from "~/features/common/table/cells/TagExpandableCell";
import { ColumnState } from "~/features/common/table/cells/types";
import { useUpdateAssetsDataUseMutation } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import ConsentCategorySelect from "~/features/data-discovery-and-detection/action-center/ConsentCategorySelect";
import { StagedResourceAPIResponse } from "~/types/api/models/StagedResourceAPIResponse";
import { isErrorResult } from "~/types/errors";

const DiscoveredAssetDataUseCell = ({
  asset,
  readonly,
  columnState,
  onChange,
}: {
  asset: StagedResourceAPIResponse;
  readonly?: boolean;
  columnState?: ColumnState;
  onChange?: (dataUses: string[]) => void;
}) => {
  const [isAdding, setIsAdding] = useState(false);
  const [isExpanded, setIsExpanded] = useState(
    columnState?.isExpanded || false,
  );

  const [updateAssetsDataUseMutation] = useUpdateAssetsDataUseMutation();
  const { successAlert, errorAlert } = useAlert();

  const { getDataUseDisplayName } = useTaxonomies();

  const currentDataUses = [...(asset.preferred_data_uses || [])].sort();

  const truncatedAssetName = truncate(asset.name || "", { length: 50 });

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
        `Consent category added to ${asset.resource_type} "${truncatedAssetName}".`,
        `Confirmed`,
      );
      onChange?.([...currentDataUses, newDataUse]);
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
        `Consent category removed from ${asset.resource_type} "${truncatedAssetName}".`,
        `Confirmed`,
      );
      onChange?.(currentDataUses.filter((use) => use !== useToDelete));
    }
  };

  useEffect(() => {
    setIsExpanded(columnState?.isExpanded || false);
  }, [columnState?.isExpanded]);

  if (readonly) {
    return (
      <TagExpandableCell
        values={currentDataUses?.map((d) => ({
          label: getDataUseDisplayName(d),
          key: d,
        }))}
        columnState={columnState}
        onStateChange={setIsExpanded}
      />
    );
  }

  return (
    <>
      {!isAdding && (
        <Space align="start">
          <Tag
            onClick={() => setIsAdding(true)}
            data-testid="taxonomy-add-btn"
            addable
            aria-label="Add data use"
          />
          <TagExpandableCell
            values={currentDataUses?.map((d) => ({
              label: getDataUseDisplayName(d),
              key: d,
            }))}
            columnState={{ ...columnState, isExpanded }}
            tagProps={{ closable: true, closeButtonLabel: "Remove data use" }}
            onTagClose={handleDeleteDataUse}
            onStateChange={setIsExpanded}
          />
        </Space>
      )}
      {isAdding && (
        <div
          className={styles.cellBleed}
          style={{ backgroundColor: "var(--fides-color-white)" }}
        >
          <ConsentCategorySelect
            selectedTaxonomies={currentDataUses}
            onSelect={handleAddDataUse}
            onBlur={() => setIsAdding(false)}
            onKeyDown={(key) => {
              if (key.key === "Escape") {
                setIsAdding(false);
              }
            }}
            open
          />
        </div>
      )}
    </>
  );
};

export default DiscoveredAssetDataUseCell;
