---
sidebar_position: 2
---

import CopyPageButton from '@site/src/components/Copy';

# Notification

<CopyPageButton inidividual= {true}/>

## Overview

The Notification Service enables real-time and persistent communication within your application by delivering alerts to users based on predefined configurations. It allows teams to control how, when, and to whom notifications are sent. Using configurable receiver types and a selectable delivery channel (currently SignalR), the service supports system-wide broadcasts, user-specific alerts, and filtered targeting based on roles or conditions.
Once configured, notifications can be triggered by backend events and displayed instantly in the frontend—optionally stored as persistent alerts that appear under the bell icon.
This feature provides a flexible and centralized way to manage in-app notifications, ensuring users receive the right information at the right time.

## Add a Notification Configuration

1. Go to Core Services → Notification . 
2. Click the Add Configuration  button.  
3. Enter a Name  for the configuration (e.g., User Activity Alert ). 
4. Select the Channel to Notify  — currently, the available option is SignalR . 
5. Choose the Notification Type  from the dropdown.  
6. Enter the Notify Method  (e.g., language import ). 
7. Check Enable Persistence  if you want the notification to be stored for future 
reference.  
 → Persistent notifications will appear under the bell icon  in the UI.  
8. Click Save  to create the configuration.  

![Hosting](/img/notification.jpg "Hosting & observability")

**Available Notification Types:**  
| Type                       | Meaning                                                                   |
|----------------------------|---------------------------------------------------------------------------|
| NoReceiverType             | No receiver defined; notification not sent to anyone                      |
| BroadcastReceiverType      | Sent to all users in the environment or system                            |
| UserSpecificReceiverType     | Sent to specific user(s) only                                             |
| FilterSpecificReceiverType | Sent to users matching certain filters or conditions (e.g. role, project) |

## Edit or Delete a Notification Configuration  

1. Go to Core Services → Notification . 
2. From the Notification Configuration  table, click the three-dot menu  beside your 
desired configuration.  
3. Select Edit  to modify settings (same fields as in Add Configuration).  
4. Select Delete  to permanently remove the configuration.

View Swagger link by clicking API Docs . 

:::note

Currently, the only supported notification channel is SignalR. For notifications to be delivered correctly, the user must select a receiver type otherwise, the notification will not be sent. Additionally, the frontend must include a matching method to the one specified in the notification method. This enables proper subscription to the notification via the front-end interface. 

Multiple notifications can be added by repeating the configuration process. Once configurations are saved, a list view displays all existing notifications. From this list, users can edit or delete any previously created notification. This setup ensures flexibility in managing real-time and persistent notifications. 

:::

