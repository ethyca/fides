import {
  AntButton as Button,
  AntButtonProps as ButtonProps,
  Icons,
} from "fidesui";

const TaxonomyAddButton = (props: ButtonProps) => (
  <Button
    size="small"
    icon={<Icons.Add />}
    className=" max-h-[20px] max-w-[20px]"
    data-testid="add-category-btn"
    aria-label="Add category"
    {...props}
  />
);

export default TaxonomyAddButton;
