---
title: "From Mail Server to End Recipient: Email Authentication"
datePublished: Fri May 02 2025 04:29:02 GMT+0000 (Coordinated Universal Time)
cuid: cma6anws7000b09l1b06ld9tr
slug: from-mail-server-to-end-recipient-email-authentication
tags: enterprise, email-security, email-authentication

---

We have a relatively new mail service built using Amazon SES (in addition to an old on-premise mail server). Our customers are mostly enterprise, and therefore layers of security checks. This blog attempts to make it easier to understand the email authentication flow from server to mail receiver, and where could go wrong with enterprise security policies.

## Mail Server Infra, SPF, DKIM, DMARC and Their Roles in Authentication

### On-premise Server

It would be easier to learn the flow using an **on-premise** email server as an example.

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1746158042731/4be13d99-847b-4b27-9311-c18167fb84f1.png align="center")

The mail server was deployed, assigned an static public IP address, and registered a DNS record for that IP and hostname.

Also added to its DNS text are SPF (sender policy framework) which specifies the mail server IP (or hostname/domain), a public key for DKIM (DomainKeys Identified Mail) which will be used to validate the d-signature in email headers (signed by the mail server using a matching private key), and optionally DMARC (Domain-based Message Authentication, Reporting, and Conformance) record that specify what to do if SPF and/or DKIM validation fails.

Because DNS records are public, the mail receiver can extract the sender’s IP address and look it up upon receiving the headers of the email message. The mail receiver tries to make the following connection:

#### SPF check — the email is from a valid SMTP infra

* `Return-Path` header is set by the actual SMTP infra.
    
* Incoming IP address (connecting IP) is also from the actual SMTP infra.
    
* Mail receiver will look up DNS for the domain of the `Return-Path` to verify the incoming IP actually belongs to the domain, and therefore verifying the mail is sent from a valid infra.
    

#### DKIM check — the email content is not altered on transit

* The `From:` header is who the mail sender claims himself to be, in this case, it comes from my domain.
    
* My domain holds a private key, and post the matching public key to DNS text as DKIM.
    
* Mail content is signed using my domain’s private key.
    
* Mail receiver can look up DNS and find the public key, to verify the DKIM signature, and hence convinced the message content has not been pampered.
    

#### DMARC check — who shown as “From” is indeed who sent the email

* It again starts from `From:` header, which is visible to end recipient as the sender.
    
* DMARC result is determined by SPF and DKIM: DMARC pass = (SPF is valid **AND** aligned) **OR** (DKIM is valid **AND** aligned)
    
    * SPF and DKIM validities are checked in flows explained above.
        
    * Alignment means the domain for SPF (or DKIM respectively) align with the `From:` header (subdomain counts too). If my `From:` domain is `mycompany.com` and SMTP sending infra assigned a `Return-Path` domain to be `mail.mycompany.com`, SPF is aligned properly.
        
* If DMARC policy is not defined in DNS text, then above DMARC check won’t happen. SPF and DKIM validity checks will still happen, but no alignment checks.
    

The authentication flow goes naturally now, since I own the whole infrastructure and can match records everywhere.

### Amazon SES

For what I needed to debug, Amazon SES (instead of on-premise server) is used, and therefore different/additional things to watch because another infra (SES) and new set of IP address & domain/hostname is added to the picture.

#### Default SES MAIL FROM domain

The **MAIL FROM** domain in Amazon SES is the `Return-Path` header domain of the email message sent by SES, also called envelope sender domain. It’s the mark left by SMTP infra to indicate where the email is *actually* sending from — regardless what the visible email `From:` field says. I can set a `From:` field to my domain (as long as my domain is a verified SES identity), but the `Return-Path` domain would always be `amazonses.com`.

During email authentication:

* SPF check happens there. DKIM and DMARC checks are still based on my domain because that’s what my `From:` header belongs.
    
* SPF validity, DKIM validity and DKIM alignment will pass, and therefore DMARC will pass.
    
* However, SPF alignment will fail as SPF is checked for amazonses.com while my `From:` header is for my domain. This could be a red flag in the eyes of the enterprise security team because it means **I do not show a proof of relationship between my sending identity (my domain) and the actual email sending SMTP infra** — what if a bad actor stole my sending identity and then sent emails from the villain’s infra?
    

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1746157324287/6dfaaebc-664d-4490-a7e2-8917ca0d68e8.png align="center")

#### Custom MAIL FROM domain

To let the email receiver *see* that the email is sent from *your* infra, you need the `Return-Path` header, i.e., envelope sender, to be in your domain, not Amazon’s. This can be done by configuring custom **MAIL FROM** domain in Amazon SES. Once configured, SES will set the envelope domain to your custom **MAIL FROM** domain, and therefore to achieve SPF domain alignment.

SPF validity check passes in this case because you will also add `include:amazoneses.com -all` to the SPF of your MAIL FROM domain, which says to the mail receiver, “yes, if the connecting IP is from amazoneses, then it’s valid”.

Combining it together, we tell the mail receiver: “**we are sending this email as who we are, from an infra that we acknowledge.**” And this would create more trust.

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1746157736636/04846d9a-1f72-4486-b882-fbcaf3cbdfea.png align="center")

#### IP Address

Well, if your customer is really strict about it (government, for example), they could implement custom IP-based filters that only allow emails sent from certain known static IPs. By default SES uses an IP range, and therefore the mail server’s connecting IP is dynamic. You can request dedicated static IPs at an additional price.

### Miscellaneous: Header-Based Filters

It’s also possible the customer requires a custom header, or requires certain headers to have (or not to have) certain values, to pass certain levels of security checks. Mail receiver can also configure security rules to modify specific headers. For example, one customer stripped the From address from our emails because it contains the name of the company. There can be different recipes!