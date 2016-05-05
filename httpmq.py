# a simple http message queue
import tokyocabinet
import tornado.ioloop
import tornado.httpserver
import tornado.web
import os
import stat
import time
# import urllib
import signal
import threading
# import multiprocessing
import optparse
import json
import config
# import logging
import setproctitle

# database
mq_db = None
# max queue num
mq_max_queue_num = 1000000

# class daemonProcess(object, multiprocessing.Process):
#	  """set a daemon process"""
#	 def __init__(self, ):
#		 multiprocessing.Process.__init__(self)

#	 def run(self, ):
#		 self.daemon = True


class HttpmqHandler(object, tornado.web.RequestHandler):
	"""main handler"""


	def __init__(self):
		"""init parameter of request"""
		self.auth = ''
		self.db_name = ''
		self.charset = ''
		self.opt_type = ''
		self.data = None
		self.position = 0
		self.queue_num = 0
		self.synctime = 1


	@tornado.web.asynchronous
	def get(self):
		"""do get"""
		self.get_args()
		self.set_headers()
		if self.do_auth():
			# put data
			if self.opt_type == "put":
				if self.db_name is not None and len(self.db_name) <= 256:
					if self.data:
						pos = self.put_pos()
						# key-value format: 'queue_name:pos' data
						key = self.db_name + ":" + str(pos)
						mq_db.put(key, self.data)
						self.set_header("Pos", pos)
						self.write("HTTPMQ_PUT_OK")
						self.finish()
					else:
						self.write("HTTPMQ_PUT_END")
						self.finish()
			# get data
			elif self.opt_type == "get":
				if self.db_name is not None and len(self.db_name) <= 256:
					pos = self.get_pos()
					if pos == 0:
						self.write("HTTPMQ_GET_END")
						self.finish()
					else:
						# key-value: 'queue_name:pos' data
						key = self.db_name + ":" + str(pos)
						data = mq_db.get(key)
						if data:
							self.set_header("Pos", key)
							self.write(data)
							self.finish()
			# return status of queue
			elif self.opt_type == "status":
				put_times = ""
				get_times = ""
				unget = None
				maxqueue = self.read_maxqueue()
				put_pos = self.read_put_pos()
				get_pos = self.read_get_pos()
				# 'put' ahead of 'get', 1 round
				if put_pos >= get_pos:
					# number of unread
					unget = abs(put_pos - get_pos)
					# 1 round
					put_times = "1st lap"
					get_times = "1st lap"
				# 'get' ahead of 'put', 2 round
				elif put_pos < get_pos:
					unget = abs(maxqueue - get_pos + put_pos)
					# 2 round
					put_times = "2nd lap"
					get_times = "1st lap"
				self.write("HTTP Message Queue %s" % config.CONFIG_VERSION)
				self.write("HTTP Message Queue Version %s" % config.CONFIG_VERSION)
				self.write("\n")
				self.write("Quene name %s" % self.db_name)
				self.write("Maximum number of queue %d" % maxqueue)
				self.write("Put position of queue is %d" % put_pos)
				self.write(put_times)
				self.write("Get position of queue is %d" % get_pos)
				self.write(get_times)
				self.write("Number of unread queue is %d" % unget)
				self.finish()
			# return status of queue in json
			elif self.opt_type == "status_json":
				put_times = ""
				get_times = ""
				unget = None
				maxqueue = self.read_maxqueue()
				put_pos = self.read_put_pos()
				get_pos = self.read_get_pos()
				# 'put' ahead of 'get', 1 round
				if put_pos >= get_pos:
					# number of unread
					unget = abs(put_pos - get_pos)
					put_times = "1"
					get_times = "1"
				# 'get' ahead of 'put', 2 round
				elif put_pos < get_pos:
					unget = abs(maxqueue - get_pos + put_pos)
					put_times = "2"
					get_times = "1"
				status_json = {}
				status_json['name'] = self.db_name
				status_json['maxqueue'] = maxqueue
				status_json['put_pos'] = put_pos
				status_json['putlap'] = put_times
				status_json['get_pos'] = get_pos
				status_json['getlap'] = get_times
				status_json['unread'] = unget
				self.write(json.dumps(status_json))
				self.finish()
			# view data of a single position
			elif self.opt_type == "view":
				if self.db_name is not None and self.position is not None:
					pos_value = self.mq_view()
					if pos_value:
						self.write(pos_value)
						self.finish()
			# reset the queue
			elif self.opt_type == "reset":
				if self.db_name is not None:
					is_reset_ok = self.mq_reset()
					if is_reset_ok == 0:
						self.write("HTTPMQ_RESET_OK")
					else:
						self.write("HTTPMQ_RESET_ERROR")
					self.finish()
			# set 'maxqueue'
			elif self.opt_type == "maxqueue":
				if self.db_name is not None and self.queue_num is not None:
					is_set_ok = self.mq_set_maxqueue()
					if is_set_ok != 0:
						self.write("HTTPMQ_MAXQUEUE_OK")
					else:
						self.write("HTTPMQ_MAXQUEUE_CANSEL")
					self.finish()
			# set 'synctime'
			elif self.opt_type == "synctime":
				if self.synctime is not None:
					# 1 second <= synctime < 1000000 seconds
					if self.synctime >= 1 and self.synctime <= 1000000:
						is_set_ok = self.mq_set_synctime(self)
						if is_set_ok >=1 :
							self.write("HTTPMQ_SYNCTIME_OK")
						else:
							self.write("HTTPMQ_SYNCTIME_ERROR")
						self.finish()
			# error of command
			else:
				self.write("HTTPMQ_ERROR")
				self.finish()
		# error of auth 
		else:
			self.write("HTTPMQ_AUTH_ERROR")
			self.finish()
			

	@tornado.web.asynchronous
	def post(self):
		"""do post"""
		self.get_args()
		self.set_headers()
		if self.do_auth():
			if self.db_name is not None and self.opt_type is not None and len(self.db_name) <= 256:
				# input data in queue
				if self.opt_type == "put":
					if len(self.data) > 0:
						pos = self.put_pos()
						if pos > 0:
							# key-value: 'db_name:pos' data
							key = str(self.db_name) + ":" + str(self.pos)
							mq_db.put(key, self.data)
							self.set_header("Pos", pos)
							self.write("HTTPMQ_PUT_OK")
							self.finish()
					else:
						self.write("HTTPMQ_PUT_END")
						self.finish()


	def put_pos(self):
		"""return current 'put' position of queue"""
		# get 'maxqueue' of queue
		maxqueue = self.read_maxqueue()
		# get current 'put' position of queue
		put_pos = self.read_put_pos()
		# get current 'get' position of queue
		get_pos = self.read_get_pos()
		key_put_pos = self.db_name + ":" + "putpos"
		# 'put' position increments
		put_pos = put_pos + 1
		# If 'put' position catch up with 'get' postion, which means queue is full
		# and needs to return 0, rejecting to put data in current queue.
		if put_pos == get_pos:
			put_pos = 0
		# If 'get' position <= 1(which means queue was read just one or zero times) 
		# and 'put' position > maxqueue, it needs to return 0, rejecting to put data
		# in current queue.
		elif get_pos <= 1 and put_pos > maxqueue:
			put_pos = 0
		# If 'put' position is over to 'maxqueue', reset 'put' position to 1
		# and return it.
		elif put_pos > maxqueue:
			if mq_db.put(key_put_pos, "1"):
				put_pos = 1
		# Normal situation: 'put' position increments and is written to database
		else:
			mq_db.put(key_put_pos, put_pos)
		return put_pos
				

	def get_pos(self):
		"""return current 'get' position of queue"""
		# get 'maxqueue' of queue
		maxqueue = self.read_maxqueue()
		# get current 'put' position of queue
		put_pos = self.read_put_pos()
		# get current 'get' position of queue
		get_pos = self.read_get_pos()
		key_get_pos = self.db_name + ":" + "getpos"
		# If 'get' position does not exists and 'put' position exists,
		# reset it "1"
		if get_pos == 0 and put_pos > 0:
			get_pos = 1
			mq_db.put(key_get_pos, "1")
		# Normal situation:'get' position < 'put' position
		elif get_pos < put_pos:
			get_pos = get_pos + 1
			mq_db.put(key_get_pos, get_pos)
		# If 'get' is faster than 'put', and 'get' position < 'maxqueue'
		elif get_pos > put_pos and get_pos < maxqueue:
			get_pos = get_pos + 1
			mq_db.put(key_get_pos, get_pos)
		# If 'get' is faster than 'put' and catch up with 'maxqueue', reset
		# it to start position("1").
		elif get_pos > put_pos and get_pos == maxqueue:
			get_pos = 1
			mq_db.put(key_get_pos, "1")
		# error situation: 'get' position == 'put' position, which means
		# the data of queue had been fetched, set 'get' position to "0".
		# "0" means can not get data.
		else:
			get_pos = 0
		return get_pos
	

	def read_maxqueue(self):
		"""get 'maxqueue'"""
		# for example: queue_name:maxqueue 1000000
		key_maxqueue = self.db_name + ":" + "maxqueue"
		maxqueue = mq_db.get(key_maxqueue)
		if maxqueue:
			maxqueue = int(maxqueue)
		else:
			maxqueue = mq_max_queue_num
		return maxqueue
	

	def read_put_pos(self):
		"""get 'put' position"""
		# for example: queue_name:putpos 555
		key_put_pos = self.db_name + ":" + "putpos"
		putpos = mq_db.get(key_put_pos)
		if putpos:
			putpos = int(putpos)
		return putpos
	

	def read_get_pos(self):
		"""get 'get' position"""
		# for example: queue_name:getpos 554
		key_get_pos = self.db_name + ":" + "getpos"
		getpos = mq_db.get(key_get_pos)
		if getpos:
			getpos = int(getpos)
		return getpos
	

	def mq_view(self):
		"""get data of any position"""
		key = self.db_name + ":" + str(self.pos)
		data = mq_db.get(key)
		return data

	
	def mq_reset(self):
		"""reset the queue"""
		# remove 'put' position
		key_put_pos = self.db_name + ":" + "putpos"
		mq_db.remove(key_put_pos)
		# remove 'get' position
		key_get_pos = self.db_name + ":" + "getpos"
		mq_db.remove(key_get_pos)
		# remove 'maxqueue'
		key_maxqueue = self.db_name + ":" + "maxqueue"
		mq_db.remove(key_maxqueue)
		# sync to database
		mq_db.sync()
		# "0" means resetting successfully
		return 0
	

	def mq_set_maxqueue(self):
		"""set 'maxqueue'"""
		put_pos = 0
		get_pos = 0
		put_pos = self.read_put_pos()
		get_pos = self.read_get_pos()
		# The new 'maxqueue' must be more than current 'put' position and
		# 'get' position
		if self.maxqueue >= put_pos and self.maxqueue >= get_pos:
			# The current 'put' position must be more than 'get' position
			# otherwise the data have not be read could be override if new
			# "maxqueue' is less than old 'maxqueue'
			if put_pos >= get_pos:
				key_maxqueue = self.db_name + ":" + "maxqueue"
				mq_db.put(key_maxqueue, self.maxqueue)
				mq_db.sync()
				return self.maxqueue
			
	@staticmethod
	def mq_set_synctime(self):
		"""set 'synctime'"""
		if self.synctime >= 1:
			config.CONFIG_INTERVAL = self.synctime
			return config.CONFIG_INTERVAL
	
	
	def get_args(self):
		"""receive argument from URL"""
		# auth code(string)
		self.auth = self.decode_argument(self.get_argument("auth"))
		# queue name(number)
		self.db_name = self.decode_argument((self.get_argument("name")))
		# option type(string)
		self.opt_type = str(self.get_argument("opt"))
		# charset(string)
		self.charset = self.get_argument("charset")
		# data (string)
		self.data = self.decode_argument(self.get_argument("data"))
		# position in queue(number)
		self.position = int(self.get_argument("pos"))
		# max queue number(number)
		self.queue_num = int(self.get_argument("num"))
		# synctime(second, 1 <= synctime <= 1000000)
		self.synctime = int(self.get_argument("time"))
		
	
	def set_headers(self):
		"""set headers of response"""
		if self.charset and (len(self.charset) <= 40):
			new_charset = "text/plain; charset=%s" % self.charset
			self.set_header("Content-type", new_charset)
		else:
			self.set_header("Content-type", "text/plain")
		self.set_header("Connection", "keep-alive")
		self.set_headr("Cache-Control",
					   "no-cache")
		
		
	def do_auth(self):
		"""request authentication"""
		is_authenticated = False
		if config.CONFIG_AUTH is not None:
			if self.auth is not None:
				if self.auth == config.CONFIG_AUTH:
					is_authenticated = True
				else:
					is_authenticated = False
		# if config_auth has not set
		else:
			is_authenticated = True

		# if authentication fails
		if not is_authenticated:
			self.write("HTTPmq authentication failed.")
			self.finish()
		# if authentication succeed
		return is_authenticated


def child_signal_handler(a, b):
	"""handle signal of child process"""
	mq_db.sync()
	mq_db.close()
	os._exit(os.EX_OK)
	

def worker_signal_handler(a, b):
	"""handle signal of worker process"""
	os.kill(0, signal.SIGTERM)
	os._exit(os.EX_OK)
	
def sync_handler():
	"""sync data from memory to disk"""
	while True:
		time.sleep(config.CONFIG_INTERVAL)
		mq_db.sync()


def show_help():
	"""show 'help' for manager"""
	print("""
		  HTTP Message Queue Service \n
		  2016-4-15 \n
		  \n
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
		  """
			)


def version():
	"""return current version"""
	print("The version is: %s" % config.CONFIG_VERSION)


def main():
	# get current work directory
	# current_work_dir = os.getcwd()
	# prase arguments
	op = optparse.OptionParser()
	op.add_option("-a", "--address", action="store", dest="address")
	op.add_option("-p", "--port", action="store", type="int", dest="port")
	op.add_option("-l", "--log", action="store", type="string", dest="log")
	op.add_option("-b", "--dbpath", action="store", type="string", dest="dbpath")
	op.add_option("-t", "--timeout", action="store", type="int", dest="timeout")
	op.add_option("-i", "--interval", action="store", type="int", dest="interval")
	op.add_option("-a", "--auth", action="store", type="string", dest="auth")
	op.add_option("-d", "--daemon", action="store_true", dest="daemon")
	op.add_option("-n", "--name", action="store", type="string", dest="proc_name")
	op.add_option("-h", "--help", action="store_true", dest="help")
	op.add_option("-v", "--version", action="store_true", dest="version")
	op.set_defaults(address="0.0.0.0", port=1234, path="/tmp/", timeout=5,
					interval=5, file="/tmp/", auth=1234, daemon=False)
	option, args = op.parse_args()
	if op.address:
		config.CONFIG_ADDRESS = op.address
	elif op.port:
		config.CONFIG_PORT = op.port
	 # timeout
	elif op.timeout:
		config.CONFIG_TIMEOUT = op.timeout
	elif op.interval:
		config.CONFIG_INTERVAL = op.interval
	elif op.auth:
		config.CONFIG_AUTH = op.auth
	elif op.daemon:
		config.CONFIG_DAEMON = True
	elif op.proc_name:
		config.CONFIG_NAME = op.proc_name
	elif op.help:
		show_help()
	elif op.version:
		version()
	else:
		pass
	if op.log:
		config.CONFIG_LOG = op.log
		if os.path.isdir(config.CONFIG_LOG):
			if not os.access(config.CONFIG_LOG, os.W_OK):
				if os.access(config.CONFIG_LOG, os.R_OK):
					os.chmod(config.CONFIG_LOG, stat.S_IWOTH)
				else:
					os.chmod(config.CONFIG_LOG, stat.S_IROTH)
					os.chmod(config.CONFIG_LOG, stat.S_IWOTH)
		else:
			os.makedirs(config.CONFIG_LOG)
	else:
		show_help()
		print("Please input the path of log, use -p <path> or --path <path>")
		os._exit(os.EX_SOFTWARE)
	if op.dbpath:
		config.CONFIG_DB_PATH = op.dbpath
		if os.path.isdir(config.CONFIG_DB_PATH):
			if not os.access(config.CONFIG_DB_PATH, os.W_OK):
				if os.access(config.CONFIG_DB_PATH, os.R_OK):
					os.chmod(config.CONFIG_DB_PATH, stat.S_IWOTH)
				else:
					os.chmod(config.CONFIG_DB_PATH, stat.S_IROTH)
					os.chmod(config.CONFIG_DB_PATH, stat.S_IWOTH)
		else:
			os.makedirs(config.CONFIG_DB_PATH)
	else:
		show_help()
		print("Please input the path of database, use -b <path> or --dbpath <path>")
		os._exit(os.EX_SOFTWARE)
	# create db Tokyo cabinnet
	mq_db_cache_nonleaf = 1024
	mq_db_cache_leaf = 2048
	mq_db_mapped_memory = 104857600
	mq_db_path = config.CONFIG_DB_PATH + "/mq.db"
	global mq_db = BDB()
	mq_db.tune(50000000, 8, 10, BDBTLARGE)
	mq_db.setcache(, mq_db_cache_leaf, mq_db_cache_nonleaf)
	mq_db.setxmsiz(mq_db_mapped_memory)
	
	# test database
	if not mq_db.open(mq_db_path, TDBOWRITER|TDBOCREAT):
		print("unable to open database file!")
		show_help()
		os._exit(os.EX_SOFTWARE)
	
	# create db Redis
	# pool = redis.ConnectionPool(host='localhost', port=None, db=10)
	# re = redis.Redis(connection_pool=pool)
	# re.config_set(maxmemory, 104857600)
	# firstly forking
	if config.CONFIG_DAEMON:
		# daemon_process = daemonProcess()
		# daemon_process.start()
		pid = os.fork()
		if pid < 0:
			os._exit(os.EX_SOFTWARE)
		# main process quit
		if pid > 0:
			os._exit(os.EX_OK)
	# start child process:
	os.setsid()
	os.umask(0)
	# rename
	pname = config.CONFIG_NAME
	setproctitle.setproctitle(pname)
	# secondly forking
	pid2 = os.fork()
	if pid2 < 0:
		print("Error of forking process!")
		os._exit(os.EX_SOFTWARE)
	# child process:
	if pid > 0:
		# ignore signal handler
		signal.signal(signal.SIGPIPE, signal.SIG_IGN)
		
		# interupt or kill or terminate or hungup or quit
		# os.signal(SIGINT, child_signal_handler)
		signal.signal(signal.SIGINT, child_signal_handler)
		# os.signal(SIGKILL, child_signal_handler)
		signal.signal(signal.SIGKILL, child_signal_handler)
		# os.signal(SIGQUIT, child_signal_handler)
		signal.signal(signal.SIGQUIT, child_signal_handler)
		# os.signal(SIGTERM, child_signal_handler)
		signal.signal(signal.SIGTERM, child_signal_handler)
		# os.signal(SIGHUP, child_signal_handler)
		signal.signal(signal.SIGHUP, child_signal_handler)
		# segament fault
		# os.signal(SIGSEGV, child_signal_handler)
		signal.signal(signal.SIGSEGV, child_signal_handler)
		# child process:
		while True:
			pid2_wait = os.wait()
			if pid2_wait < 0:
				continue
			time.sleep(100000)
			pid2 = os.fork()
			if pid2 == 0:
				# if worker process was terminated, break loop and jump to Start:
				break
	
	# Start : start httpmq worker process
	# ignaore handler
	signal.signal(signal.SIGPIPE, signal.SIG_IGN)
	# process interupt or kill or quit or terminate
	# os.signal(SIGINT, worker_signal_handler)
	signal.signal(signal.SIGINT, worker_signal_handler)
	# os.signal(SIGKILL, worker_signal_handler)
	signal.signal(signal.SIGKILL, worker_signal_handler)
	# os.signal(SIGQUIT, worker_signal_handler)
	signal.signal(signal.SIGQUIT, worker_signal_handler)
	# os.signal(SIGTERM, worker_signal_handler)
	signal.signal(signal.SIGTERM, worker_signal_handler)
	# os.signal(SIGHUP, worker_signal_handker)
	signal.signal(signal.SIGHUP, worker_signal_handler)
	
	# process segament fault
	# os.signal(SIGSERV, worker_signal_handler)
	signal.signal(signal.SIGSERV, worker_signal_handler)
	# create sync thread
	sync_thread = threading.Thread(target=sync_handler, args=None)
	sync_thread.run()
	# rename httpmq worker process
	pname = config.CONFIG_NAME
	setproctitle.setproctitle(pname)
	
	# start handle http request:
	application = tornado.web.Application(r"/", HttpmqHandler)
	application.listen(config.CONFIG_PORT)
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.listen(config.CONFIG_PORT)
	tornado.ioloop.IOLoop.instance().start()
	
	
if __name__ == "__main__":
	main()




