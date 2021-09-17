insert into "DATA_QUALIFIER"(id, `key`, `name`, clause,description) values(1,"identified_data","Identified data","8.3.2","Identified data is data that can unambiguously be associated with a specific person because PII is observable in the information. Guidance on what can be considered as identifiers can be found in ISO/IEC 29100:2011, 4.4.1.
Identified data can be either PII or OPD.");
insert into "DATA_QUALIFIER"(id, `key`, `name`, clause,description) values(2,"pseudonymized_data","Pseudonymized data","8.3.3","Pseudonymized data is data for which all identifiers are substituted by aliases for which the alias assignment is such that it cannot be reversed by reasonable efforts of anyone other than the party that performed them.
This corresponds to data resulting from the process of “pseudonymization” in ISO/IEC 29100:2011, 2.24 and described as “pseudonymous data” in ISO/IEC 29100:2011, 4.4.4.
Pseudonymized data can be either PII or OPD.");
insert into "DATA_QUALIFIER"(id, `key`, `name`, clause,description) values(3,"unlinked_pseudonymized_data","Unlinked pseudonymized data","8.3.4","Unlinked pseudonymized data is data for which all identifiers are erased or substituted by aliases for which the assignment function is erased or irreversible, such that the linkage cannot be re-established by reasonable efforts of anyone including the party that performed them.
Unlinked pseudonymized data can be either PII or OPD.");
insert into "DATA_QUALIFIER"(id, `key`, `name`, clause,description) values(4,"anonymized_data","Anonymized data","8.3.5","Anonymized data is data that is unlinked and for which attributes are altered (e.g. attributes’ values are randomized or generalized) in such a way that there is a reasonable level of confidence that a person cannot be identified, directly or indirectly, by the data alone or in combination with other data.
This corresponds to data defined as “anonymized data” in ISO/IEC 29100:2011, 2.3 and the process defined as “anonymization” in ISO/IEC 29100:2011, 2.2.
For OPD containing information related to the identity of a non-human entity, this can be made into anonymized data by unlinking and alteration of attributes in such a way that the identity of the non- human entity cannot be discovered from the data.");
insert into "DATA_QUALIFIER"(id, `key`, `name`, clause,description) values(5,"aggregated_data","Aggregated data","8.3.6","Aggregated data is statistical data that does not contain individual-level entries and is combined from information about enough different persons that individual-level attributes are not identifiable.
Aggregated data can also be created from information about non-human entities such that individual- level attributes are not identifiable. Such aggregated data can be OPD.");
