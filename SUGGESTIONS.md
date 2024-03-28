## Sugarcane
The project aims to solve API optimization with objectives as mentioned below.

## Objectives
API Call Reduction
API Resposne Time Optimization
Cache Control and Predictability
Feature Flags (Granularity)
Lazy Loading controls
Engineering Implementation Time Reduction (Swift Rollout)


A sample schema for when static APIs get called could look like:

1. verbose and terse mode
2. verbose mode will have updated_on, version etc info in the list
3. terse mode will have expires_on only


**VERBOSE**
```
{
    "expires_on": "",
    "updated_on": "",
    "scheme": "master",
    "namespaces": {
        "dashboard": ["profile", "wallet_balance", "notice"],
        "quiz": ["profile", "/api/quiz/questions"],
    },
    "defaults": {
        "timeout": 60000,
        "expires_on": "2024-03-20 00:50:19.208527"
    },
    "flags": {
        "url": "",
        "expires_on": ""
    },
    "nodes": {
        "/api/quiz/questions": {
            "expires_on": "2024-03-20 00:50:19.208527",
            "updated_on": "2024-03-20 00:49:59.208529",   # to be discussed
            "url": "/api/quiz/questions/v5.6.69/",
            "ver": "v5.6.69" # to be discussed,
            "timeout": "v5.6.69" # to be discussed,
        }, 
        "notice": {
            "expires_on": "2024-03-20 00:50:19.208507",
            "updated_on": "2024-03-20 00:49:59.208511",
            "url": "/url/for/notice",
            "version": "v7.6.89"
        },
        .....
        .....
    }
}
```
**TERSE**
```
{
    "expires_on": "",
    "scheme": "master",
    "namespaces": {
        "dashboard": ["profile", "wallet_balance", "notice"],
        "quiz": ["profile", "/api/quiz/questions"],
    },
    "nodes": {
        "/api/quiz/questions": {
            "expires_on": "2024-03-20 00:50:19.208527",
            "url": "/api/quiz/questions/v5.6.69/",
        }, 
        "notice": {
            "expires_on": "2024-03-20 00:50:19.208507",
            "url": "/url/for/notice"
        },
        .....
        .....
    }
}
```
