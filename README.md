### httpmq
The httpmq is a simple HTTP message queue service written in Python based on Tornado and Redis.

### Feature
* 1 Fast and simple.
* 2 Asynchronous I/O.
* 3 Multiple queue.
* 4 Low memory consumption.
* 5 Queue status view.
* 6 Be able to view the contents of the specified position.

### usage
          python3.6 server.py
          --profile set profile to run.Default profile is develop.\n
		  --port set port to listen. Default port is 8200.\n
		  --daemon set main process as a daemon.Default value is true.\n

* 1 put data into a queue
url: /queue/
method: PUT
json param:

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

* 2 GET data from a queue
url: /queue/
method: GET
query param:

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
  
* 3 View status of a queue
url: /status/
method: GET
query param:

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
  
* 4 View a position of queue
url: /view/
method: GET
query param:

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

* 5 Reset queue
url: /reset/
method: GET
query param:

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