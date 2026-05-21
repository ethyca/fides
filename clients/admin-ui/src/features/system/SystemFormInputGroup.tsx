import { Card } from "fidesui";

interface SystemFormInputGroupProps {
  heading: string;
  HeadingButton?: React.ReactNode;
  children?: React.ReactNode;
}

const SystemFormInputGroup = ({
  heading,
  HeadingButton,
  children,
}: SystemFormInputGroupProps) => (
  <Card
    size="small"
    title={heading}
    extra={HeadingButton}
    className="mt-6 max-w-[720px]"
  >
    {children}
  </Card>
);

export default SystemFormInputGroup;
