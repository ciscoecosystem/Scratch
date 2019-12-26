-Kafka validations that topic should exist before consumer is started , prod->trans->consumer configurations should follow this sequence
-On kafka validation earlier the topic was getting created , now the topic shall be created on save click
-Kafka python libraries synced in producer and consumer
-producer avro tested without beam
-consumer avro non tested 
-kafka topic names changed to producer topic and consumer topic
-mapper logic integration and tested without beam
-frammework structure.






# Designing for ecohub

Building a Docker image for use with ecohub requires adherence to a few simple guidelines that will be described in this document. In return, your users get access to a rich user interface where data entry, log parsing, and scheduling work is simplified.

Every ecohub container receives its parameters as environment variables. These parameters include things like username, password, API keys, and which action the container should take. Review the `EnvironmentVariables.md` document in this repository for tips on using environment variables during testing.

Review the `Docker.md` document in this repository for more details on how to design and test a container.

## Feedback via Pigeon

Messages are sent from the container to the ecohub portal simply by printing to `stdout`. ecohub ignores any output sent to the screen other than **pigeon** messages. A **pigeon** is just a JSON structure that mimics an HTTP response sent to `stdout`. It provides a status code (integer), a message (string), and a dictionary/hash of data (if needed). Most pigeons only require a status code and message.

```json
{
    "status_code": 100,
    "message": "Sample of an INFO pigeon",
    "data": {}
}
```

Every pigeon sent by the container is displayed in the log and saved to the ecohub database, so you should provide valuable data without being overly verbose.

### status_code

The integer status code provided in the pigeon has the following meaning:
- 100 = INFO
- 200 = SUCCESS
- 4xx = ERROR

Any pigeon with a status_code of 100 will be displayed in the ecohub log as `INFO` along with its associated message. ecohub will simply log/display these messages and take no action on its contents. The `data` field is ignored for `INFO` messages.

Any pigeon with a status_code of 200 will be considered a *success* and mark the *completion* of the task given to the container. The status and message will be logged. In *some* cases, the `data` portion of the pigeon will also be examined or saved. Consult the actions below for more details.

Any pigeon with a status_code of 4xx (400, 403, 404, etc.) will be considered an *error* and mark the *failed completion* of the task given to the container. The status and message will be logged. 400-level codes do not have to be 400... they can be 403, 404, etc. This allows the script author to return the exact failure code returned by the API action it is trying to access. For example, vCenter might return 403 for a bad password but 404 for an invalid datacenter name. ecohub allows you to specify the exact error status code to help with troubleshooting.

### message

Each pigeon contains a message (string) field. This field should be descriptive yet concise. ecohub does not examine the contents of the message field; it is simply displayed in the log and saved to the database.

### data

At this time, the data portion of the pigeon is only used when the container has to **fetch** information to display to the user in the ecohub portal. The format of this data is critical. Read the `FETCH_ITEMS` section below for more details.

## Actions

Each ecohub Docker image is programmed to do several things. The **ACTION** environment variable is set by ecohub to tell the container which action to take. The most common actions will be detailed in this section. Consult with an ecohub architect if you have to deviate from this list.

The *entrypoint* for Docker containers for ecohub is a script that looks at the **ACTION** environment variable and then launches one more scripts in one or more different languages to perform the specified action.

In most ecohub images, the entrypoint is

```python
python eco_action.py
```

Each image author is free to implement the Docker entrypoint differently as long as they adhere to the requirement of interpreting the **ACTION** environment variable and act accordingly.

### Action: TEST_CONNECTIVITY

The ecohub portal handles testing connectivity to your configured *target* (i.e. Tetration) so individual Docker images don't have to do that. The TEST_CONNECTIVITY  action should validate connectivity to the *specific* integration endpoint (i.e. vCenter Infoblox, Splunk, etc.).

This action should validate that the supplied username and password (or API key) are valid, and if possible, that those credentials have the role or access level required to execute the task that the image was designed to execute.

### Action: RUN_INTEGRATION

This action does what the Docker image was really designed to do. It tells the container to do something like synchronize annotations or export policy. When the user specifies that an ecosystem integration should run every 15 minutes, ecohub will run the Docker container every 15 minutes with the **ACTION** of RUN_INTEGRATION.

### Action: FETCH_ITEMS

The FETCH_ITEMS action is used by ecohub to populate certain fields in the user interface to prevent the user from making typos. For example, the vCenter integration will fetch a list of VMware Datacenter names from vCenter so the user can select from a dropdown list instead of having to type the exact Datacenter name. 

When ecohub runs a container with the FETCH_ITEMS `ACTION` environment variable, it will also specify a `FETCH_TARGET` environment variable so the container knows what data to return. More detail is provided in the JSON sections below, but this **ACTION** *does* use the data field of the pigeon message.

```json
{
    "status_code": 200,
    "message": "Data fetched successfully.",
    "data": {}
}
```

### Action: CUSTOM

At this time, there are no CUSTOM actions defined in any ecohub integrations. Docker images that do not implement the CUSTOM action should return a pigeon like:

```json
{
    "status_code": 404,
    "message": "Requested action CUSTOM not implemented",
    "data": 
        [
            {
                "label": "First label",
                "value": "First value"
            },
            {
                "label": "Second label",
                "value": "Second value"
            }

        ]
}
```

### Undefined actions

If the container does not recognize the **ACTION** environment variable, it should return an error message like

```json
{
    "status_code": 404,
    "message": "Requested action not recognized.",
    "data": {}
}
```

## Docker

Most images for ecohub use `centos:centos7.4.1708` as their base image. Try to follow suit in order to make downloads faster and save ecohub disk space.

Docker images should be posted to `https://hub.docker.com/u/ecohub/` when possible, but the ecohub manifest (described below) allows other locations to be specified.

Docker images can be downloaded and run independently of the ecohub portal, so the environment variables or config files used by the container should be well documented on Docker Hub. In most cases, it's much easier for the end user to employ your container through ecohub than by manually downloading the image.

## Manifest.json

A *manifest* file defines a list of **all** of the integrations available to ecohub. It is a single JSON file stored on github. An ecohub architect will help you define this structure for your integration and add it to the main `manifest.json` file. Because this file contains information about **all** the integrations, that information is high-level. Greater detail exists in a JSON file in the subdirectory where the integration is stored. The structure for one integration looks like:

```json
{
    "name": "vcenter",
    "label": "vCenter Annotations",
    "versions": [
        0.2
    ],
    "latest": 0.2,
    "path": "https://github.com/techBeck03/Scratch/raw/master/ecoScripts/vcenter",
    "icon": "icon.png",
    "tags": "vmware",
    "required_targets": ["tetration"]
},
```
The `label` field represents the friendly name for the *image*. It will be visible to the ecohub user.

The `versions` field defines all available versions of the integration, but ecohub presently only uses the `latest` version.

Your integration will pull information from one source and then push it to one or more *targets*. For example, your integration might pull rich data from an IPAM and push it to Tetration as annotations. ecohub architecture supports different *targets*, but only `tetration` is currently supported for `required_targets`.

## Your integration JSON file

Every integration requires its own JSON manifest file that describes the image details and the ecohub HTML form details. Here is a summary of the JSON format:

```json
{
    "version": "0.2",
    "type": "api",
    "configurable": true,
    "schedulable": true,
    "docker_image": "ecohub/vcenter:v0.2",
    "config_parameters": [ ... ]
}
```

### Image details

The top portion of the JSON structure describe an image.

`version` describes the version number of the integration. This is displayed in a few places within the ecohub web portal, so make sure it is accurate.

`type` is always set to `api` at this time.

`configurable` is a boolean (true/false) that indicates whether or not the integration has parameters that can be specified by the end user. There are no integrations at this time that should use a value other than `true` for this parameter.

`schedulable` is a boolean (true/false) that indicates whether or not a user should be allowed to run this integration on a schedule. Not all integrations should be schedulable. For example, an integration that simply does a file conversion should be run interactively and not on a schedule.

`docker_image` points to the location on Docker Hub where the Docker image can be found.

### Configuration parameters

Will add more detail here as time permits.
