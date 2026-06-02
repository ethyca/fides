import { useMessage } from "fidesui";

import DataUseSelect from "~/features/common/dropdown/DataUseSelect";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { StagedResourceAPIResponse } from "~/types/api";

import { useUpdateAssetsDataUseMutation } from "../action-center.slice";
import InfrastructureClassificationSelect from "../components/InfrastructureClassificationSelect";
import { tagRender } from "../fields/MonitorFieldListItem";

/**
 * "Categories of consent" editor for website assets, wired to the website
 * data-use mutation.
 *
 * - List rows use the borderless inline style (matches datastore/infra).
 * - The detail drawer passes `bordered` to render a standard bordered
 *   multi-select form field.
 */
const WebsiteConsentSelect = ({
  asset,
  readonly,
  bordered,
}: {
  asset: StagedResourceAPIResponse;
  readonly?: boolean;
  bordered?: boolean;
}) => {
  const message = useMessage();
  const [updateAssetsDataUseMutation] = useUpdateAssetsDataUseMutation();

  const currentDataUses = [...(asset.preferred_data_uses || [])];

  const persist = async (dataUses: string[]) => {
    if (!asset.monitor_config_id) {
      return;
    }
    const result = await updateAssetsDataUseMutation({
      monitorId: asset.monitor_config_id,
      urnList: [asset.urn],
      dataUses,
    });
    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
    }
  };

  if (bordered) {
    return (
      <DataUseSelect
        mode="multiple"
        // TaxonomySelect defaults to variant="borderless"; force a bordered
        // box for the drawer's standard form-field look.
        variant="outlined"
        autoFocus={false}
        className="w-full"
        placeholder="Add categories of consent"
        value={currentDataUses}
        selectedTaxonomies={currentDataUses}
        disabled={readonly}
        onChange={(values) => persist((values as string[]) ?? [])}
      />
    );
  }

  const handleSelectDataUse = (value: string) => {
    if (!currentDataUses.includes(value)) {
      persist([...currentDataUses, value]);
    }
  };

  return (
    <InfrastructureClassificationSelect
      mode="multiple"
      value={currentDataUses}
      urn={asset.urn}
      disabled={readonly}
      onSelectDataUse={handleSelectDataUse}
      tagRender={(props) =>
        tagRender({
          ...props,
          // sparkle when the use was auto-detected (in data_uses) vs assigned
          isFromClassifier: asset.data_uses?.includes(props.value as string),
          onClose: () =>
            persist(currentDataUses.filter((use) => use !== props.value)),
        })
      }
    />
  );
};

export default WebsiteConsentSelect;
