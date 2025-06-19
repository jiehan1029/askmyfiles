---
title: "Rendering Strategies in Modern Web: CSR, SSR, and SSG"
datePublished: Thu Jun 19 2025 03:07:22 GMT+0000 (Coordinated Universal Time)
cuid: cmc2svs9a000i02jrhugu0g1r
slug: rendering-strategies-in-modern-web-csr-ssr-and-ssg
tags: spa, web-development, ssr, rendering, csr

---

This is a quick recap of my effort to catch up on modern frontend trends, particularly the renaissance of Server-Side Rendering (SSR), and how it compares to Client-Side Rendering (CSR) and Static Site Generation (SSG).

I’ve organized this post as personal study notes first, followed by an AI-generated summary. Here are the key questions I asked myself:

* Do I care about SEO?
    
* How big is my app, user base, or company (eng & infra team)?
    
* How complex is my app? What’s the size of the current JavaScript bundle (assuming a typical CSR SPA)? Would reducing it meaningfully improve load times?
    
* Are my users sensitive to loading speed, or is a loading spinner on first visit acceptable?
    
* Is it worth the effort to maintain a new server (for SSR) alongside the existing backend, and ensure its observability and scalability?
    
* If my backend is already written in TypeScript or Node.js, does it make sense to merge frontend and backend logic into one SSR-enabled repo (e.g. with server components)?
    
* Is there a benefit to adopting a hybrid SSR + CSR approach?
    

### My Takeaway

SSR brings meaningful gains for larger applications and companies where load time, SEO, and performance are top priorities. For small to medium projects, it only makes sense if:

* I already use JavaScript/TypeScript across the stack.
    
* I adopt a unified framework like Next.js or Nuxt.js to co-locate backend logic and avoid managing an additional server.
    
* I’m developing a mobile app that needs to run on older devices, which are more sensitive to large JavaScript bundles and heavy client-side logic. In this case, offloading processing to the server and reducing the client bundle size can improve performance and user experience.
    

If my backend is written in another language and my users aren’t performance-sensitive, sticking with a CSR SPA is likely good enough. Hybrid SSR + CSR is also a practical option to improve initial page loads without going all in on SSR.

OK, below is AI generated comparison :)

---

## 🔍 What Are CSR, SSR, and SSG?

| Method | Where HTML is rendered | When HTML is generated | Who renders content | Ideal For |
| --- | --- | --- | --- | --- |
| **CSR** (Client-Side Rendering) | In the browser | On each page load | Client (JS) | Highly dynamic apps, dashboards |
| **SSR** (Server-Side Rendering) | On the server | On each request | Server | Personalization, SEO pages, blogs |
| **SSG** (Static Site Generation) | During build time | Before deployment | Server (once) | Marketing pages, docs, blogs |

---

## 🧠 Summary of Trade-offs

| Feature | CSR | SSR | SSG |
| --- | --- | --- | --- |
| **Initial Load Speed** | Slower (wait for JS) | Faster (HTML pre-rendered) | Fastest (cached HTML) |
| **SEO Support** | Poor by default | Good | Great |
| **Personalization** | Easy (client state) | Easy (server logic) | Difficult (static only) |
| **Hosting Simplicity** | Very simple (S3/CDN) | Needs server runtime | Simple (S3/CDN) |
| **Real-Time Data** | Easy | Works with hydration | Needs client-side fallback |
| **Cold Start Risk** | None | Some (if serverless) | None |
| **Build Scalability** | Great | Good | May be slow for many pages |

---

## ✅ Sweet Spot for Each

### 🟩 CSR:

* Use when interactivity is king: dashboards, apps with lots of user state and real-time changes
    
* Simpler hosting with static site delivery + APIs
    

### 🟦 SSR:

* Use when you need:
    
    * SEO for dynamic content (e.g. product pages)
        
    * Personalized HTML per request (e.g. user-specific data)
        
* You can selectively SSR certain pages (hybrid routing)
    

### 🟨 SSG:

* Use when content is mostly static or doesn’t change per user
    
* Lightning-fast delivery via CDN
    
* Ideal for blogs, documentation, and marketing sites
    

---

## 🔬 Core Web Vitals & How Rendering Affects Them

### 📏 Definitions

* **TTFB (Time To First Byte)**: Time until the browser receives the first byte of response
    
* **FCP (First Contentful Paint)**: Time until the first text/image is rendered
    
* **LCP (Largest Contentful Paint)**: Time until the largest visible element is rendered
    
* **CLS (Cumulative Layout Shift)**: Measures visual stability (layout jumps)
    
* **INP (Interaction to Next Paint)**: Measures responsiveness of interactions
    

### 📊 Rendering Impacts

| Vitals Metric | CSR Impact | SSR Impact | SSG Impact |
| --- | --- | --- | --- |
| TTFB | Fast (static HTML) | Slower (server computes) | Fastest (pre-built) |
| FCP | Slower (wait for JS) | Faster (HTML sent early) | Fastest |
| LCP | Slower | Better | Best |
| CLS | Risky (hydration jumps) | Can be stable | Stable |
| INP | Good (interactive) | Good post-hydration | Good post-hydration |