## ![alt text](https://raw.githubusercontent.com/techBeck03/Scratch/runner/ecoScripts/user-management/icon.png "Logo") Lab user management

## Overview
This image can:

- Create a new user
- Delete an existing user
- Reset an existing user's password

## Create new user

The specified user account will be added to:

- Active Directory
- Guacamole
- Tetration (Perseus)
- ACI
- vCenter

If the specified user account already exists in any of the above steps, it will not be modified.

## Delete existing user

The specified user account will be removed from:

- Active Directory
- Guacamole
- Tetration (Perseus)
- ACI

## Reset user password

Password will be reset to random password and email sent.

## Parameters

- **givenName** the user's given (first) name
- **surname** the user's surname (last name)
- **userId** the user's CEC ID (without the @cisco.com part)
