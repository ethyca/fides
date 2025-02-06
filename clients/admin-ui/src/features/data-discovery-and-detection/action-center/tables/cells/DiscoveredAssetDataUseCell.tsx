import { AntButton as Button, Box, CloseIcon } from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { useUpdateAssetsDataUseMutation } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import ConsentCategorySelect from "~/features/data-discovery-and-detection/action-center/ConsentCategorySelect";
import { DiscoveredAssetResponse } from "~/features/data-discovery-and-detection/action-center/types";
import isConsentCategory from "~/features/data-discovery-and-detection/action-center/utils/isConsentCategory";
import TaxonomyAddButton from "~/features/data-discovery-and-detection/tables/cells/TaxonomyAddButton";
import TaxonomyCellContainer from "~/features/data-discovery-and-detection/tables/cells/TaxonomyCellContainer";
import TaxonomyBadge from "~/features/data-discovery-and-detection/TaxonomyBadge";
import { isErrorResult } from "~/types/errors";

const DeleteDataUseButton = ({ onClick }: { onClick: () => void }) => (
  <Button
    onClick={onClick}
    icon={<CloseIcon boxSize={2} />}
    size="small"
    type="text"
    className="max-h-4 max-w-4"
    aria-label="Remove data use"
  />
);

const DiscoveredAssetDataUseCell = ({
  asset,
}: {
  asset: DiscoveredAssetResponse;
}) => {
  const [isAdding, setIsAdding] = useState(false);

  const [updateAssetsDataUseMutation] = useUpdateAssetsDataUseMutation();
  const { successAlert, errorAlert } = useAlert();

  const { getDataUseDisplayName } = useTaxonomies();

  const handleAddDataUse = async (newDataUse: string) => {
    const existingUses = asset.data_uses || [];
    const result = await updateAssetsDataUseMutation({
      monitorId: asset.monitor_config_id!,
      urnList: [asset.urn],
      dataUses: [...existingUses, newDataUse],
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
    const existingUses = asset.data_uses || [];
    const result = await updateAssetsDataUseMutation({
      monitorId: asset.monitor_config_id!,
      urnList: [asset.urn],
      dataUses: existingUses.filter((use) => use !== useToDelete),
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

  const dataUses = asset.data_uses?.filter((use) => isConsentCategory(use));

  return (
    <TaxonomyCellContainer>
      {!isAdding && (
        <>
          {dataUses?.map((d) => (
            <TaxonomyBadge
              key={d}
              data-testid={`data-use-${d}`}
              closeButton={
                <DeleteDataUseButton onClick={() => handleDeleteDataUse(d)} />
              }
            >
              {getDataUseDisplayName(d)}
            </TaxonomyBadge>
          ))}
          <TaxonomyAddButton
            onClick={() => setIsAdding(true)}
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
