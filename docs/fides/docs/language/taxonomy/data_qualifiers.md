# Data Qualifiers Reference

Data Qualifiers describe the degree of identification of the given data. Think of this as a spectrum: on one end is completely anonymous data, i.e. it is impossible to identify an individual from it, and on the other end is data that specifically identifies an individual. 

!!! Note "Extensibility and Interopability"
    Data Qualifiers in Fides are designed to support common privacy regulations and standards out of the box, these include GDPR, CCPA, LGPD and ISO 19944. 
    
    You can extend the taxonomy to support your system needs. If you do this, we recommend extending from the existing categories to ensure interopability inside and outside your organization.

    If you have suggestions for core categories that should ship with the taxonomy, please submit your requests [here](https://github.com/ethyca/fides/issues)


## Data Qualifiers

Data Qualifiers are arranged as a series of nested subcategories, going from least identifiable (aggregated) to most identifiable (identified).

| Label                    | Parent Key                                                              | Description                                                                                                                                                                                                        |
| ---                      | ---                                                                     | ---                                                                                                                                                                                                                |
| `aggregated`             | `-`                                                                     | Statistical data that does not contain individually identifying information but includes information about groups of individuals that renders individual identification impossible.                                |
| `anonymized`             | `anonymized`                                                            | Data where all attributes have been sufficiently altered that the individaul cannot be reidentified by this data or in combination with other datasets.                                                            |
| `unlinked_pseudonymized` | `aggregated.anonymized`                                                 | Data for which all identifiers have been substituted with unrelated values and linkages broken such that it may not be reversed, even by the party that performed the pseudonymization.                            |
| `pseudonymized`          | `aggregated.anonymized.unlinked_pseudonymized`                          | Data for which all identifiers have been substituted with unrelated values, rendering the individual unidentifiable and cannot be reasonably reversed other than by the party that performed the pseudonymization. |
| `identified`             | `aggregated.anonymized.unlinked_pseudonymized.pseudonymized.identified` | Data that directly identifies an individual.                                                                                                                                                                       |

