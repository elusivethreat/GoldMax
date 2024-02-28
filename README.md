# GoldMax
Controller for the GoldMax implant in the SolarWinds breach. Sample was pulled from MalwareBazaar.


## Sample
Can be downloaded from:
- https://bazaar.abuse.ch/sample/4e8f24fb50a08c12636f3d50c94772f355d5229e58110cccb3b4835cb2371aec/

## Database
Requires redis backend. If docker and redis are already installed, the controller will automatically start the database.

```
docker pull redis

docker run --rm --detach --name GoldMaxDB -p 7001:6379 redis:latest 
```