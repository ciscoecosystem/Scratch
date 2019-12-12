## ![alt text](https://raw.githubusercontent.com/ciscoecosystem/Scratch/max-test/ecoScripts/service_now/icon.png "Logo") ServiceNow Consumer

### Overview
Consumer for The ServiceNow Integration

### Behavior

This Consumer shall read Kafka topic for EPG's and Contracts and push it in ACI

### Configuration

This section desribes how to configure a **deployment** of the ServiceNow image. There are three sections of configuration parameters.

#### Connection Parameters

- **Kafka Hostname or IP** is the Kafka Host/IP(just the ip address and no prefix or suffix), where the producer shall dump data for transformer
- **Kafka Port** specifies the port number for Kafka.
- **Consumer Topic** is the kafka topic from where consumer shall read the data which was dumped by transformer.

#### ACI Options

- **Tenant Name** is the tenant under which the integration will push segmentation configuration to.
- **Application Profile** is the application profile for the above tenant under which EPGs and Contracts will be configured.


