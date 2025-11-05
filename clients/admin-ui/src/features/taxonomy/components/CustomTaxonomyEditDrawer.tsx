import { AntButton as Button } from "fidesui";

import { DetailsDrawer } from "~/features/data-discovery-and-detection/action-center/fields/DetailsDrawer";
import { DetailsDrawerProps } from "~/features/data-discovery-and-detection/action-center/fields/DetailsDrawer/types";
import CustomTaxonomyDetails from "~/features/taxonomy/components/CustomTaxonomyDetails";
import { useUpdateCustomTaxonomyMutation } from "~/features/taxonomy/taxonomy.slice";
import { TaxonomyResponse } from "~/types/api/models/TaxonomyResponse";
import { TaxonomyUpdate } from "~/types/api/models/TaxonomyUpdate";

interface CustomTaxonomyEditDrawerProps
  extends Omit<DetailsDrawerProps, "itemKey"> {
  taxonomy?: TaxonomyResponse;
}

const CustomTaxonomyEditDrawer = ({
  taxonomy,
  ...props
}: CustomTaxonomyEditDrawerProps) => {
  const [updateCustomTaxonomy, { isLoading: isUpdating }] =
    useUpdateCustomTaxonomyMutation();

  const handleUpdate = async (values: TaxonomyUpdate) => {
    // const result = await updateCustomTaxonomy({
    //   fides_key: taxonomy?.fides_key as string,
    //   ...values,
    // });
    console.log(values);
  };

  return (
    <DetailsDrawer
      title={`Edit ${taxonomy?.name}`}
      {...props}
      itemKey=""
      open={!!taxonomy}
      destroyOnHidden
      footer={
        <Button
          type="primary"
          htmlType="submit"
          loading={isUpdating}
          onClick={handleUpdate}
        >
          Save
        </Button>
      }
    >
      <CustomTaxonomyDetails taxonomy={taxonomy} onSubmit={handleUpdate} />
    </DetailsDrawer>
  );
};

export default CustomTaxonomyEditDrawer;
