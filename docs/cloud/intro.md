---
slug: /
sidebar_position: 1
---

# Overview

Let's discover **Blocks Cloud**.

## What is Blocks Cloud?

Blocks Cloud is a developer‑focused cloud platform that accelerates application development by providing a ready-to-use front-end boilerplate, integrated backend services, AI capabilities, observability, and deployment tools. With Blocks Cloud, developers can focus on building features, not wiring infrastructure. 

**No More Building From Zero**  
Blocks Cloud eliminates the need to rebuild core foundations like [authentication](./identity/authentication), [authorization](./identity/access-manager), [captcha](./identity/captcha), [localization](./localization) and even a [browser extension](./localization/extension). These capabilities are available out of the box, so developers skip the boilerplate and start building real product features immediately.

**Built-in Chatbot**  
With an integrated [chatbot](./ai/agents.md) engine, Blocks Cloud lets you add conversational AI to your application without managing external services. It can guide users, answer questions, and automate workflows—all fully configurable inside the platform.

**Deploy Your Code**  
Blocks Cloud provides an end-to-end [deployment](./deploy.md) environment where you bring your code and the platform handles builds, runtime, scaling, and observability. You get fast, reliable deployments without dealing with complex infrastructure.

**LMT: Logging, Metrics & Tracing**  
Blocks Cloud includes built-in observability through its [LMT](./observability/logsandtracing.md) stack, giving you instant access to logs, metrics, and distributed traces for all your services. You can monitor performance, troubleshoot issues, and understand system behavior without setting up any external tooling.

**Construct**  
[Construct](https://github.com/SELISEdigitalplatforms/blocks-construct-react) gives you a ready-made React app prewired to all Blocks Cloud services. Authentication, roles, storage, data APIs, and more work out of the box—saving weeks of integration effort and letting you focus on your application’s logic.

```
      ┌───────────────────────────────┐
      │   CONFIGURE ON BLOCKS CLOUD   │
      │  IAM • CAPTCHA • MFA • Chatbot│
      └──────────────┬────────────────┘
                     ▼
      ┌───────────────────────────────┐
      │     DOWNLOAD CONSTRUCT        │
      │  Pre-built integration layer  │
      └──────────────┬────────────────┘
                     ▼
      ┌───────────────────────────────┐
      │  BUILD YOUR BUSINESS LOGIC    │
      │   React + APIs + Extensions   │
      └──────────────┬────────────────┘
                     ▼
      ┌───────────────────────────────┐
      │            DEPLOY             │
      │  Simple deployment pipeline   │
      └──────────────┬────────────────┘
                     ▼
      ┌───────────────────────────────┐
      │             LMT               │
      │   Logs • Metrics • Traces     │
      └───────────────────────────────┘

```

## What is Blocks Cloud Portal?

From the Blocks Cloud [Portal](https://cloud.seliseblocks.com), users can manage all the services that Blocks Cloud offers. You can configure authentication, emails, notifications, and much more directly from the portal, and the changes will be reflected in your Construct app. Think of the portal as the place where you manage your backend services, while the Construct app immediately reflects those configurations.


