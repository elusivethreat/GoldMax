# GoldMax
Controller for the GoldMax implant in the SolarWinds breach. Sample was pulled from MalwareBazaar.


## Database
Requires redis backend

```
docker pull redis

docker run --rm --detach --name GoldMaxDB -p 7001:6379 redis:latest 
```