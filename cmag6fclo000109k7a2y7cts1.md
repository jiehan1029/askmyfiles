---
title: "Postmortem: Building a New Email Microservice to Stand Beside a Legacy System"
datePublished: Fri May 09 2025 02:28:06 GMT+0000 (Coordinated Universal Time)
cuid: cmag6fclo000109k7a2y7cts1
slug: postmortem-building-a-new-email-microservice-to-stand-beside-a-legacy-system
tags: microservices, architecture, migration, email-server, postmortem

---

## Background & Requirements

About two years ago, I led a project to build a new email microservice for our company. The existing system—built about 15 years ago—was embedded in a monolithic codebase using a now-less-popular language. It sent customer emails and SMS messages reliably, but couldn’t support modern product requirements:

* No user engagement tracking (opens/clicks)
    
* Strong coupling to a specific MySQL schema
    
* Only usable by apps with the same schema and database setup (newer apps with postgresQL cannot use it)
    
* Vague service ownership (only a few engineers in the company know how to mess with the codebase)
    

The new service needed to be:

* Decoupled from the monolith and its database
    
* Capable of tracking user engagement
    
* Scalable, reliable, and observable
    
* Flexible enough to support new messaging formats and requirements
    

## What’s Built

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1745967157406/1ae86c51-fb43-4ccf-b8b6-a5d50b9576e3.png align="center")

The architecture was relatively simple:

* Incoming requests are saved to a database
    
* A producer extracts messages and sends them to a queue (SQS)
    
* Consumers send the messages (SES) and SNS events return user engagement stats
    
* A webhook captures the SNS events and stores engagement in the database
    

The service is written in Python. Beyond the core service, we implemented autoscaling, monitoring, load testing, and product analytics hooks.

While the core design held up, a few architectural decisions are worth revisiting.

### Why Then, What’s Changed, and What I’d Do Differently

1. #### Database as a Queue: Simple and Good Enough
    

Email sending needs to be processed asynchronously, with option to to schedule a send in the future. Instead of a job orchestrator like Celery, we decided to use a **database as a queue** for the following key technical factors:

* **Traceability and Auditability:** by storing the scheduled emails directly in the database, we could easily track the entire lifecycle of each message, from when it was requested to when it was sent, including details about which service triggered the request. This was crucial for debugging, auditing, and ensuring we had full visibility into the system, especially since we wanted to keep detailed logs about the process. Customized grouping and filtering are also convenient: we can easily find out the request volume for a specific customer, a certain time period, even adding subdivision metadata for analysis, all in one place, without any learning curve of new tools. In the meantime, job broker often use a separate datastore or a predefined table schema, that you must implement custom correlation between the job and rest of the flow.
    
* **Control and Flexibility**: the database allowed us to easily manage and modify scheduled jobs. For instance, if we needed to reschedule or cancel an email, it was as simple as updating or removing rows from the queue table. This was much more straightforward compared to using EventBridge or Celery, which would require additional tooling or logic to track jobs, reschedule them, or handle cancellations. With the database, we also had **unlimited retention** for the records.
    
* **Simplicity and Maintenance**: the database solution was simple to implement and maintain compared to a more complex orchestration system. If we need to scale horizontally, we could add database partition, just like for a regular application database.
    

There are several cons as well:

* **Reinvent the Wheels** (sort of): we need to implement retries with backoffs, ensure atomic transactions, ensure data consistency and integrity during system failure, etc etc, which would be readily available if use a job or workflow orchestrator.
    
* **Scalability and Throughput**: with api, producer and consumer all talking to the database, the db naturally becomes the bottleneck: connection management, row lock, race condition, query optimization, database CPU utilization — these factors play an important role in how much RPS or throughput we can achieve. Fortunately, our company does not generate unmanageable traffic, usually about 20-40RPS in busy hours, which is well within the system capacity.
    

In conclusion, the **database as a queue** solution provided the right balance of **reliability**, **traceability**, and **control**. The throughput meets our needs, and the system is simple enough to build and maintain.

2. #### Decouple Producer and Consumer: Improved Reliability
    

Looking at the architecture diagram, one question asked is “why add a queue and consumer instead of sending emails from producer directly?” Several reasons:

* **Separation of Concerns**: each component has clear responsibility and service boundary, making code maintenance and iteration easier.
    
* **Independent Scaling**: we are free to adjust producer or consumer pods independently as necessary. If the queue is too big and consumer too busy, we could slow down producer. If the mail service provider has a rate limit, we could implement that in consumer without affecting producer.
    
* **Fault Tolerance**: also because of the decoupling, failed producer won’t block consumer to send the email, and vice versa.
    

In summary, separating producer and consumer via queue (SQS) has made the system more reliable.

3. #### Event Handling: Webhook → Queue
    

In current implementation, SNS events for delivery and engagement are sent to a public webhook that processes and stores the data. This works, but has scaling issues. I’d now prefer routing SNS events to a queue, then processing them with a dedicated consumer.

##### **Why this change?**

* **Resilience**: Large message volumes can overwhelm webhook pods, leading to timeouts and retries. Yes, it’s possible to configure the cadence of SNS delivery and retry policy, but the new approach would be cleaner.
    
* **Flexibility**: Other services (say, a dashboard showing email engagement rate) could subscribe to these events using pub/sub patterns without reaching out to the email service (and its database).
    

4. #### Service Scope: Replacement → Supplement
    

Originally, the plan was to fully replace the legacy mail server. But that turned out to be overly optimistic. Two years later, the old system is still very much alive—and for good reason.

First, from a business perspective, rebuilding for parity didn’t feel like a great use of resources, especially during a time of rapid product growth. Why spend time duplicating something that already works? “if it works…don’t touch it”.

Second, the legacy system is *convenient*—at least for apps that can use it. It pulls user data directly from the app’s database, so there’s no need to pass much around. Without strong top-down push, the team had little incentive to switch.

And finally, internal support teams have years of tooling and muscle memory built around the old system. Asking them to retrain and adopt a new one—with fewer tools and a steeper learning curve—was a tough sell.

So the new email service found its niche: powering *new* apps, while the legacy system continues to support the old guard.

**Implications:**

* The new service no longer needs to support legacy schemas.
    
* It can integrate directly with newer systems, like the new user directory service, translation service, and more, making the service more customized for the microservice architecture overall.
    
* For example, we would be able to pass user directory IDs instead of full user context, and the email service resolves it internally. This simplifies the API and ensures consistency.
    

### Lessons from Migration

1. Don’t assume code rewrites finish on schedule.
    
2. Don’t assume customers will migrate on schedule.
    
3. Don’t assume internal teams will adopt new systems on schedule.
    
4. Just as important: **respect what the legacy system gets right**. It was built with real constraints and has strengths that kept it running for years. Understand that before deciding what the new service is really adding.
    

**Reality check:** The old system’s not going anywhere—it still makes money. So instead of a smooth, clean migration, you’ll likely be patching things up and connecting the old and new systems for a long time. Don’t count on everything going to plan. Keep your scope tight, stay flexible, and be ready to shift gears as things unfold.

### Operational & Compliance Considerations

1. **Security**: Enterprise infoSec audits can be strict. I explained the email auth flow and key places to config in this post: [From Mail Server to End Recipient: Email Authentication](https://hashnode.com/post/cma6anws7000b09l1b06ld9tr).
    
2. **Tracking and privacy**: SES pixel tracking is not always possible or compliant, so give customers the option to opt out. Configure a custom tracking domain for whitelisting by customer IT (yes SES generates random (and relatively stable) tracking domain but that’s not permanent).
    
3. **Unsubscribe management**: two parts: 1) product teams shall define unsubscribe behavior across suites (so get them involved early). 2) handle hard bounces to protect sender reputation and avoid repeat sends to bad addresses.
    
4. **Data policy**: coordinate with legal and privacy teams to understand what data can be tracked, stored or shared(e.g., PII, EU data residency, GDPR compliance).
    

### Final Thoughts

This project taught me that building infrastructure in a legacy-heavy org is as much about organizational design and communication as it is about code. You need to design for today’s needs while positioning for tomorrow’s architecture, and be ready to adapt as the ground shifts beneath you.