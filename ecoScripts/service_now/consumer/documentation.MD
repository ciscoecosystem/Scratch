## ![alt text](https://raw.githubusercontent.com/ciscoecosystem/Scratch/max-test/ecoScripts/service_now/icon.png "Logo") ServiceNow Consumer

### Overview
Consumer for The ServiceNow Integration

### Behavior

This Consumer shall read Kafka topic for EPG's and Contracts 

### Configuration

This section desribes how to configure a **deployment** of the ServiceNow image. There are three sections of configuration parameters.

#### Connection Parameters

- **ServiceNow URL** is the URL for Service Now. Include HTTP or HTTPS in this field.
- **ServiceNow Username** specifies the login ID to be used each time this deployment runs. \
- **ServiceNow Password** is the login password for the username specified above. ecohub uses this password to connect to ServiceNow every time, this field must be updated if the user's password changes.\
- **Fetch from Duration** is the duration(in days) starting from which the user needs to fetch the data from Service Now.

- **Kafka Hostname or IP** is the Kafka Host/IP(just the ip address and no prefix or suffix), where the producer shall dump data for transformer
- **Kafka Port** specifies the port number for Kafka.
- **Producer Topic** is the kafka topic where the Producer shall dump data.



#### ACI Options

- **Tenant Name** is the tenant under which the integration will push segmentation configuration to.
- **Application Profile** is the application profile for the above tenant under which EPGs will be configured.


