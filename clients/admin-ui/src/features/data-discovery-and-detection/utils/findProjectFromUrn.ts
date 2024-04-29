const findProjectFromUrn = (urn: string) => {
  const urnParts = urn.split(".");
  if (urnParts.length > 1) {
    return urnParts[1];
  }

  return "";
};
export default findProjectFromUrn;
