import { AntTag as Tag, Box } from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { useUpdateAssetsDataUseMutation } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import ConsentCategorySelect from "~/features/data-discovery-and-detection/action-center/ConsentCategorySelect";
import isConsentCategory from "~/features/data-discovery-and-detection/action-center/utils/isConsentCategory";
import TaxonomyCellContainer from "~/features/data-discovery-and-detection/tables/cells/TaxonomyCellContainer";
import { StagedResourceAPIResponse } from "~/types/api/models/StagedResourceAPIResponse";
import { isErrorResult } from "~/types/errors";

const DiscoveredAssetDataUseCell = ({
  asset,
}: {
  asset: StagedResourceAPIResponse;
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

  const dataUses = currentDataUses.filter((use) => isConsentCategory(use));

  return (
    <TaxonomyCellContainer>
      {!isAdding && (
        <>
          {dataUses?.map((d) => (
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
            selectedTaxonomies={dataUses || []}
            onSelect={handleAddDataUse}
            onBlur={() => setIsAdding(false)}
            open
          />
        </Box>
      )}
    </TaxonomyCellContainer>
  );
};

export default DiscoveredAssetDataUseCell;
