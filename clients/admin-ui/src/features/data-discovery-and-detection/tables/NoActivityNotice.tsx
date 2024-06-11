import EmptyTableNotice from "~/features/common/table/EmptyTableNotice";

const NoActivityNotice = () => (
  <EmptyTableNotice
    title="No activity found"
    description="You're up to date!"
  />
);

export default NoActivityNotice;
