import { AntTag as Tag, Box } from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks/useAlert";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import ConsentCategorySelect from "~/features/data-discovery-and-detection/action-center/ConsentCategorySelect";
import isConsentCategory from "~/features/data-discovery-and-detection/action-center/utils/isConsentCategory";
import TaxonomyCellContainer from "~/features/data-discovery-and-detection/tables/cells/TaxonomyCellContainer";
import { useUpdateSystemAssetsMutation } from "~/features/system/system-assets.slice";
import { Asset } from "~/types/api";
import { isErrorResult } from "~/types/errors";

const SystemAssetsDataUseCell = ({
  asset,
  systemId,
  readonly,
}: {
  asset: Asset;
  systemId: string;
  readonly?: boolean;
}) => {
  const { getDataUseDisplayName } = useTaxonomies();
  const [updateSystemAssets] = useUpdateSystemAssetsMutation();
  const { errorAlert, successAlert } = useAlert();

  const [isAdding, setIsAdding] = useState(false);

  const handleAddDataUse = async (use: string) => {
    const newDataUses = [...(asset.data_uses || []), use];
    const result = await updateSystemAssets({
      systemKey: systemId,
      assets: [{ id: asset.id, data_uses: newDataUses }],
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error));
    } else {
      successAlert(
        `Consent category added to ${asset.asset_type} "${asset.name}".`,
        `Confirmed`,
      );
    }
  };

  const handleDeleteDataUse = async (use: string) => {
    const newDataUses = asset.data_uses?.filter((u) => u !== use);
    const result = await updateSystemAssets({
      systemKey: systemId,
      assets: [{ id: asset.id, data_uses: newDataUses }],
    });
    if (isErrorResult(result)) {
      errorAlert(getErrorMessage(result.error));
    } else {
      successAlert(
        `Consent category removed from ${asset.asset_type} "${asset.name}".`,
        `Confirmed`,
      );
    }
  };

  const cellValues =
    asset.data_uses
      ?.filter((use) => isConsentCategory(use))
      .map((use) => ({
        label: getDataUseDisplayName(use),
        key: use,
      })) ?? [];

  if (readonly) {
    return (
      <TaxonomyCellContainer>
        {cellValues.map((use) => (
          <Tag key={use.key} data-testid={`data-use-${use.key}`} color="white">
            {use.label}
          </Tag>
        ))}
      </TaxonomyCellContainer>
    );
  }

  return (
    <TaxonomyCellContainer>
      {!isAdding && (
        <>
          {cellValues.map((use) => (
            <Tag
              key={use.key}
              data-testid={`data-use-${use.key}`}
              color="white"
              closable
              onClose={() => handleDeleteDataUse(use.key)}
              closeButtonLabel="Remove data use"
            >
              {use.label}
            </Tag>
          ))}
          <Tag
            onClick={() => setIsAdding(true)}
            data-testid="taxonomy-add-btn"
            addable
            aria-label="Add data use"
          />
        </>
      )}
      {isAdding && (
        <Box
          // eslint-disable-next-line tailwindcss/no-custom-classname
          className="select-wrapper"
          position="absolute"
          zIndex={10}
          top="0"
          left="0"
          width="100%"
          height="max"
          bgColor="#fff"
        >
          <ConsentCategorySelect
            selectedTaxonomies={asset.data_uses || []}
            onSelect={handleAddDataUse}
            onBlur={() => setIsAdding(false)}
            open
          />
        </Box>
      )}
    </TaxonomyCellContainer>
  );
};

export default SystemAssetsDataUseCell;
