### httpmq
The httpmq is a simple HTTP message queue service written in Python based on Tornado and Redis.

### Feature
*  Fast and simple.
*  Asynchronous I/O.
*  Multiple queue.
*  Low memory consumption.
*  Queue status view.
*  Queue position view.

### Usage
```bash
python3.6 server.py
```
```
--profile set profile to run.Default profile is develop.\n
--port set port to listen. Default port is 8200.\n
--daemon set main process as a daemon.Default value is false.\n
```

#### put data into a queue
- url: /queue/
- method: PUT
- json param:

field |    type   | require | remark
------|-----------|---------|------
name  |    str    |   yes   | queue name
data  | (str,int) |   yes   | data

example:
```bash
curl -X PUT -H 'Content-Type:application/json' "http://127.0.0.1:8200/queue/" -d '{"name":"test", "data":1}' | jq .
```
response:
```json
{
  "code": 1,
  "message": "HTTPMQ_PUT_OK",
  "data": {}
}
```

#### get data from a queue
- url: /queue/
- method: GET
- query param:

field |    type   | require | remark
------|-----------|---------|------
name  |    str    |   yes   | queue name

example:
```bash
curl -X GET "http://127.0.0.1:8200/queue/" -d 'name=test' | jq .
```
response:
```json
{
  "code": 1,
  "message": "HTTPMQ_SUCCEED",
  "data": "1"
}
```
  
#### view status of a queue
- url: /status/
- method: GET
- query param:

field |    type   | require | remark
------|-----------|---------|------
name  |    str    |   yes   | queue name

example:
```bash
curl -X GET "http://127.0.0.1:8200/status/" -d 'name=test' | jq .
```
response:
```json
{
  "code": 1,
  "message": "HTTPMQ_SUCCEED",
  "data": {
    "name": "test",
    "put_pos": 2,
    "get_pos": 1,
    "unread": 1
  }
}
```
  
#### view a position of queue
- url: /view/
- method: GET
- query param:

field    |  type  | require | remark
---------|--------|---------|------
name     |  str   |   yes   | queue name
position |  int   |   yes   | position

example:
```bash
curl -X GET "http://127.0.0.1:8200/view/" -d 'name=test' -d 'position=1' | jq .
```
response:
```json
{
  "code": 1,
  "message": "HTTPMQ_SUCCEED",
  "data": 1
}
```

#### reset a queue
- url: /reset/
- method: GET
- query param:

field |    type   | require | remark
------|-----------|---------|------
name  |    str    |   yes   | queue name

example:
```bash
curl -X GET "http://127.0.0.1:8200/reset/" -d 'name=test' | jq .
```
response:
```json
{
  "code": 1,
  "message": "HTTPMQ_RESET_OK",
  "data": {}
}
```

 
### response code
code  |        info        | remark
------|--------------------|-------
1	  | HTTPMQ_SUCCEED     |
2	  | HTTPMQ_FAILED      |
3	  | HTTPMQ_PARAM_ERROR |