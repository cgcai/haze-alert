#!/usr/bin/env python

from urllib import urlencode
from os.path import expanduser
from datetime import datetime
import argparse
import json
import urllib2

_VERBOSE = False
_APP_NAME = "hazealert"
_HOIIO_SMS_API = "https://secure.hoiio.com/open/sms/send"
_ALERT_MSG = "The official 3-hour PSI is now {psi} as of {time}. "
_ALERT_BEGIN = "These alerts will continue until PSI falls below {threshold}. "
_ALERT_END = "No further alerts will be sent. "

def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-v", "--verbose", action="store_true", help="turns on console output")
	parser.add_argument("-t", "--test", action="store_true", help="test mode. Prints API call but does not send SMS. Always prints regardless of --verbose")
	parser.add_argument("-u", "--url", action="store_true", help="specify to treat the datasource as a URL")
	parser.add_argument("-i", "--identity", default="~/.hoiioapi", help="Hoiio API identity file to use. Default: ~/.hoiioapi")
	parser.add_argument("scratch", help="haze-alert scratch file")
	parser.add_argument("datasource", help="the file from which PSI data should be loaded. Specify --url if the datasource is a URL")
	parser.add_argument("threshold", type=float, help="the PSI threshold above with an alert should be sent")
	args = parser.parse_args()
	return args

def main():
	args = get_args()

	global _VERBOSE
	if args.verbose:
		_VERBOSE = True

	# Try to load Hoiio credentials or fail.
	id_path = expanduser(args.identity)
	cred = read_credentials(id_path)
	if not cred:
		log("Unable to load Hoiio credentials.")
		return
	else:
		log("Hoiio Credentials: " + str(cred))
		appid, token, dest = cred

	# Load the latest PSI or fail.
	if args.url:
		ds = json_from_url(args.datasource)
	else:
		ds = json_from_file(args.datasource)
	if not ds:
		log("Unable to load PSI data.")
		return

	# Parse the loaded data, read old value from scratch file.
	# Note: if the scratch file did not exist or was corrupt, a zero-tuple is returned.
	cur_ts, cur_val = get_psi_info(ds)
	last_ts, last_val = get_scratch_info(args.scratch)

	# Exit if we have nothing new to report.
	if cur_ts == last_ts:
		return

	# If there is no current value ("null"), report the previous time/value.
	using_last = False
	if cur_val == None:
		cur_ts, cur_val = last_ts, last_val
		using_last = True

	# Note: humans don't like UNIX timestamps.
	# Note: We strip() every message to save characters.
	human_time = datetime.fromtimestamp(cur_ts).strftime("%H:%M")
	if cur_val >= args.threshold:
		# Send an alert if PSI is above threshold.

		msg = _ALERT_MSG.format(psi=cur_val, time=human_time)
		if last_val < args.threshold:
			# If PSI is above threshold for the first time, also inform the user that updates have started.

			msg += _ALERT_BEGIN.format(threshold=args.threshold)

		send_sms(appid, token, dest, msg.strip(), testmode=args.test)
	elif last_val >= args.threshold:
		# If PSI fell below the threshold, send one last alert, and inform the user that no further alerts will be sent.

		msg = _ALERT_MSG.format(psi=cur_val, time=human_time) + _ALERT_END
		send_sms(appid, token, dest, msg.strip(), testmode=args.test)
	
	# Save the latest data to the scratch file.
	# Note: the old scratch file is truncated and re-written.
	update_scratch_info(args.scratch, cur_ts, cur_val)

def update_scratch_info(path, ts, val):
	struct = {
		"last_ts": ts,
		"last_val": val
	}

	with open(path, "w") as f:
		f.write(json.dumps(struct))

def get_scratch_info(path):
	try:
		with open(path, "r") as f:
			dat = f.read()
		struct = json.loads(dat)
		if struct and struct["last_ts"] and struct["last_val"]:
			return (int(struct["last_ts"]), float(struct["last_val"]))
		else:
			return (0, 0.0)
	except IOError:
		return (0, 0.0)

def get_psi_info(ds):
	base_date = ds["date"]
	update_key = ds["last_update"]
	current_value = ds["history"][unicode(update_key)]
	if current_value:
		current_value = float(current_value)
	current_time = int(base_date) + int(update_key) * 3600
	return (current_time, current_value)

def json_from_url(url):
	try:
		raw_contents = urllib2.urlopen(url).read()
		struct = json.loads(raw_contents)
		if struct:
			return struct
		else:
			return None
	except Exception:
		return None

def json_from_file(path):
	try:
		with open(path, "r") as f:
			dat = f.read()
		struct = json.loads(dat)
		if struct:
			return struct
		else:
			return None
	except IOError:
		return None

def read_credentials(path):
	try:
		with open(path, "r") as f:
			dat = f.read()
		struct = json.loads(dat)
		app_settings = struct[_APP_NAME]
		if app_settings and app_settings["appid"] and app_settings["token"] and app_settings["number"]:
			return (app_settings["appid"], app_settings["token"], app_settings["number"])
		else:
			return None
	except IOError:
		return None

def send_sms(appid, token, dest, message, testmode=False):
	request_data = {
		"app_id" : appid,
		"access_token" : token,
		"dest" : dest,
		"msg" : message
	}

	url = _HOIIO_SMS_API + "?" + urlencode(request_data)
	if testmode:
		log("Test Mode: " + url, always=True)
	else:
		req = urllib2.Request(url)
		resp_data = urllib2.urlopen(req).read()

		resp = json.loads(resp_data)
		if "status" in resp.keys() and resp["status"] == "success_ok":
			log("SMS sent.")
		else:
			log("Failed to send SMS.")

def log(message, always=False):
	if _VERBOSE or always:
		print message

if __name__ == "__main__":
	main()