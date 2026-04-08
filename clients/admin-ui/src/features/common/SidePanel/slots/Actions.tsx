import React from "react";

import styles from "../SidePanel.module.scss";

interface ActionsProps {
  children: React.ReactNode;
}

const Actions: React.FC<ActionsProps> & { slotOrder: number } = ({
  children,
}) => <div className={styles.actions}>{children}</div>;
Actions.slotOrder = 3;

export default Actions;
