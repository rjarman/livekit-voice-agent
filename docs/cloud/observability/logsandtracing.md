---
slug: /logsandtracing
sidebar_position: 1
---

# LMT

## Overview

Blocks Cloud provides powerful tools for managing and monitoring your services:

* **Logs:** View and filter logs for your services, analyze issues, and ask AI for insights.
* **Traces:** Monitor service traces, filter by date or service name, and analyze detailed trace timelines.


## Logs

Logs provide detailed records of events and actions within your services. They help you debug issues, monitor activity, and ensure your services are running smoothly.

**Key Features**

* **Filter Logs:** Filter logs by date or log level (INFORMATION, WARNING, ERROR).
* **Search Logs:** Use the search bar to find specific log entries.
* **Ask AI:** Get insights and answers about your logs using AI.

### Viewing the Logs

Navigate to **Services → Logs.**
![LMT](/img/LMT1.png "Logs")
Select the service you want to view logs for (e.g., Authentication, IAM, Storage).

Click on a log entry's trace id to view its details.


### Using AI for Log Analysis

Open the **Ask AI** panel on the right.
![tracing](/img/LMT2.png "Ask AI")

Type your query.

## Traces

Traces provide a timeline of requests and actions within your services. They help you monitor performance, identify bottlenecks, and debug issues.

**Key Features**

* **Trace List:** View all traces for your services.
* **Filter Traces:** Filter traces by date or service name.
* **Trace Details:** Analyze individual traces, including timelines, annotations, and attributes.
![LMT](/img/LMT3.png "Tracing")

### Use the filters to narrow down the trace list:

* **Date:** Select a specific date range.
* **Service Name:** Filter traces by service name (e.g., Authentication, Storage).
![LMT](/img/LMT4.png "Tracing")

### Using AI to Query Tracing Information

Open the **Ask AI** panel on the right.
![LMT](/img/LMT5.png "Ask AI")
Click on a trace entry to view its details.

### Analyzing Trace Details

Select a trace from the list.

View the timeline to analyze request durations and dependencies.

Check the **Info** tab for key details:

* **Status:** Success, Error, etc.
* **Service:** The service that generated the trace.
* **Span ID:** Unique identifier for the trace span.

Use the **Log** tab to view logs associated with the trace.


:::info
These observability tools are not limited to Blocks' microservices. You can use them for your own deployed service, as well. See our [guide](/cloud/my-services) for integrating your services.
:::
