import {
  AntButton as Button,
  AntButtonProps as ButtonProps,
  Icons,
} from "fidesui";

const TaxonomyAddButton = (props: ButtonProps) => (
  <Button
    size="small"
    icon={<Icons.Add />}
    className="max-h-5 max-w-5"
    data-testid="taxonomy-add-btn"
    {...props}
  />
);

export default TaxonomyAddButton;
