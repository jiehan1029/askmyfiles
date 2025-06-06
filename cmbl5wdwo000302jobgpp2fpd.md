---
title: "How One Blocking Call Killed Our Entire FastAPI Service"
datePublished: Fri Jun 06 2025 18:51:54 GMT+0000 (Coordinated Universal Time)
cuid: cmbl5wdwo000302jobgpp2fpd
slug: how-one-blocking-call-killed-our-entire-fastapi-service
tags: asynchronous, event-loop, fastapi

---

## Incident Recap

It happened to us on production environment:

* Our FastAPI service suddenly started **timing out every request**, including the plain Kubernetes health checks that didn’t touch the database or any external dependencies.
    
* We restarted the deployment, and things recovered—briefly. A few minutes later, the app **froze again**.
    
* Load was minimal. CPU and memory usage were low.
    
* All external services reported healthy.
    
* But our app remained unresponsive.
    

After hours of debugging and a good deal of hair-pulling, we uncovered the root cause:  
A subtle but dangerous **mix of blocking code inside an** `async` FastAPI dependency.

Worse yet, only **one** pod of a downstream service was unhealthy—causing a **tiny subset of requests** to hang indefinitely. Because most requests still succeeded, the external service showed as “healthy.” But for us, a few blocked requests were enough to stall the entire **event loop** and lock up the app.

Let’s take a closer look at what happened and run some code examples.

## Why This Happens: A Closer Look

### Mechanism behind the scene

Our FastAPI app runs on top of the ASGI server (uvicorn) with multiple uvicorn workers: incoming requests → ASGI server picking up one worker → uvicorn worker passes request to FastAPI → FastAPI generates response → Uvicorn worker sends response back.

FastAPI defines how to treat functions that are used as endpoints or dependencies. When they has `async def`, they are flagged by FastAPI as “non-blocking” (regardless whether it contains blocking code or not), and `def` functions are marked as “blocking”.

The “blocking” `def` functions will be passed to the **thread pool** — there is one pool for each uvicorn worker, and that pool usually **contains a fixed number of threads** (40-100 by default, configurable). Each process takes one thread. When load is high and the sync process takes a long time, incoming requests would have to wait as all threads are in use (thread starvation).

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1749175867952/d1bbbe1e-655d-41b9-a6ad-aa66b9fb2b89.png align="center")

The “non-blocking” `async def` functions will be passed to the **event loop** — there is **only one event loop and it is shared within this python process**, i.e., this current uvicorn worker.

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1749177807583/8ee9e055-ae9f-41e3-a3bc-a3c8eeb1d3e3.png align="center")

Just to remind you: there will be multiple sequential steps required before the endpoint could respond, for example, parsing request body, resolving dependencies, run the endpoint function itself, and serialize the response data. Each of these steps could be running on either thread pool or event loop, and only after the last step is finished the response would be sent back to the caller. As a result, two things to note —

#### First, it is totally possible to mix a `def` endpoint with `async def` dependency

The dependency will be resolved first, running inside the event loop, and after that, the endpoint function will be offload to the thread pool. The mix of `async def` endpoint and `def` dependency is just the other way around: dependency is resolved first in a thread, and then the endpoint function will execute inside the event loop.

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1749181872703/175caf5f-f2f6-4052-936e-2ca571b39b34.png align="center")

Note that there is **only one** event loop — and it is supposed to run **continuously without hanging at all times**.

#### Second and most critical — though sync endpoint or dependency functions runs in the thread pool, the scheduling of their runs will happen in an event loop.

Let’s break it down.

* FastAPI/Starlette implements [AnyIO](https://github.com/agronholm/anyio) underneath the hood and specifically it uses [run\_in\_threadpool (starlette)](https://github.com/encode/starlette/blob/master/starlette/routing.py#L68) which calls [await anyio.to\_thread.run\_sync(func)](https://github.com/encode/starlette/blob/master/starlette/concurrency.py#L36) to handle sync endpoints.
    
* When AsyncIO is used for event loop when running the ASGI server, and therefore it’s detected by AnyIO as the async backend underneath the hood.
    
* It then uses AsyncIO to schedule the task to be run in thread pool [run\_sync\_in\_worker\_thread](https://github.com/agronholm/anyio/blob/master/src/anyio/_backends/_asyncio.py#L2412) which runs within AsyncIO’s event loop context, and results from the worker thread are dispatched back to the event loop.
    

### What if the event loop is blocked: load testing examples

The demo app and load test plans can be found in [this repository](https://github.com/jiehan1029/fast-fastapi/blob/main/01_blocking-requests/README.md). The main app defined two endpoints, both could block the event loop.

* `/sync_with_async_blocking_dep`: a `def` endpoint (sync) but depends on `async def` dependency which has **5%** chance hitting blocking process.
    
* `/async_with_blocking`: endpoint defined with `async def` and **5%** chance hitting blocking process.
    

```python
# code snippet from main.py

def blocking_process(blocking_time: int = 15):
    logger.info(f"Starting blocking process @ {datetime.now()}")
    time.sleep(blocking_time)
    logger.info(f"Blocking process finished @ {datetime.now()}")

async def async_dep(request: Request):
    """
    Randomly insert a long blocking process.
    """
    blocking_call = False
    if random.random() < 0.05:  # 5% chance
        blocking_call = True
        blocking_counter.inc()
        blocking_process()
    else:
        logger.info("[async_dep]Skipping blocking process.")
        non_blocking_counter.inc()

    request.state.blocking_dep = blocking_call
    return {"async_dep": f"Returned @ {datetime.now()}", "blocking_call": blocking_call}

@app.get("/sync_with_async_blocking_dep", dependencies=[Depends(async_dep)])
def sync_with_async_blocking_dep(request: Request):
    """
    Endpoint is defined without 'async' keyword but dependency is async, and this will bring
    the endpoint processing into event loop.
    """
    thread_name = threading.current_thread().name
    active_threads = threading.active_count()
    logger.info(f"[sync+dep][THREAD-{thread_name}] Inside endpoint. {request.state.blocking_dep=}. Active threads: {active_threads}")  # noqa
    return {"sync_with_async_blocking_dep": f"Returned @ {datetime.now()}",
            "blocking_call": request.state.blocking_dep,
            "thread": thread_name,
            "active_threads": active_threads}

@app.get("/async_with_blocking")
async def async_with_blocking():
    """
    Randomly insert a long blocking process.
    """
    blocking_call = False
    if random.random() < 0.05:  # 5% chance
        blocking_call = True
        async_blocking_counter.inc()
        blocking_process()
    else:
        logger.info("[async]Skipping blocking process.")
        async_non_blocking_counter.inc()
    return {"async_with_blocking": f"Returned @ {datetime.now()}", "blocking_call": blocking_call}
```

Then a 5 minutes load tests were run with 500 users with spawn rate 50/s for each endpoint. Both of them behave similarly, for example, for the endpoint with blocking dependency:

* There were some responses initially, but soon the app froze.
    
* The server was still running (still generating logs), but no responses were received.
    
* Server logs showing dependency resolution one after another after another…but not until several minutes after the load test, the endpoint execution started, and responses finally sent out.
    

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1749183605684/90897f51-f9aa-4367-a97f-fe158339e945.png align="center")

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1749183610566/9236e025-df0e-4bbe-8776-7520daaf6d39.png align="center")

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1749183776364/79e831d8-846b-4ccf-8f48-00f247926dc4.png align="center")

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1749183810006/0d00ffc5-9c7d-4787-9042-80551d859516.png align="center")

This is exactly because the **event loop is blocked** by the long running dependency resolution — **even though there is only 5% of chance encountering such blocking process.**

This is what happened:

1. Requests flooded in, mostly without blocking calls, so the first few got passed smoothly.
    
2. One request came in with the blocking dependency, so event loop paused to handle it (took 15 seconds).
    
3. While event loop was blocked, more and more tasks were queued. Say, at 150 RPS, for 15 seconds, if the blocking rate is 5%, then there could be additional 112 blocking tasks entered the event loop queue.
    
4. When the 15 seconds synchronous dependency resolution was finally completed, event loop would soon encounter another blocking dependency function, so on and so forth.
    
5. As a result, the queue grew bigger and stuck in dependency resolution. The task of “dispatching endpoint function to thread pool” never got a chance to execute inside the event loop until all previously piled-up dependency tasks were cleared up.
    
    **Key point here**:
    
    > For all endpoints (even for a `def` endpoint), **the event loop must either run or schedule the endpoint function to thread pool** (in addition to request parsing, route matching, response serialization etc). Therefore, a blocked event loop really blocks *everyone*!!
    

#### Unclog the pipeline: offload the blocking dependency to **thread pool**

Changing the async dependency to be truly “non-blocking” made the performance dramatically better.

Now we use threadpool for the blocking function as below.

```python
async def async_dep_offload(request: Request):
    """
    Offload the blocker to threadpool
    """
    blocking_call = False
    if random.random() < 0.05:  # 5% chance
        blocking_call = True
        blocking_counter.inc()
        await run_in_threadpool(blocking_process)
    else:
        logger.info("[async_dep_offload]Skipping blocking process.")
        non_blocking_counter.inc()

    request.state.blocking_dep = blocking_call
    return {"async_dep_offload": f"Returned @ {datetime.now()}", "blocking_call": blocking_call}
```

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1749185179273/c5305e06-6041-4772-87d3-3d9c1e567ad4.png align="center")

![](https://cdn.hashnode.com/res/hashnode/image/upload/v1749185186707/fa2f5ba9-4523-49d2-ab0a-6d2f69e1aeae.png align="center")

And this time, 95 percentile response time went from **“no data” (more than 5 minutes) to 11 seconds**!

## How to Write Truly Non-Blocking FastAPI Code

Just because an endpoint is `def` doesn’t mean it’s immune from degraded event loop — check its dependencies too. An endpoint or dependency is `async def` doesn’t mean it’s non-blocking — you have to consciously write non-blocking code yourself.

### Key takeaway:

* Blocking code inside async functions is a common, silent performance killer.
    
* Exam the whole flow of request handling and understand which model your endpoint is using and why.
    
* In an `async def` endpoint or dependency, **never use blocking code such as synchronous http requests to external services, heavy file I/O or synchronous database calls**. Switch to async libraries where available, blocking the event loop hurts *everyone*.
    
    * For example, use `httpx` instead of `requests` for making http calls. Adding explicit timeout for service requests is also beneficial.
        
    * If you have to use a blocking call, offload it to a separate thread using asyncio, for example `await fastapi.concurrency.run_in_threadpool(blocking_process)`
        
* If you have lots of `def` endpoints, consider increasing the threadpool size to avoid thread starvation. This can be done by configuring the `max_workers` parameter in the ThreadPoolExecutor.
    

## Bonus Lesson: Load Testing Isn’t Enough Without Fault Injection

We *did* load testing before this incident—but everything passed with flying colors.

Why? Because all our external services were healthy during the test.

What we didn’t simulate was:

* A **single misbehaving pod** in an upstream service.
    
* An endpoint that **responds slowly but doesn't fail outright**.
    
* A third-party dependency that hangs under certain conditions.
    

That’s why this issue remained hidden until it hit production. It wasn’t the volume of requests that hurt us—it was a few **perfectly-timed bad ones** that blocked the async dependency and **froze the entire event loop**.

> Don't just simulate high load. Simulate **flaky**, **slow**, or **partially failing** dependencies too.

Chaos testing (Chaos Monkey, Gremlin, or Litmus), latency injection, and timeout simulation can reveal problems that raw throughput tests never will—especially in async architectures.