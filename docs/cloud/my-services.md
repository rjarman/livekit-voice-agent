---
slug: /my-services
sidebar_position: 3
---
import CopyPageButton from '@site/src/components/Copy';

# My Services

<CopyPageButton inidividual= {true}/>

## Overview

My Services allow you to register and manage your services within **Blocks Cloud**. Once a service is registered, you can begin collecting logs and traces for it.

**Key Features**

- High Performance - Automatic batching reduces network overhead and improves throughput
- Automatic Retry Logic - Exponential backoff with configurable retry attempts
- Failed Batch Queue - Prevents data loss during transient failures
- Thread-Safe - Built with concurrent collections for multi-threaded environments
- OpenTelemetry Integration - Industry-standard distributed tracing support
- Multi-Tenant Support - Automatic tenant isolation via baggage propagation
- Zero Dependencies on Logging Frameworks - Works independently or alongside Serilog, NLog, etc.
- Azure Service Bus Native - Optimized for Azure Service Bus Topics and Subscriptions
- Easy Integration - Simple dependency injection set up with minimal configuration

## Register a Service

1. Navigate to **My Services**.
2. Click **Register Service**.

  ![Managed Services](/img/manageservices2.png "Managed Services")  

 
3. Fill in the required details:
   * **Service Name:** Enter the name of the service.
   * **Tags:** Add relevant tags to categorize the service.
   * **Description:** Provide a brief description of the service.
4. Click **Save** to register the service.
5. After registering, connect your application to the service using the provided **NuGet package**. Once connected, you can view logs and traces for that service directly in Blocks Cloud.

To set up My Services with your backend project, install our supported packages:

| Language | Package link      |
| ----------- | ----------- |
| .NET |  [NuGet](https://www.nuget.org/packages/SeliseBlocks.LMT.Client)|
| Python | [PyPI](https://pypi.org/project/seliseblocks-lmt)      |


## Monitor Your service

You can click on the three dots menu to set up a monitor for your service. To learn more, visit [Monitor your Deployments](./deploy.md#monitor-your-deployments)