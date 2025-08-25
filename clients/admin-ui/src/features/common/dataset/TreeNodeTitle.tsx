import { Text } from "fidesui";

const TreeNodeTitle = ({ nodeData }: any) => {
  if (nodeData.selectable) {
    return <Text fontWeight="bold">{nodeData.title}</Text>;
  }
  return <Text>{nodeData.title}</Text>;
};

export default TreeNodeTitle;
