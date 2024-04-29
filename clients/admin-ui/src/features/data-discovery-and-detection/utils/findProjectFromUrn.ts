const findProjectFromUrn = (urn: string) => {
  let project = "";
  const urnParts = urn.split(".");
  if (urnParts.length > 1) {
    return urnParts[1];
  }

  return project;
};
export default findProjectFromUrn;
