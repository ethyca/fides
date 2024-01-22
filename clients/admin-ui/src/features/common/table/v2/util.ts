export const getTableTHandTDStyles = (cellId: string) =>
  cellId === "select"
    ? { padding: "0px" }
    : {
        paddingLeft: "16px",
        paddingRight: "8px",
        paddingTop: "0px",
        paddingBottom: "0px",
      };
