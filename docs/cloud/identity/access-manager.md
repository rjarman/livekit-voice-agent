---
sidebar_position: 2
---
import CopyPageButton from '@site/src/components/Copy';

# Access Manager  

<CopyPageButton inidividual= {true}/>

The Access Manager section in Blocks Cloud  allows administrators to manage users, their access 
permissions, and login-related actions for the Construct  environment.  

## Configure Access Manager Settings  
1. Go to Core Services → Access Manager . 
2. Click the Configure  button.  
3. The configuration panel includes fields to input the following URLs (typically corresponding to the domain where your project is hosted):  
	a. User Activation  
	b. User Verification  
	c. Account Recovery  
4. Add the following values as needed:  
a. Activation URL Lifetime (mins)  – Defines how long the activation link 
remains valid.  
b. Recovery Account URL Lifetime (mins)  – Defines the validity period for the 
account recovery link.  
5. (Optional) Tick the Logout on Password Change  option if you want users to be 
logged out after changing their password.  
6. Click Change  to save your configuration.  
7. You can experiment with different input values — if needed, click Reset  to revert to 
the previous settings.  
Note:  Once you modify and save new values, they cannot be reset automatically ; you 
need to do it manually . 

## Organizations

The Organization feature allows you to separate users, roles, and resources for different teams, departments, or clients. Doing so provides better control, improved security, and simpler management, making it easier to scale your project as it grows.
A default organization is already created. When users are added through IAM, they are automatically placed under this default organization.

### Configure Multi-Organization
Before adding a new organization, you need to configure the feature:
- Go to Access Manager and, on the Organization tab, click the Config button.
- Enable Multi-Organization.
- Select Creation from Cloud – this allows adding organizations from the cloud.
- Click Save to apply the configuration.

### Add a New Organization
- Go to the Add Organization tab.
- Provide a name for the organization and click Add.
- The new organization will appear in the Organizations list.
- You can rename or disable an organization by clicking the three-dot button next to it.

### Add Users to an Organization
- Enter the organization and invite users to it.
- You can also go to the Users tab and assign a user to another organization from the organization table.
- From any organization’s three-dot menu, you can configure roles and permissions for users in that organization.
When a user invited from an organization logs in to the frontend, they will only see features and resources according to the roles and permissions set for that organization.

:::note
If a user is added to two organizations, they will see an **organization switcher** in the frontend app while logged in, allowing them to switch organizations without logging out.
:::
 
##	Users

### Add a user

1. Go to Core Services → IAM . 
 → The Users  tab will open by default.  
2. Click the Invite User  button.  
3. Enter the user’s First Name, Last Name, and Email Address. 
4. Click Send  to invite the user.  
 → The invited user will receive an email with instructions to log in to Construct .
![Authentication](/img/IAM1.png "Settings")

 
### Search and View User Information  
- Use the search field  to find a specific user by typing their email , first name , or last 
name . 
- The User Table  displays key information such as:  
	- Active/Inactive  status  
	- Number of logins  
	- Assigned roles and permissions  
 
### Edit User Details  

1. Click on a specific user row to open the Edit Page. The Details tab will open by default.
2. Click the Edit User  button to update the user’s name. 
3. Use the three-dot menu  for additional actions:  
	a. Resend Activation  – Sends a new activation email.  
	b. Reset Password  – Sends a password reset email.  
	c. Disable MFA  – Disables multi -factor authentication for that user.  
4. Click Change Image  in the Details  tab to upload or update the user’s profile 
picture. 
5. In the Roles  table, click Assign Role  to add a role (e.g., User , Admin).   
6. Select the desired role’s checkbox.   
	a. You can also use the search bar  if there are many roles.  
7. Click Include  to assign the role. The change will be saved, and the user will receive a notification  to log in to Construct. 
8. In the Permissions table, click Assign Permission. 
9. Use the search box  to find the desired permission by name.  
10. Select the permission and click Include  to assign it. The change will be saved, and the user will receive a notification  to log in to 
Construct . 

:::note  
You can assign a maximum of five permissions to a single user. If additional permissions are required, create a new role  that includes those permissions.  
:::
 
:::info  
Roles and permissions must be configured separately from their dedicated tabs  on 
the IAM landing page.  
:::

### Check User History and Devices  
- Go to the History  or Devices  tabs to view:  
	- Login activity  
	- Session history  
	- Connected devices  
 
## Roles and Permissions

### Using Roles and Permissions with Client Credentials

Blocks Cloud now supports **Roles and Permissions** for controlling access to platform resources. When accessing Blocks Cloud APIs using **client credentials**, it is important to ensure that the credential has a role assigned and that the role includes the correct permissions.

If a required permission is missing, the **access token obtained via client credentials will not include the necessary authorization**, and API calls will fail.

This guide explains how to create and assign the correct permission.


### Scenario

A user attempted to **create a localization key via an API call**. The client credential being used had a role assigned, but the role did **not include the permission required to save localization keys**. Because of this, the token issued through the client credential lacked the required authorization.

Below is an example of the role configuration. As shown, the permission for **saving a localization key** is not present.

![Role without required permission](/img/permissions1.png)

To resolve this issue, the required permission must be created and added to the role.


#### Creating the Required Permission


:::note
For endpoint protection, the resource name should follow the format  
 service::controller::name   
:::


1. Navigate to **Access Manager** from the main menu.
2. Select the **Permissions** tab.
3. Click **Add Permission**.

You will see a screen similar to the following:

![Create permission screen](/img/permissions2.png)

Fill in the fields as follows:

#### Name

Enter a name that you will recognize when assigning it to roles.

Example:

```
localization-key-save
```

#### Type

Select:

```
Endpoint
```

Other available types include:

* **FE Action**
* **Data Protection**

#### Resource

The resource follows the naming convention:

```
service::controller::action
```

For saving a localization key, the resource will be:

```
blocks-localization-api::key::save
```

#### Group

Set the group to:

```
localization
```

#### Description

(Optional) Add a description explaining what this permission allows.

Click **Save** to create the permission.

### Assigning the Permission to a Role

After creating the permission:

1. Navigate to **Access Manager → Roles**.
2. Select the role associated with your **client credential user**.
3. Locate the newly created permission.
4. Add the permission to the role.
5. Save the role configuration.

Once the permission has been added to the role:

* The **client credential token will include the new permission**.
* The API call to **save a localization key** will succeed.
* The application will now have the required authorization to perform the action.

### Key Takeaway

When using **client credentials to access Blocks Cloud APIs**, always ensure:

* The credential has a **role assigned**.
* The role includes **all required permissions for the target API endpoints**.

Missing permissions will result in tokens that **cannot access the required resources**, even if authentication succeeds.


### Steps to Add a Role
1. Go to Core Services → IAM . 
2. By default, the Users  tab will open.  
3. Select the Roles  tab.  
4. Click the Add Role  button.  
5. Enter the following details:  
	a. Role Name  – e.g., Admin  
	b. Slug  – e.g., admin  
	c. Description  – Briefly describe what this role can do.  
6. Click Add  to save the new role.
![Authentication](/img/IAM2.png "Settings")
  

### Search Permissions  

1. Go to Core Services → IAM. 
2. Select the Permissions tab.
3. In the search field , you can:  
	a. Search by permission name.  
	b. Filter by source  using the dropdown (e.g., Built-in or Custom ).  
	c. Filter by type  using the Type  dropdown.  
