# Implementation

How should a sugarcane powered client application should make caching decisions ?

## Fetching the master
- Respect the master schema expiry time as the main authority

## Fetching the nodes

### When child node expires ?
- if master is not expired ? - do as said in the last fetched master
- if the master is also expired ? - fetch the master first and proceed as said in the new master

### When child node is not expired ?
check the master expiry
- if the master is not expired ? - check if child node version is already updated in the fetched master (The cached child content might be obsolete already)
- if the master is expired ? - fetch the master and proceed as said in the master

### When live=True in the child node ?
- skip the cache and fetch from production endpoint

### When live=True in the master node ?
- fetch from live regardless of any settings. But still respect the expiry settings in the master schema. Means, fetch master next time to see if the `live` flag has been updated to be false or removed.

  
