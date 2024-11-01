import {
  AntButton as Button,
  AntButtonProps as ButtonProps,
  SmallAddIcon,
} from "fidesui";

const TaxonomyAddButton = (props: ButtonProps) => (
  <Button
    size="small"
    icon={<SmallAddIcon mb="1px" />}
    className=" max-h-[20px] max-w-[20px] rounded-sm border-gray-200 bg-white hover:!bg-gray-100"
    data-testid="add-category-btn"
    aria-label="Add category"
    {...props}
  />
);

export default TaxonomyAddButton;
