## ![alt text](https://raw.githubusercontent.com/ciscoecosystem/Scratch/max-test/ecoScripts/service_now/icon.png "Logo") ServiceNow Transformer

### Overview
Transformer for The ServiceNow Integration

### Behavior

This transformer shall take the data of EP's,Reltypes and Rels from producer topic and forms EPG's and Contracts and pushes to consumer topic.

### Configuration

This section desribes how to configure a **deployment** of the Transformer image. There should be a jar file in the Image folder before creating build once this code is pulled on server. This jar file should have the code for transformer which should be Apache beam transformations pertaining to the usecase.

### Connection Parameters

#### Kafka Options

- **Kafka Hostname or IP** is the Kafka Host/IP(just the ip address and no prefix or suffix), where the producer shall dump data for transformer.
- **Kafka Port** specifies the port number for Kafka.
- **Producer Topic** is the kafka topic where the Producer shall dump data and Transformer shall read it.
- **Consumer Topic** is the kafka topic where the Transformer shall dump data and Consumer shall read it.

#### Elasticsearch Options

- **ES Hostname or IP** is the Elasticsearch Host/IP(just the ip address and no prefix or suffix), which shall be used by Transformer to create indices required for the transformations.
- **ES Port** specifies the port number for Elasticsearch.

#### Flink Options

- **Flink Hostname or IP** is the Flink Host/IP(just the ip address and no prefix or suffix), which shall be served as Runner environment for Transformer jobs.
- **Flink Port** specifies the port number for Flink.


