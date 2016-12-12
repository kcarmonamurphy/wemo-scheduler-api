from flask import Flask
from subprocess import STDOUT, check_output, call
import re
import json

app = Flask(__name__)

app.config['DEBUG'] = True
app.config.from_pyfile('.env')

queues = {
	"a": "toggle",
	"b": "on",
	"c": "off"
}

inv_queues = {v: k for k, v in queues.items()}

'''
Each API route returns a JSON formatted array in the format of `{ result_code: output }`
where `result_code` can either be a `0` (success) or a `1` (failure),
and the `output` describes either the appropriate json return value or the error message
'''

@app.route('/status')
def status():
	endpoint = "/api/environment"
	output = check_output(["curl", "-u", "light:switch", "-X", "GET", app.config['BASE_URL'] + endpoint])
	if output == {}:
		return json.dumps({"1": "no devices found"})
	return json.dumps({"0": json.loads(output)})

@app.route('/status/<device>')
def device(device):
	endpoint = "/api/environment"
	output = json.loads(check_output(["curl", "-u", "light:switch", "-X", "GET", app.config['BASE_URL'] + endpoint]))
	try:
		for key, value in output.items():
			if (key == device):
				return json.dumps({"0": "found " + device})
	except:
		pass
	return json.dumps({"1": device + " not found"})	

@app.route('/set/<device>/<action>/<HH>/<MM>')
def set(device, action, HH, MM):
	time = HH + ":" + MM
	if int(HH) > 23 or int(MM) > 59: return json.dumps({"1": "time is out of bounds"})
	output = check_output([app.config['WEMO_CURL'], app.config['BASE_URL'], device, action, inv_queues[action], time], stderr=STDOUT)
	if (re.search('(?<=job )[0-9]+', output).group(0)):
		return json.dumps({"0": re.search('(?<=job )[0-9]+', output).group(0)})
	else:
		return json.dumps({"1": json.loads(output)})

@app.route('/set/<device>/<action>/now')
def now(device, action):
	output = check_output([app.config['WEMO_CURL'], app.config['BASE_URL'], device, action, "a", "now"], stderr=STDOUT)
	if (re.search('(?<=job )[0-9]+', output).group(0)):
		return json.dumps({"0": re.search('(?<=job )[0-9]+', output).group(0)})
	else:
		return json.dumps({"1": json.loads(output)})

@app.route('/queue')
def queue():
	dictionary = {}
	for queue in queues.keys():
		output = check_output(["atq", "-q", queue])
		times = re.findall('\t(.*?):\d{2}\s\d{4}', output)
		job_ids = re.findall('([0-9]+)\t', output)
		dictionary.update(dict(zip(job_ids, [dict([["action",queues[queue]],["time",t]]) for t in times])))
	if dictionary == {}:
		return json.dumps({"1": "no jobs scheduled"})
	return json.dumps({"0": dictionary})

@app.route('/unset/<jobid>')
def unset(jobid):
	status = call(["atrm", jobid])
	return json.dumps({status: "failure" if status else "success"})

if __name__ == '__main__':
	app.run(host= '0.0.0.0', port=4989)
