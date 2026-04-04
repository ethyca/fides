import classNames from "classnames";
import { Form, Icons, Switch } from "fidesui";

import styles from "./SwitchField.module.scss";

interface SwitchFieldProps
  extends Omit<React.ComponentProps<typeof Form.Item>, "tooltip"> {
  tooltip?: string;
  switchProps?: React.ComponentProps<typeof Switch>;
}

/** Renders a switch with label on left, switch on right */
export const SwitchField = ({
  tooltip,
  switchProps,
  ...props
}: SwitchFieldProps) => (
  <Form.Item
    layout="horizontal"
    colon={false}
    valuePropName="checked"
    {...props}
    tooltip={
      tooltip
        ? {
            title: tooltip,
            icon: (
              <Icons.InformationFilled
                color="var(--fidesui-neutral-200)"
                size={14}
              />
            ),
          }
        : undefined
    }
    className={classNames(props.className, styles["switch-field"])}
  >
    <Switch size="small" data-testid={`input-${props.name}`} {...switchProps} />
  </Form.Item>
);
