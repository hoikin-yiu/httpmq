## httpmq
Httpmq is a simple HTTP message queue written in Python with Tornado and Tokyo Cabinet, just like httpsqs wriiten in C.

## Feature
* 1 Very fast and very simple, less than 700 lines python code.
* 2 High concurrency
* 3 Multiple queue.
* 4 Low memory consumption, mass data storage, less than 100MB of physical memory buffer.
* 5 Convenient to change the maximum queue length of per-queue.
* 6 Queue status view.
* 7 Be able to view the contents of the specified queue ID.
* 8 Multi-Character encoding support.

## usage
      -a <ip_address> or --address <ip_address> set ip addrss to listen.Default ip is localhost.\n
		  -p <port> or -- <port> set port to listen. Default port is 1234.\n
		  -l <file_path> or --l <file_path> set path of log file.Default path is null.\n
		  -b <db_path> or --dbpath <db_path> set path of database.Default path is null.\n
		  -t <second> or --timeout <second> set timeout to listen.Default timeout is none.\n
		  -i <second> or --interval <second> set interval to sync data from memory to disk.Default value is 5.\n
		  -a <string> or --auth <string> set auth string. Default value is null.\n
		  -d or --daemon set main process as a daemon.Default value is true.\n
		  -n <string> or --name <string> set name of main process and worker process.Default value is null.\n
		  -h or --help show help.\n
		  -v or --version show version.\n

* 1 PUT text message into a queue

  HTTP GET protocol (Using curl for example):
  
  `curl "http://host:port/?name=your_queue_name&opt=put&data=url_encoded_text_message&auth=mypass123"`
  
  HTTP POST protocol (Using curl for example):
  
  `curl -d "url_encoded_text_message" "http://host:port/?name=your_queue_name&opt=put&auth=mypass123"`
  
* 2 GET text message from a queue

  HTTP GET protocol (Using curl for example):
  
  `curl "http://host:port/?charset=utf-8&name=your_queue_name&opt=get&auth=mypass123"`
  
* 3 View queue status

  HTTP GET protocol (Using curl for example):
  
  `curl "http://host:port/?name=your_queue_name&opt=status&auth=mypass123"`
  
* 4 View queue details

  HTTP GET protocol (Using curl for example):
  
  `curl "http://host:port/?name=your_queue_name&opt=view&pos=1&auth=mypass123"`

* 5 Reset queue

  HTTP GET protocol (Using curl for example):
  
  `curl "http://host:port/?name=your_queue_name&opt=reset&pos=1&auth=mypass123"`
