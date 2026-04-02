---
slug: /getting-started
sidebar_position: 2
---

# Getting Started

This guide walks you through each of these steps to help you quickly set up and manage your projects in Blocks Cloud. To get started, please go to the [Cloud Portal](https://cloud.seliseblocks.com).

## User Registration

### Signing Up with Email

Users can create an account using their email address.
Enter the required details such as **name**, **email**, and **password**.
A verification email will be sent — clicking **Verify Email** activates the account and grants access to the Blocks Cloud Console.

### Signing Up with SSO

Users can alternatively register using supported Single Sign-On (SSO) providers.
Blocks currently supports:

- GitHub
- Google
- Microsoft
- LinkedIn
- X

After selecting an SSO option, the user is authenticated through the provider, and the Blocks Cloud account is created automatically.

## Blocks Cloud Console

The Console section introduces you to the core workflow for creating and managing projects within the Blocks Cloud Console. From here, you can view all your projects at a glance, create new ones, connect repositories, and configure deployment environments — all in one place.

See all your projects in the Blocks Cloud Console. Click on the Main logo on the top left to navigate to the Project Settings Menu page.

:::note
You can create a maximum of 10 projects
:::

## Project Creation

### Initiating a new project

Click on "Add Project" to create a new project. You will be taken to a new page. Enter a project name here and accept the terms and conditions.

### Adding a Repository

There is an optional step to add a repository. This step is important for users who wish to deploy their project using the Blocks Cloud platform. The user connects to GitHub via SSO. Once connected, the available repositories are listed. Users can select a repository and add it to the project.

![Hosting](/img/hosting1.jpg "Hosting & observability")

:::danger[Take care]

Make sure you have a corresponding branch in your repository if you want to deploy using Blocks Cloud. See the table below for the proper branch names.

:::

:::info
Access to the chosen version control system (e.g. GitHub) can be revoked in the "Select Repository" modal by clicking on "Edit your GitHub Permissions"
:::

### Environment Selection

The system prompts the user to select the number of required environments. The user selects a single environment for this demo. Submission leads to final project creation with the chosen environment.

If users wish to deploy using Blocks Cloud, corresponding branches must also exist. For example, in order to deploy in development, the system will automatically look for the “dev” branch. The following is a list of supported environments and their corresponding branches:

| Environment | Branch      |
| ----------- | ----------- |
| Development | dev         |
| Testing     | test        |
| Staging     | stg         |
| IAT         | iat         |
| UAT         | uat         |
| Prod Shadow | prod-shadow |
| Pre-Prod    | pre-prod    |
| Production  | main        |

## Project Settings Menu

The Project Settings Menu is the central location for managing all project-level configuration and administrative controls. It is accessible from the sidebar, which exposes four main sections:

- Environments
- People
- Repositories
- Settings

### Environments

The Environments section allows users to access and manage the different environments within a project. Access rights and capabilities differ depending on the user's role.

#### User Roles

There are two types of users within a project:

- **Owner** — The user who created the project. The project creator automatically becomes the Owner. Only one Owner can exist at a time. Ownership can be transferred to another accepted project member at any point.
- **General User** — All other project members who have been invited and accepted their invitation.

#### Environment Access Control

The Owner has full control over environments:

- Can view all existing environments.
- Can create new environments.
- Can manage (grant or revoke) environment access for other users.
- Cannot edit their own environment access — this is by design to prevent accidental lockout. The Owner has inherent access to all environments they create.

General Users have restricted access:

- Can only access environments they have been explicitly granted permission to.
- Cannot create new environments.
- Cannot modify environment permissions for themselves or others.

#### Environment Migration

A Migration Feature allows services to be moved from a source environment to a destination environment. Migration can be performed by all users, regardless of role, as long as they have access to the relevant environments.

You can migrate data from one environment to another. On the Project Settings Menu page, click **Start Migration** to go to the migration page.

![Environment Migration](/img/environmentmigration1.png "Environment Migration")

1. Select the source environment from the dropdown on the left and the target environment on the right.
2. Select the services you want to migrate.
3. Enable **Overwrite Data** if you want to overwrite existing data in the target environment.
4. Click **Continue** at the bottom to go to the Review page. Review your changes here and start the migration!

:::info
Not all the data in any given service will be migrated. Each service allows its own set of data that can be migrated.
:::

**Localization-specific behavior:**

- If the IDs are the same in both environments and Overwrite Data is enabled, existing keys in the target environment will be overwritten.
- New keys from the source environment will be added to the target environment, while keys that exist in the target environment but not in the source environment will remain unchanged.

#### Environment Switcher

Once inside an environment, users can navigate between environments efficiently using the Environment Switcher, without needing to return to the home screen or manually navigate back through the project menu.

The Environment Switcher provides:

- A quick-access list to switch directly between available environments.
- A "View All" option that redirects to the full Environments section inside the project, giving a complete overview of all environments.

### People & Project Membership

The People section is where all project members and pending invitations are managed. It gives the owner full control over who has access to the project and what environments they can work in. General users can view member profiles but cannot make changes.

#### Members Table

The People section displays a table listing all project members and invited users. The table includes the following columns:

- **Name** — The user's full name.
- **Email** — The user's registered email address.
- **Environments** — The environments the user currently has access to.
- **Actions Menu (⋮)** — A contextual action button that adapts based on the user's current invitation or membership status (see below).

#### Invitation Status & Actions

The actions available in the (⋮) menu update dynamically based on each user's current status:

- **Pending** — An invitation has been sent but not yet accepted. The Owner can resend the invitation.
- **Inactive (Not Registered)** — The invited user has not yet registered on the platform. The Owner can resend the activation email.
- **Accepted** — The user has accepted the invitation and is an active project member. The Owner can transfer project ownership to this user.

#### User Profile View

Any project member can open another user's profile by clicking on their entry in the table. The profile view is organized into three tabs:

**Details**

Displays general account information including name, email, role, last login, browser used, and sign-up date.

**Environments**

Shows the list of environments the user has access to. Only the Owner can grant or remove environment access from this view. The Owner's own access cannot be modified here — they inherently have access to all environments within the project.

**Devices**

Displays the devices from which the user has logged into the platform.

#### Owner Privileges & Restrictions

The Owner is the only user who can perform the following actions:

- Send invitations to new users and assign environment access as part of the invitation.
- Modify a user's environment access at any time after they have joined.
- Resend invitations or activation emails.
- Transfer ownership of the project to another accepted member.

#### Transferring Ownership

The current Owner can transfer the project to another accepted member. Once transferred:

- The selected user immediately becomes the new Owner and gains all owner-level privileges.
- The previous Owner loses owner-level privileges and becomes a general user.
- Only one Owner can exist at a time. Transfers are final unless the new Owner transfers it back.

### Repositories

The Repositories section allows users to connect and manage code repositories within a project. Adding a repository is required before deployment can take place.

Repositories are used to:

- Support deployment workflows.
- Enable integration with Construct.
- Deploy Construct applications.
- Deploy React-based frontend applications.

### Settings

The Settings section displays project-level configuration details. It is visible to all project members, but only the Owner can make changes.

Information displayed in Settings includes:

- Project Name
- Additional project metadata
- Created On (e.g., 01/03/2026, 16:45)
- Plan (e.g., Free)

Only the Owner can edit the project name and other configuration fields. All other users have read-only access to this section.

## Deleting a Project

In order to delete a project, you must delete the environments within a project first. If you have only one environment, deleting it will delete the project as well.

To delete a project:

1. Select the desired project you want to delete from the console home page
2. Select the environment that you want to delete
3. Navigate to the Environment Overview page by selecting it on the navigation menu on the left
4. Click on the delete button in this page
