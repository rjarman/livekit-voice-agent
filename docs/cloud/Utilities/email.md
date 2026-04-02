---
sidebar_position: 1
---

import CopyPageButton from '@site/src/components/Copy';

# Email

<CopyPageButton inidividual= {true}/>

## Overview 

The Email service in Blocks Cloud enables administrators to manage and customize all email communications used across the Construct environment. It provides tools to configure mail servers, create and edit email templates. With flexible configuration options, a visual template editor, and built-in testing features, the Email service ensures teams can design branded, reliable, and secure email workflows that integrate seamlessly with their applications.

## Set Email Configuration

1. Go to Core Services → Email. The Templates  tab will open by default.  
2. Click the Configure  button. This will take you to the Email Configuration  page, where a default configuration is already set.  
3. To view the existing setup, click the Edit  button next to the default configuration.  
4. To create a new configuration, click Add Configuration. 
5. Enter the required information such as:  
	a. Host details  
	b. Port  
	c. Username and password  
6. Check the Enable SSL  option if your mail server requires a secure connection.  
7. Click Save  to create the new configuration.

![Email](/img/Email1.png "Email Configuration")


## Add a Template  
1. Go to Core Services → Email. The Templates  tab will open by default.  
2. Click the Add Template  button. This opens the About the Template  page.  
3. Fill in the required details:  
	a. Template Name  
	b. Email Configuration (select from dropdown; the default configuration will 
	always be available)  
	c. Language  
	d. Subject  
4. Click Save and Continue. This will open the Template Editor  page.  
5. Use the playground editor to design your email:  
	a. Drag and drop components from the Content  sidebar.  
	b. Adjust styles (color, size, alignment, etc.) from the Settings  bar.  
	c. Switch to Segment View  to structure your layout easily.  
6. Click Preview  to see how the email will appear to recipients.  
7. Click Save  to store your template. Once saved, you’ll see buttons to Send Test Email  or Edit Template Details. 
8. Click Send Test Email  to send a sample email to the address linked with your Blocks Cloud account.
9. Click Yes  to confirm.

![Email](/img/Email2.png "Email Template")

:::note
Emails need to be triggered from the code when a new template is created.  
:::

## View and Manage Templates  
1. Go to Core Services → Email. The Templates  tab displays a table of all email templates.  
2. The table includes:  
	a. Predefined templates for frequent use  
	b. Custom templates created by users  
3. Use the search field to find templates by name.  
4. Filter templates using:  
	a. Configuration  dropdown (select preferred configuration)  
	b. Language  dropdown  
5. To edit a template, click on the desired row. This opens the Edit Template  page, where you can update template details or send a 
test email.  

## Clone a Template  
To clone an existing email template:  
1. Click the three-dot menu  beside the desired email template.  
2. Select Clone Template . 
3. Click Yes  to confirm.

:::note
To migrate from one environment to another environment, please follow [Environment Migration](https://docs.seliseblocks.com/cloud/getting-started#environment-selection)
:::
