-- required for valid org id references
INSERT INTO ORGANIZATION(id, fides_key, description) values (1, "Test", "Reserved for a test account");
INSERT INTO ORGANIZATION(id, fides_key, description) values (3, "Test data", "Reserved for a test taxonomy data");
-- DATA CATEGORIES (see doc/iso_19944_data_categories.csv)--

insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(1,NULL, 1, "customer_content_data","Customer content data","8.2.2","Customer content data is cloud service customer data extended to include similar data objects provided to applications executing locally on the device. Notice that the locally executing application may or may not choose to share that data with the cloud service and yet the data would still fit in this extended definition. This includes content directly created by customers and their users and all data, including all text, sound, software or image files that customers provide to the cloud service, or are provided to the cloud service on behalf of customers, through the capabilities of the service or application. This also includes data that the user intentionally creates through the use of the application or cloud service, such as documents, processed data sets, modified images, recorded sounds, etc. When customer content data local to the device is transmitted to the cloud service, it becomes cloud service customer data.

Specific types of information in customer content data may require explicit use statements by the cloud services provider to the extent that the CSPs are aware of their presence.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(2,1, 1, "credentials","Credentials","8.2.2.2","Data provided by the customer to identify a user to the device, application or cloud service, e.g. passwords, password hints, etc., including biometric data provided for identification. The set of credentials data are a sub-type of customer content data.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(3,1, 1, "customer_contact_lists","Customer contact lists","8.2.2.3","Contact information for people that the cloud service customer provides, or is provided to the service on customers’ behalf, through the capabilities of the service. Customer contact list data is a sub-type of customer content data.
NOTE 1 Cloud services can have a distinction between the cloud service customer and the cloud service users associated with that customer. Cloud service user contact list information provided by the cloud service customer to the cloud service provider is also customer content data.
NOTE 2 Contact information provided solely to support, to administer or to make payment for the service is account or administration contact information (see 8.2.5.2).");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(4,1, 1, "personal_health_data_and_medical_records","Personal health data and medical records","8.2.2.4","Personal health data and medical records are a form of sensitive personal data relating to an individual. The processing of this type of data is heavily regulated in many jurisdictions (e.g. Health Insurance Portability and Accountability Act [HIPAA] in the USA and Personal Information Protection and Electronic Documents Act [PIPEDA] in Canada[20]).");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(5,1, 1, "personal_genetic_data","Personal genetic data","8.2.2.5","Personal genetic data is information about the genetic makeup of an individual (e.g. DNA record).");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(6,1, 1, "personal_biometric_data","Personal biometric data","8.2.2.6","Personal biometric data is encoded data that describes certain characteristics of an individual (e.g. fingerprints, face geometry, iris pattern). For example, the voice prints of the human vocal cords and the posture maintained when walking (as used in Japan's Amended Act on the Protection of Personal Information)[19].");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(7,1, 1, "personal_data_of_children","Personal data of children","8.2.2.7","Personal data relating to children is regarded as sensitive personal data and is subject to more stringent regulations and compliance rules (e.g. General Data Protection Regulation (GDPR)[17] in the European Union).");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(8,1, 1, "political_opinions","Political opinions","8.2.2.8","Political opinions of an individual are personal data that is often subject to special rules and regulations.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(9,1, 1, "financial_details","Financial details","8.2.2.9","Financial details relating to an individual include information about accounts, credit cards, payments and credit history. This is usually regarded as sensitive personal information subject to particular regulations.
Financial details relating to an organization as organizational data include information about tax records such as invoices, accounting documents or documents supporting company registration.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(10,1, 1, "sensor_measurement_data","Sensor measurement data","8.2.2.10","Data that has been obtained from a measurement sensor. Sensor measurement data are typically organizational data and may even exist in mixed dataset; examples are precision farming (helping to monitor and optimize the use of pesticides, nutrients and water), data about temperature or wind speed from wind turbines, data obtained from industrial robots measuring the environmental elements around them.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(11,NULL, 1, "derived_data","Derived data","8.2.3","Derived data is cloud service derived data extended to include similar data objects derived as a user exercises the capabilities of an application executing locally on the device. When the local portion of the data is transmitted to the cloud service, it becomes cloud service derived data.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(12,11, 1, "end_user_identifiable_information","End user identifiable information (EUII)","8.2.3.2","EUII is linkable to the user but is not customer content data. EUII is a sub-type of derived data.
NOTE The term customer, user and tenant are used in the same way as cloud service customer, cloud service user and cloud service tenant in ISO/IEC 17788, with the definition of “customer” extended to include users of applications. In many services, a single individual fulfils all client-side roles, including user, customer and administrator. Customer, when used alone, is assumed to represent all three roles.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(13,12, 1, "telemetry_data","Telemetry data","8.2.3.2.2","This refers to data collected about the capabilities of the product or service. Examples are measurement, performance and operations data. Telemetry data represents information about the capability and its use, with a focus on providing the capabilities of the product or service. Telemetry data may contain information about one or more users and is a sub-type of EUII (see 9.3.2).");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(14,12, 1, "connectivity_data","Connectivity data","8.2.3.2.3","This refers to data that describes the connections and configuration of the devices connected to the service and the network, including device identifiers, (e.g. IP addresses) configuration, settings and performance. Connectivity data is a sub-type of EUII.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(15,12, 1, "observed_usage_of_the_service_capability","Observed usage of the service capability","8.2.3.2.4","This refers to data provided or captured about the users’ interaction with the service or products by the cloud service provider. Captured data includes the records of the users’ preferences and settings for capabilities, the capabilities used and commands provided to the capabilities. Usage data is a sub-type of EUII.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(16,12, 1, "demographic_information","Demographic information","8.2.3.2.5","This refers to data containing demographic information about the end user provided or gathered though use of the capabilities of the application or cloud service. Demographic information is a sub- type of EUII.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(17,12, 1, "profiling_data","Profiling data","8.2.3.2.6","This refers to data provided or acquired about a users’ interests and preferences relating to content, organizations or objects outside of the service, e.g. sports teams, businesses, products, etc. Profiling data is a sub-type of EUII.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(18,12, 1, "content_consumption_data","Content consumption data","8.2.3.2.7","This refers to data about media content that a customer accesses through the capabilities of the service, e.g. TV, video, music, audio or text books, applications and games. Content consumption data is a sub- type of EUII.
NOTE 1 Content consumption data is distinct from usage data collected when the user accesses customer content data.
NOTE 2 Content consumption data is distinct from client-side browsing history collected when accessing information accessed or available on the web.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(19,12, 1, "client_side_browsing_history","Client-side browsing history","8.2.3.2.8","This refers to data in the form of records of the web browsing history when using the capabilities of the applications or cloud services stored in the service or application. Client-side browsing history data is a sub-type of EUII.
NOTE A record of the websites viewed by the user captured by a web browser is an example of a client-side browsing history. In some instances, certain legal obligations may be defined, e.g. UK Investigatory Powers Act 2016[18].");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(20,12, 1, "search_commands_and_queries","Search commands and queries","8.2.3.2.9","This refers to data in the form of records of search commands or queries provided by the user to the service or product. Search commands and queries data are a sub-type of EUII.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(21,12, 1, "user_location","User location","8.2.3.2.10","This refers to data in the form of records of the location of the user within a specified degree of precision. User location data is a sub-type of EUII.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(22,12, 1, "social_data","Social data","8.2.3.2.11","This refers to data in the form of records of interaction between the user, other people and organizations. This includes friends’ lists and information about types of interactions (e.g. likes, dislikes, events, etc.) related to people and/or entities/ businesses which collectively encompass social graph data. Social data is a sub-type of EUII.
NOTE 1 A customer’s own contact information is account or administration contact information (see 8.2.5.2).
NOTE 2 User’s contact list maintained explicitly as such and entered by the cloud service user or customer using the capabilities of the service is called a “customer contact list” and is considered customer content data.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(23,12, 1, "biometric_and_health_data","Biometric and health data","8.2.3.2.12","This refers to data in the form of metrics about the (human) user’s inherent characteristics collected by the application or service’s capabilities. Biometric and health data are a sub-type of EUII. For example, the voice prints of the human vocal cords and the posture maintained when walking (as used in Japan's Amended Act on the Protection of Personal Information)[19].
NOTE 1 Biometric data provided to the system or application for identification areconsidered credentials (see 8.2.2.2).
NOTE 2 Personal biometric data (see 8.2.2.6) entered by the user are customer content data.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(24,12, 1, "end_user_contact_data","End-user contact data","8.2.3.2.13","This refers to data in the form of contact information for a cloud service user. End-user contact data is a sub-type of EUII.
NOTE End-user contact data is different from customer contact lists (see 8.2.2.3) or account or administration contact information (see 8.2.5.2). This data type is captured or generated as the user interacts with the cloudservice.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(25,12, 1, "users_environmental_sensor_data","User’s environmental sensor data","8.2.3.2.14","This refers to data in the form of the physical environment captured by sensors as the user exercises an application or cloud service’s capabilities. User’s environmental sensor data is a sub-type of EUII.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(26,11, 1, "organization_identifiable_information","Organization identifiable information (OII)","8.2.3.3","OII is the data that can be used to identify a particular tenant (general configuration or usage data); is not linkable to a user and does not contain customer content data. This also includes data aggregated from the users of a tenant that is not linkable to the individual user. OII data is a sub-type of derived data.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(27,NULL, 1, "cloud_service_provider_data","Cloud service provider data","8.2.4","Cloud service provider data (as defined in ISO/IEC 17788) is unique to the system and under the control of the cloud service provider.
NOTE Cloud service provider data does not include customer content or derived data.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(28,27, 1,"access_and_authentication_data","Access and authentication data","8.2.4.2","This refers to data used within the cloud service to manage access to other categories of data or capabilities within the service. It includes passwords, security certificates and other authentication- related data. Access control data is a sub-type of cloud service provider data.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(29,27, 1,"operations_data","Operations data","8.2.4.3","This refers to the data which is used for supporting the operation of cloud service providers and system maintenance, such as service logs, technical information about a subscription (e.g. service topology), technical information about a tenant (e.g. customer role name), configuration settings/files.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(30,NULL, 1,"account_data","Account data","8.2.5","Account data is a class of data specific to each cloud service customer that is required to sign up for, purchase or administer the cloud service. This data includes information such as names, addresses, payment information, etc. Account data is generally under the control of the cloud service provider although each cloud service customer usually has the capability to input, read and edit their own account data but not the records of other cloud service customers. See ISO/IEC 19086-1.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(31,30, 1,"account_or_administration_contact_information","Account or administration contact information","8.2.5.2","This refers to the contact information for a customer of an application or cloud service and any cloud service administrators and cloud service business managers designated to administer and control the use of the service. Account or administration contact information is a sub-type of account data.");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key, `name`, clause, description) values(32,30, 1,"payment_instrument_data","Payment instrument data","8.2.5.3","This refers to data provided by the cloud service customer for the purpose of making payment for the services, or to pay for products or services bought through the services. Payment instrument data is a subset of account data.");

-- DATA QUALIFIERS (see doc/iso_19944_data_qualifiers.csv)--
insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key, `name`, clause,description) values(1,NULL,1,"aggregated_data","Aggregated data","8.3.6","Aggregated data is statistical data that does not contain individual-level entries and is combined from information about enough different persons that individual-level attributes are not identifiable.
Aggregated data can also be created from information about non-human entities such that individual- level attributes are not identifiable. Such aggregated data can be OPD.");
insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key, `name`, clause,description) values(2,1,1,"anonymized_data","Anonymized data","8.3.5","Anonymized data is data that is unlinked and for which attributes are altered (e.g. attributes’ values are randomized or generalized) in such a way that there is a reasonable level of confidence that a person cannot be identified, directly or indirectly, by the data alone or in combination with other data.
This corresponds to data defined as “anonymized data” in ISO/IEC 29100:2011, 2.3 and the process defined as “anonymization” in ISO/IEC 29100:2011, 2.2.
For OPD containing information related to the identity of a non-human entity, this can be made into anonymized data by unlinking and alteration of attributes in such a way that the identity of the non- human entity cannot be discovered from the data.");
insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key, `name`, clause,description) values(3,2,1,"unlinked_pseudonymized_data","Unlinked pseudonymized data","8.3.4","Unlinked pseudonymized data is data for which all identifiers are erased or substituted by aliases for which the assignment function is erased or irreversible, such that the linkage cannot be re-established by reasonable efforts of anyone including the party that performed them.
Unlinked pseudonymized data can be either PII or OPD.");
insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key, `name`, clause,description) values(4,3,1,"pseudonymized_data","Pseudonymized data","8.3.3","Pseudonymized data is data for which all identifiers are substituted by aliases for which the alias assignment is such that it cannot be reversed by reasonable efforts of anyone other than the party that performed them.
This corresponds to data resulting from the process of “pseudonymization” in ISO/IEC 29100:2011, 2.24 and described as “pseudonymous data” in ISO/IEC 29100:2011, 4.4.4.
Pseudonymized data can be either PII or OPD.");
insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key, `name`, clause,description) values(5,4,1,"identified_data","Identified data","8.3.2","Identified data is data that can unambiguously be associated with a specific person because PII is observable in the information. Guidance on what can be considered as identifiers can be found in ISO/IEC 29100:2011, 4.4.1.
Identified data can be either PII or OPD.");

-- DATA USE (see doc/iso_19944_data_use_categories.csv)--

insert into DATA_USE(id,parent_id, organization_id, fides_key, `name`, clause,description) values(1,NULL,1,"provide","Provide","9.3.2","Provide means the use of specified data categories:
— from the source scope by an applications and services scope to provide and protect the current
capabilities of a results scope;
— to communicate with the customer about the status and availability of the current capabilities of the result scope;
— including providing support for the result scope and to protect at a minimum the specified data category from the source scope.
Provide can include the use of specified data categories to protect the rights and property of the cloud service provider and to prevent loss of life or serious injury to anyone. For example:
Example 1:
This cloud service uses derived data only to provide the cloud services defined in the cloud services agreement.
NOTE 1 In this example, use of derived data is restricted to provide the service contracted for in the cloud service agreement, including operational support system (OSS) and business support system (BSS) for exclusively those services. In the case of a single contracted service, “This application” or “This service” can also define the scope (see 9.4.2.3).
NOTE 2 The data use statement structure used in this example is described in Clause 10.
In the case where a single scope is involved, provide also means to protect the customer content data that exists within this scope and to provide and communicate with the customer about the status and availability of the current capabilities of this scope.");
insert into DATA_USE(id,parent_id, organization_id, fides_key, `name`, clause,description) values(2,1,1,"provide_operational_support_for_contracted_service","Provide operational support for contracted service","9.3.2.2","This usage is related to the acquisition, processing and storage of data about the usage of a cloud service (derived data) contracted by a specific cloud service customer in order to operate and protect the systems and processes necessary for the provision of this cloud service. This includes:
— service usage data to be used for capacity planning;
— monitoring of user behaviour to identify potential attackers and to perform forensic analyses;
— logging data for system and network maintenance and optimization;
— correlation of service usage data and system events for fault tracking and root cause analysis.");
insert into DATA_USE(id,parent_id, organization_id, fides_key, `name`, clause,description) values(3,1,1,"improvement_of_business_support_for_contracted_service","Improvement of business support for contracted service","9.3.2.3","This usage is related to acquisition, processing and storage of data on the usage of contracted services (derived data) being used for business support related to this service. This includes:
— evaluation of service usage data to determine user preference about use of the current capabilities of the services contracted for in the SLA;
— financial controlling, budgeting and resource planning.");
insert into DATA_USE(id,parent_id, organization_id, fides_key, `name`, clause,description) values(4,NULL,1,"improve","Improve","9.3.3","Improve means to use specified data categories from the source scope to improve or increase the quality of the existing functional capabilities of the result scope.
Improve can be used with a single scope. In this case, it means that data acquired or created by applications and services in the scope is used to improve the existing functional capabilities and to add new capabilities to the scope, available to all users.");
insert into DATA_USE(id,parent_id, organization_id, fides_key, `name`, clause,description) values(5,NULL,1,"personalize","Personalize","9.3.4","Personalize means to use specified data categories from the source scope to change the presentation of the capabilities of the result scope or to change the selection and presentation of data or promotions accessed through the capabilities of the result scope to be specific to the user, based on information about the user gathered by applications and services in the source scope.
The same changes may apply to multiple users, for example all users of a particular customer or all of the users sharing common characteristics may receive the same changes.
Personalize can be used with a single scope, in which case data acquired or created by applications and services in the provided scope is used to change the presentation of the capabilities of that scope or to change the selection and presentation of content by the applications and services in the scope to be specific to a user.
Example 2:
Customer content data from this service is used to personalize cloud service provider’s services outside of the services listed in the cloud service agreement.
Example 2 describes personalizing of services unrelated to the contracted service based on usage of customer data regarding the contracted service to improve services that are not contracted by the customer. Since data on service usage provide information on the preferences of the cloud service user, their collection and correlation with other data sources can be used to trigger, maintain and improve a large variety of supplementary services. This includes use of other services, not explicitly contracted by user, as listed in the following examples.
— The usage of location data from mobile devices to provide location-based services to the user according to his or her past behaviour.
— Add-on advertisement services based on search engine queries, combined with data on past user behaviour.
NOTE The data use statement structure used in this example is described in Clause 10.");
insert into DATA_USE(id,parent_id, organization_id, fides_key, `name`, clause,description) values(6,NULL,1,"offer_upgrades_or_upsell","Offer upgrades or upsell","9.3.5","Offer upgrades or upsell means to use specified data categories from the source scope to offer to the customer increased capacity or resources for the capabilities of the result scope or new capabilities currently outside of the result, in exchange for compensation.
The source of new capabilities may be defined as a scope. For example: “...to upsell capabilities to customers from any of our products and services.”
Offer upgrades or upsell requires the definition of the person or group of people who are the target audience.");
insert into DATA_USE(id,parent_id, organization_id, fides_key, `name`, clause,description) values(7,NULL,1,"market_advertise_or_promote","Market/advertise/promote","9.3.6","Market/advertise/promote means to promote specified products and services to users or customers of a results scope based on data from the source scope.
Promotion is targeted at an individual or a group of individuals. Market/advertise/promote requires the definition of the person or group of people who are the target audience.");
insert into DATA_USE(id,parent_id, organization_id, fides_key, `name`, clause,description) values(8,7,1,"promote_based_on_contextual_information","Promote based on contextual information","9.3.6.2","Market/advertise/promote based on data derived from the use of the current capability or based on the services and application scope, without the use of data derived from the user’s prior use of the services.");
insert into DATA_USE(id,parent_id, organization_id, fides_key, `name`, clause,description) values(9,7,1,"promote_based_on_personalization","Promote based on personalization","9.3.6.3","Use specified data categories from the source scope to change the content of a promotion to the result scope to be specific to the user. The same content may be presented to multiple users, for example, all users of a customer or all of the users sharing a profile may receive the same changes.");
insert into DATA_USE(id,parent_id, organization_id, fides_key, `name`, clause,description) values(10,NULL,1,"share","Share","9.3.7","Share means to transfer specified data categories from the source scope to an entity other than the cloud service provider of the source scope. This entity may be defined as the cloud service provider of a result scope, e.g. “... share pseudonymized operations data with cloud service providers of similar commercial cloud services.”
Example 3:
This service shares customer content data with third parties.
This example is a poor use statement in that it does not provide clarity of the purpose for which the data are being shared nor of the extent of the data being shared. CSPs are strongly encouraged to provide as much detail as possible in data use statements so that it is clear to the CSC what is being done with which data.
NOTE 1 The data use statement structure used in this example is described in Clause 10.
Cloud service providers should specify a purpose for sharing data by including a use definition. Example 4:
This service shares payment instrument data with third-party partners and data processors to provide the cloud service.
This example adds some clarity to how retail services provide payment instrument data (i.e. credit card information) to third parties, for example for billing purposes, for the specific purpose of providing the service.
NOTE 2 The data use statement structure used in this example is described in Clause 10.
Cloud service providers should use scope characteristics (see 9.4.3) for the source scope and for the
receiving entity or result scope to further specify the sharing.
Cloud service providers should include a description of the network connection between scopes (see
9.4.4) following the statement structure described in data sharing (see 10.2.9).");
insert into DATA_USE(id,parent_id, organization_id, fides_key, `name`, clause,description) values(11,10,1,"share_when_required_to_provide_the_service","Share when required to provide the service","9.3.7.2","There are conditions where CSP are required to share data: by contract, applicable laws and regulations, resulting in the transfer of specified data categories to third parties to provide the service. This can include sharing data to comply with applicable law or respond to valid legal processes from competent authorities, including from law enforcement or other government agencies and providing data to law enforcement to protect the service and uphold the terms governing the use of the service. This use statement only includes the use of data provided by the third parties to provide the services in the scope.");
insert into DATA_USE(id,parent_id, organization_id, fides_key, `name`, clause,description) values(12,NULL,1,"collect","Collect","9.3.8","Collect includes collecting, preparing, pre-processing and storing specified data categories from the source scope in preparation for other uses such as training machine learning algorithms.");
insert into DATA_USE(id,parent_id, organization_id, fides_key, `name`, clause,description) values(13,NULL,1,"train_ai_system","Train (AI system)","9.3.9","Use the specified data categories from the source scope to train, retrain or test an artificial intelligence (AI) system. The AI system can use machine learning technologies, or it can use other technologies.
Cloud service providers describing the use of data to train AI systems should include a statement addressing the extent to which individuals are directly identified in the resulting AI system. The data identification qualifiers in 8.3 could be used as the basis for this description. If there is PII in the resulting AI system, then additional statements are likely required, e.g. about data retention periods.");

insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key, `name`, description) values (1,NULL,1,'anonymous_user','Anonymous User','');
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key, `name`, description) values (2,NULL,1, 'citizen_voter', 'Citizen / Voter','');
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key, `name`, description) values (3,NULL,1, 'commuter', 'Commuter','');
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key, `name`, description) values (4,NULL,1, 'consultant', 'Consultant','');
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key, `name`, description) values (5,NULL,1, 'customer', 'Customer','');
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key, `name`, description) values (6,NULL,1, 'employee', 'Employee','');
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key, `name`, description) values (7,NULL,1, 'job_applicant', 'Job Applicant','');
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key, `name`, description) values (8,NULL,1, 'next_of_kin', 'Next of Kin','');
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key, `name`, description) values (9,NULL,1, 'passenger', 'Passenger','');
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key, `name`, description) values (10,NULL,1, 'patient', 'Patient','');
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key, `name`, description) values (11,NULL,1, 'prospect', 'Prospect','');
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key, `name`, description) values (12,NULL,1, 'shareholder', 'Shareholder','');
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key, `name`, description) values (13,NULL,1, 'supplier_vendor', 'Supplier / Vendor','');
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key, `name`, description) values (14,NULL,1, 'trainee', 'Trainee','');
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key, `name`, description) values (15,NULL,1,'visitor', 'Visitor','');


-- some trees at id 0 for taxonomy testing:

insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key) values(33,NULL, 3, "ca");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key) values(34,33, 3, "ca1");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key) values(35,34, 3, "ca11");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key) values(36,34, 3, "ca12");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key) values(37,33, 3, "ca2");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key) values(38,37, 3, "ca21");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key) values(39,37, 3, "ca22");

insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key) values(40,NULL, 3, "cb");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key) values(41,40, 3, "cb1");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key) values(42,41, 3, "cb11");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key) values(43,41, 3, "cb12");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key) values(44,40, 3, "cb2");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key) values(45,44, 3, "cb21");
insert into DATA_CATEGORY(id, parent_id, organization_id, fides_key) values(46,44, 3, "cb22");

insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key) values(6,NULL, 3, "qa");
insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key) values(7,6, 3, "qa1");
insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key) values(8,7, 3, "qa11");
insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key) values(9,7, 3, "qa12");
insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key) values(10,6, 3, "qa2");
insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key) values(11,10, 3, "qa21");
insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key) values(12,10, 3, "qa22");

insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key) values(13,NULL, 3, "qb");
insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key) values(14,13, 3, "qb1");
insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key) values(15,14, 3, "qb11");
insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key) values(16,14, 3, "qb12");
insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key) values(17,13, 3, "qb2");
insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key) values(18,17, 3, "qb21");
insert into DATA_QUALIFIER(id, parent_id, organization_id, fides_key) values(19,17, 3, "qb22");

insert into DATA_USE(id, parent_id, organization_id, fides_key) values(14,NULL, 3, "ua");
insert into DATA_USE(id, parent_id, organization_id, fides_key) values(15,14, 3, "ua1");
insert into DATA_USE(id, parent_id, organization_id, fides_key) values(16,15, 3, "ua11");
insert into DATA_USE(id, parent_id, organization_id, fides_key) values(17,15, 3, "ua12");
insert into DATA_USE(id, parent_id, organization_id, fides_key) values(18,14, 3, "ua2");
insert into DATA_USE(id, parent_id, organization_id, fides_key) values(19,18, 3, "ua21");
insert into DATA_USE(id, parent_id, organization_id, fides_key) values(20,18, 3, "ua22");

insert into DATA_USE(id, parent_id, organization_id, fides_key) values(21,NULL, 3, "ub");
insert into DATA_USE(id, parent_id, organization_id, fides_key) values(22,21, 3, "ub1");
insert into DATA_USE(id, parent_id, organization_id, fides_key) values(23,22, 3, "ub11");
insert into DATA_USE(id, parent_id, organization_id, fides_key) values(24,22, 3, "ub12");
insert into DATA_USE(id, parent_id, organization_id, fides_key) values(25,21, 3, "ub2");
insert into DATA_USE(id, parent_id, organization_id, fides_key) values(26,25, 3, "ub21");
insert into DATA_USE(id, parent_id, organization_id, fides_key) values(27,25, 3, "ub22");

insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key) values(16,NULL, 3, "sa");
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key) values(17,16, 3, "sa1");
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key) values(18,17, 3, "sa11");
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key) values(19,17, 3, "sa12");
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key) values(20,16, 3, "sa2");
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key) values(21,20, 3, "sa21");
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key) values(22,20, 3, "sa22");

insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key) values(23,NULL, 3, "sb");
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key) values(24,23, 3, "sb1");
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key) values(25,24, 3, "sb11");
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key) values(26,24, 3, "sb12");
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key) values(27,23, 3, "sb2");
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key) values(28,27, 3, "sb21");
insert into DATA_SUBJECT(id, parent_id, organization_id, fides_key) values(29,27, 3, "sb22");
