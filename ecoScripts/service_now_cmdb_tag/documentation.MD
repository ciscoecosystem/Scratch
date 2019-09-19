## ![alt text](https://raw.githubusercontent.com/ciscoecosystem/Scratch/max-test/ecoScripts/service_now/icon.png "Logo") ServiceNow

### Overview
The ServiceNow integration ...

### Behavior

#### TODO add more

### Configuration

This section desribes how to configure a **deployment** of the ServiceNow image. There are three sections of configuration parameters.

#### Connection Parameters

- **ServiceNow URL** is the URL for Infoblox. Include HTTP or HTTPS in this field.
- **ServiceNow Username** specifies the login ID to be used each time this deployment runs. \
- **ServiceNow Password** is the login password for the username specified above. ecohub uses this password to connect to ServiceNow every time, this field must be updated if the user's password changes.

#### ACI Options

- **Tenant Name** is the tenant under which the integration will push segmentation configuration to.
- **Application Profile** is the application profile for the above tenant under which EPGs will be configured.

#### *Renaming attributes

Each parameter in the configuration screen that can be enabled/disabled can also be renamed. For example, the user might want to push `Hostname` to Tetration but search for it using a different parameter name (like `Infoblox Hostname` or `Infoblox_Hostname`) in the Tetration user interface.

It is recommended to maintain consistent names (labels) for annotations in Tetration as Tetration considers `Infoblox Hostname` and `Infoblox_Hostname` to be completely different and unrelated fields.
