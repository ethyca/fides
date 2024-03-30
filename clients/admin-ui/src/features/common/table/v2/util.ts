import { theme } from "@fidesui/react-theme";

export const getTableTHandTDStyles = (cellId: string) =>
  cellId === "select"
    ? { padding: "0px" }
    : {
        paddingLeft: theme.space[3],
        paddingRight: `calc(${theme.space[3]} - 5px)`, // 5px is the width of the resizer
        paddingTop: "0px",
        paddingBottom: "0px",
        borderRadius: "0px",
      };
