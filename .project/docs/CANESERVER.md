#CANESERVER

- A flask application intended to be a high available edge node to serve the content cache.
- Get content from the JAGGERY server and serve accordingly.


# Endpoints
- /master/ (Serves the master schema)
- /r/:idx/:version/:slug (the versioned url thats time lived as per the catalog definition rules)

## HTTP APIs for cache management
- DELETE to invalidate some particular version of a cache
- PATCH to trigger the JAGGERY to fetch the latest content.

  
