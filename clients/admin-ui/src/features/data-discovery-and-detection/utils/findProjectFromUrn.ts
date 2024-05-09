/**
 * findProjectFromUrn returns the 'project' part of the resource urn
 * @param urn urn string for a resource
 * @returns project part of the urn
 * urns structure for reference: ${monitorId}.${projectName}.${datasetName}[...]
 */
const findProjectFromUrn = (urn: string) => {
  const urnParts = urn.split(".");

  // Get the [1] element of the array. The first part is the monitor id. The second part is the project.
  if (urnParts.length > 1) {
    return urnParts[1];
  }

  return "";
};
export default findProjectFromUrn;
