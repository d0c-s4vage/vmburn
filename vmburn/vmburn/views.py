from django.http import HttpResponse
from django.shortcuts import render
import json
import re
import os
import subprocess
import time
import socket
from django.views.decorators.csrf import csrf_exempt
from threading import Thread
import random

def home(request):
	vms = ["TESTING1", "TESTING2", "TESTING3"]
	return render(request, "home.htm", {"vms": vms})

	
# -----------------------------------------------
# -----------------------------------------------
# -----------------------------------------------
# -----------------------------------------------
# -----------------------------------------------	
# -----------------------------------------------	

def run_command(cmd):
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout,stderr = p.communicate()
	return stdout,stderr
	
# -----------------------------------------------
# -----------------------------------------------
# -----------------------------------------------
# -----------------------------------------------
# -----------------------------------------------	
# -----------------------------------------------	

def js_response(data):
	return HttpResponse(json.dumps(data), content_type="application/json")

def get_available_vms():
	stdout,stderr = run_command(["VBoxManage", "list", "hdds"])
	
	available_vms = []
	for hdd_info in stdout.split(os.linesep*2):
		hdd_info = hdd_info.replace(os.linesep, "|||")
		match = re.match(r'UUID:\s*([\w-]*).*Location:\s*(.*\.vdi).*Type:\s*(\w*)', hdd_info)
		#match = re.match(r'.*Type:\s*(\w*).*Usage:\s*([\w\s]*) \(UUID: (.*)\)', hdd_info)
		if match is None:
			continue
		
		hdd_uuid,location,hdd_type = match.groups()
		
		if hdd_type != "immutable":
			continue
		
		hdd_name = os.path.basename(location).replace(".vdi", "")
		
		available_vms.append({
			"name": hdd_name,
			"path": location,
			"uuid": hdd_uuid,
		})
	
	#available_vms.append({
		#"name": "TAILS",
		#"uuid": available_vms[0]["uuid"],
		#"path": available_vms[0]["path"],
	#})
	
	return available_vms
	
@csrf_exempt
def api_vms(request):
	available_vms = get_available_vms()

	# don't need to be sending that info everywhere
	for x in available_vms:
		if "path" in x:
			del x["path"]
	
	available_vms.append({
		"name": "RANDOM",
		"uuid": "XXXXXX",
	})
	
	return js_response(available_vms)

def api_usb_devices(request):
	stdout,stderr = run_command(["VBoxManage", "list", "usbhost"])
	#stdout,stderr = run_command('VBoxManage usbfilter add 0 -target "%s" -name "Dell Laser Printer 1700" -vendorid 413C -productid 5202 -revision 0100 -manufacturer Dell -product "Dell Laser Printer 1700" -serialnumber 72253CR' % (new_vm_name))
	#stdout,stderr = run_command('VBoxManage controlvm "%s" usbattach ffe31169-975a-4272-bafe-af8188de4bc0' % (new_vm_name))
	
	devs = stdout.split(os.linesep*2)
	
	res = []
	for dev_str in devs:
		dev_res = {}
		dev_str = dev_str.replace(os.linesep, "|||")
		if dev_str == "Host USB Devices:":
			continue
		
		match = re.match(r".*UUID:\s*([a-f0-9\-]+)\|\|\|", dev_str)
		if match is None:
			continue
		dev_res["uuid"] = match.groups()[0]

		match = re.match(r".*VendorId:\s*0x.... \((.{4})\)\|\|\|", dev_str)
		dev_res["vendor_id"] = match.groups()[0]

		match = re.match(r".*ProductId:\s*0x.... \((.{4})\)\|\|\|", dev_str)
		dev_res["product_id"] = match.groups()[0]

		match = re.match(r".*Revision:\s*[0-9\.]+\s*\(([^\s]*)\)\|\|\|", dev_str)
		if match is None:
			print dev_str
			import pdb ; pdb.set_trace()
		dev_res["revision"] = match.groups()[0]

		match = re.match(r".*Product:\s*([^\|]+)\|\|\|", dev_str)
		dev_res["name"] = match.groups()[0]

		match = re.match(r".*Manufacturer:\s*([^\|]+)\|\|\|", dev_str)
		if match:
			dev_res["manufacturer"] = match.groups()[0]
		else:
			dev_res["manufacturer"] = "Generic"
			
		match = re.match(r".*SerialNumber:\s*([^\|]+)\|\|\|", dev_str)
		if match:
			dev_res["serial_number"] = match.groups()[0]
		
		res.append(dev_res)
	
	return js_response(res)

def get_vm_path(uuid):
	all_vms = get_available_vms()
	for vm_info in all_vms:
		if vm_info["uuid"] == str(uuid):
			return str(vm_info["path"])

def get_available_audio_args():
	cmd = [
		'VBoxManage', '--help',
	]
	stdout,stderr = run_command(cmd)

	match = re.match(r".*\[--audio\s+([^\s]*)\]", stdout, re.MULTILINE|re.DOTALL)
	if match:
		return match.group(1).split("|")

def create_tmp_vm(name, hd_path, memory=2048, cpus=2, vram=56, tails_boot=False, usb_devices=None):
	vm_ports = ",".join([str(x) for x in range(3389,3389+100)])
	name = str(name)
	
	if usb_devices is None:
		usb_devices = []

	cmd = [
		'VBoxManage',
			'createvm',
			'--name', name,
			'--register'
	]

	ostype = ""
	if name.find("Windows 7") != -1:
		ostype = "Windows7"
	elif name.find("Ubuntu") != -1:
		ostype = "Ubuntu"
	elif name.find("Fedora") != -1:
		ostype = "Fedora"
	
	if "x64" in name and ostype != "":
		ostype += "_64"
	
	if ostype != "":
		cmd += ["--ostype", ostype]
	
	stdout,stderr = run_command(cmd)

	stdout = stdout.replace(os.linesep, "        ")

	match = re.match(r'.*UUID: ([\w-]*)', stdout)
	new_uuid = match.group(1)

	audio_args = get_available_audio_args()
	# the first two available args are always none, and null, so
	# try use something else
	audio_arg = audio_args[-1]

	modify_opts = [
		"--memory", str(memory),
		"--acpi", "on",
		"--pae", "on",
		"--nic1", "nat",
		"--cpus", str(cpus),
		"--nictype1", "82540EM",
		"--ioapic", "on",
		"--vram", str(vram),
		"--audio", audio_arg,
		"--audiocontroller", "hda",
		"--vrde", "on",
		"--vrdeport", vm_ports,
		"--usb", "on",
		"--usbehci", "on", # for usb 2.0 - need extension pack installed though
		#"--accelerate3d", "on", # TODO: Find a way to determine if this is supported
		"--hwvirtex", "on",
	]
	
	sata_port_count = 1
	
	if tails_boot:
		sata_port_count = 2
		modify_opts += [
			"--boot1", "dvd",
			"--boot2", "disk",
			"--boot3", "none"
		]
	
	modify_cmd = [
		'VBoxManage',
			'modifyvm', name,
	] + modify_opts
	stdout,stderr = run_command(modify_cmd)

	stdout,stderr = run_command([
		'VBoxManage',
			'storagectl', name,
				'--name', "SATA CONTROLLER",
				'--add',  'sata',
				'--sataportcount', str(sata_port_count),
				'--controller', 'IntelAHCI',
				'--bootable', 'on'
	])
	stdout,stderr = run_command([
		'VBoxManage',
			'storageattach', name,
				'--storagectl', "SATA CONTROLLER",
				'--port', '0',
				'--device', '0',
				'--type', 'hdd',
				'--medium', hd_path
	])
	
	if tails_boot:
		tails_path = r"C:\Users\nephi\__ws__\software\os\linux\tails-i386-0.16.iso"
		stdout,stderr = run_command([
			'VBoxManage',
				'storageattach', name,
					'--storagectl', "SATA CONTROLLER",
					'--port', '1',
					'--device', '0',
					'--type', 'dvddrive',
					'--medium', tails_path
		])
	
	for dev in usb_devices:
		cmd = [
			'VBoxManage',
				'usbfilter', 'add', '0',
					'-target', name,
					'-name', dev["name"],
					'-vendorid', dev["vendor_id"],
					'-productid', dev["product_id"],
					'-revision', dev["revision"],
					'-manufacturer', dev["manufacturer"],
					'-product', dev["name"],
		]
		if "serial_number" in dev:
			cmd += ['-serialnumber', dev["serial_number"]]

		stdout, stderr = run_command(cmd)
		stdout,stderr = run_command([
			'VBoxManage',
				'controlvm', name, 'usbattach', dev["uuid"]
		])
		

def get_vrde_port(vm_name):
	stdout,stderr = run_command([
		'VBoxManage', 'showvminfo', vm_name
	])
	stdout = stdout.replace(os.linesep, "||||")
	
	match = re.match(r'.*VRDE port:\s*(\d*)', stdout)

	if match is None:
		return 55555
		#import pdb ; pdb.set_trace()
	
	return int(match.group(1))
	
def vrde_is_connected(vm_name):
	stdout,stderr = run_command(['VBoxManage', 'showvminfo', vm_name])
	stdout = stdout.replace(os.linesep, "||||")
	
	match = re.match(r'.*VRDE Connection:\s*([\w\s]*)\|\|\|\|', stdout)
	connected = match.group(1)
	
	return connected != "not active"

def is_powered_off(vm_name):
	stdout,stderr = run_command(['VBoxManage', 'showvminfo', vm_name])
	stdout = stdout.replace(os.linesep, "||||")
	
	match = re.match(r'.*State:\s*powered off', stdout)
	return match is not None
	
def thread_shutdown_when_inactive(vm_name, max_time, close_on_disconnect):
	start_time = time.time()
	was_connected = False
	
	while True:
		# they shutdown the vm
		if is_powered_off(vm_name):
			break
	
		curr_time = time.time()
		if not was_connected and vrde_is_connected(vm_name):
			print("%s IS NOW ACTIVE" % vm_name)
			was_connected = True
		
		# they were connected, but now they're not, so shut it
		# down
		if close_on_disconnect and was_connected and not vrde_is_connected(vm_name):
			print("%s HAS BEEN DISCONNECTED" % vm_name)
			break
		
		# they've exceeded their time limit to connect to the vm,
		# so shut it down
		if max_time != -1 and not was_connected and (curr_time - start_time) > max_time:
			print("TOOK TOO LONG TO CONNECT TO '%s'" % vm_name)
			break
		
		time.sleep(5)
	
	print("SHUTTING '%s' DOWN" % vm_name)
	stdout,stderr = run_command(['VBoxManage', 'controlvm', vm_name, 'poweroff'])
	stdout,stderr = run_command(['VBoxManage', 'unregistervm', vm_name,  '--delete'])

@csrf_exempt
def api_kill_vm(request, uuid):
	print("SHUTTING '%s' DOWN" % uuid) 

	stdout,stderr = run_command(['VBoxManage', 'controlvm', uuid, 'poweroff'])
	# still let the watcher thread delete and clean up
	#stdout,stderr = run_command('VBoxManage unregistervm "%s" --delete' % (uuid))

	return js_response("OK");
	
@csrf_exempt
def api_running_vms(request):
	"""
	Should return the vm name, some info about it, and the connection info
	"""
	stdout,stderr = run_command(['VBoxManage', 'list', 'runningvms'])
	
	vms = []
	
	for line in stdout.split("\n"):
		match = re.match(r'.*"(.*) -- [a-f0-9]{8}" \{(.*)\}', line)
		if match is None:
			continue

		name,uuid = match.groups()
		vm_info = {
			"name": name,
			"uuid": uuid,
		}
		
		stdout,stderr = run_command(['VBoxManage', 'showvminfo', uuid])
		# Number of CPUs:  2
		# VRDE port:       3389
		# Memory size:     2048MB
		# VRAM size:       56MB
		stdout = stdout.replace(os.linesep, "|||")
		
		vrde_match = re.match(r'.*VRDE port:\s*(\d*)', stdout)
		if vrde_match is not None:
			host = request.META["HTTP_HOST"]
			if re.match(r".*\:\d+", host):
				host = host.split(":")[0]

			vm_info["connect"] = "rdp://%s:%d" % (
				host,
				int(vrde_match.groups()[0])
			)
		else:
			vm_info["connect"] = "VRDE NOT ENABLED"
			
		cpu_match = re.match(r".*Number of CPUs:\s*(\d+)", stdout)
		if cpu_match is not None:
			vm_info["cpus"] = int(cpu_match.groups()[0])
			
		memory_match = re.match(r".*Memory size:\s*(\d+)MB", stdout)
		if memory_match is not None:
			vm_info["memory"] = int(memory_match.groups()[0])
			
		vram_match = re.match(r".*VRAM size:\s*(\d+)MB", stdout)
		if vram_match is not None:
			vm_info["vram"] = int(vram_match.groups()[0])
		
		vms.append(vm_info)

	return js_response(vms)
	
@csrf_exempt
def api_startvm(request):
	hdd_info = json.loads(request.body)

	if hdd_info["name"] == "RANDOM":
		hdd_info = random.choice(get_available_vms())
	
	hdd_info.setdefault("printer", False)
	hdd_info.setdefault("ram", 2048)
	hdd_info.setdefault("vram", 56)
	hdd_info.setdefault("cpu_cores", 2)
	hdd_info.setdefault("usb_devices", [])
	hdd_info.setdefault("connect_timeout", 60*5)
	hdd_info.setdefault("close_on_disconnect", True)

	path = get_vm_path(hdd_info["uuid"])

	new_vm_name = "%s -- %08x" % (hdd_info["name"], random.randint(0, 0xffffffff))
	create_tmp_vm(new_vm_name, path,
		tails_boot=(hdd_info["name"] == "TAILS"),
		memory=hdd_info["ram"],
		cpus=hdd_info["cpu_cores"],
		vram=hdd_info["vram"],
		usb_devices=hdd_info["usb_devices"]
	)

	stdout,stderr = run_command([
		'VBoxManage',
			'startvm', new_vm_name,
				'--type', 'headless'
	])
	port = get_vrde_port(new_vm_name)	
	
	# user has five minutes to connect to vm, otherwise it gets
	# shutdown and cleaned up
	Thread(
		target=thread_shutdown_when_inactive, 
		args=(
			new_vm_name,
			hdd_info["connect_timeout"],
			hdd_info["close_on_disconnect"]
		)
	).start()
	
	return js_response({"port": port, "name": new_vm_name})

def api_vms_old(request):
	cmd = "VBoxManage list vms"
	p = Popen(cmd, stdout=PIPE, stderr=PIPE)
	stdout,stderr = p.communicate()
	
	vms = []
	for vm_desc in stdout.split("\n"):
		match = re.match(r'^"(.*)" {(.*)}', vm_desc)
		if match is None:
			continue
		vms.append({
			"name": match.group(1),
			"uuid": match.group(2),
		})
	
	return js_response(vms)
