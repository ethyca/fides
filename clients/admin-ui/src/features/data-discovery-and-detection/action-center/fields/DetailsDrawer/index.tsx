import { Drawer } from "fidesui";

import { DetailsDrawerFooter } from "./DetailsDrawerFooter";
import { DetailsDrawerTitle } from "./DetailsDrawerTitle";
import type { DetailsDrawerProps } from "./types";

export const DetailsDrawer = ({
  title,
  titleIcon,
  titleTag,
  actions,
  width,
  ...drawerProps
}: DetailsDrawerProps) => (
  <Drawer
    title={
      <DetailsDrawerTitle
        title={title}
        titleIcon={titleIcon}
        titleTag={titleTag}
      />
    }
    footer={
      drawerProps.footer || !actions ? (
        drawerProps.footer
      ) : (
        <DetailsDrawerFooter itemKey={drawerProps.itemKey} actions={actions} />
      )
    }
    width={width}
    {...drawerProps}
  />
);
