# Mucize - Cache Mock

## Routes
- Master Schema - `/cdn/master`
- Node Data - `/cdn/get/<version>/<node_name>`


## TTL Distribution
- keep master schema ttl to be less, eg. 300 Seconds
- keep node data ttl to be higher, eg. 1 Day


# How application should work ?
- application is supposed to query the master schema as the metadata for object endpoints
- each object endpoint api is found in the response of the master schema


**/cdn/master**
```
{
    "master": {
        "ttl": 3
    },
    "nodes": {
        "post": "/cdn/get/v8.1.68/post",
        "user": "/cdn/get/v9.0.35/user",
        "food": "/cdn/get/v1.8.52/food",
        "emoji": "/cdn/get/v8.6.27/emoji",
        "people": "/cdn/get/v8.1.15/people"
    }
}
```

**/cdn/get/v8.1.68/post**
```
{
    "node": "post",
    "version": "v8.1.68",
    "expires_on": "2024-03-11 16:02:05.040831",
    "data": [
        {
            "id": 1,
            "value": "https://picsum.photos/id/321/200/300?type=post"
        },
        {
            "id": 2,
            "value": "https://picsum.photos/id/426/200/300?type=post"
        },
        {
            "id": 3,
            "value": "https://picsum.photos/id/246/200/300?type=post"
        },
        {
            "id": 4,
            "value": "https://picsum.photos/id/629/200/300?type=post"
        },
        {
            "id": 5,
            "value": "https://picsum.photos/id/702/200/300?type=post"
        },
        {
            "id": 6,
            "value": "https://picsum.photos/id/913/200/300?type=post"
        },
        {
            "id": 7,
            "value": "https://picsum.photos/id/361/200/300?type=post"
        },
        {
            "id": 8,
            "value": "https://picsum.photos/id/216/200/300?type=post"
        },
        {
            "id": 9,
            "value": "https://picsum.photos/id/528/200/300?type=post"
        }
    ]
}
```

