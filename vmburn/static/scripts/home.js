
function Vm(vm_info) {
	var _self = this;

	this.vm_info = vm_info;
	this.name = vm_info.name;
	this.uuid = vm_info.uuid;
	this.path = vm_info.path;

	this.running_vms = [];
	
	this.dom = null;
	this.dom_info_table = null;
	this.dom_name = null;
	this.dom_status = null;
	this.dom_uuid = null;
	this.dom_path = null;
	this.dom_start = null;
	
	var _create_row_label = function(append_to, label, label_class) {
		/***
		Creates a </td><td>LABEL</td><td></td></tr>, appends it to "append_to", and returns
		the second, empty, <td>
		***/
		var row = $("<tr>");
		row.css("background-color: transparent");
		append_to.append(row);
		
		var label_td = $("<td>");
		label_td.text(label);
		label_td.addClass(label_class);
		row.append(label_td);
		
		var empty_td = $("<td>");
		row.append(empty_td);
		return empty_td;
	}
	
	this.start_vm = function() {
		var new_info = jQuery.extend(true, {}, _self.vm_info);
		_self.add_options(new_info);
		$.ajax({
			url: "/api/startvm",
			type: "POST",
			data: JSON.stringify(new_info),
			processData: false,
			dataType: "json",
			contentType: "application/json",
			success: _self.start_vm_success,
		});
	}
	
	this.add_options = function(obj) {
		obj["ram"] = parseInt(_self.dom_config_ram.val());
		obj["vram"] = parseInt(_self.dom_config_vram.val());
		obj["cpu_cores"] = parseInt(_self.dom_config_cpu_cores.val());
		obj["connect_timeout"] = parseInt(_self.dom_config_connect_timeout.val());
		obj["close_on_disconnect"] = this.dom_close_on_disconnect.is(":checked");
		
		obj["usb_devices"] = []
		for(x in _self.usb_devices) {
			var checkbox = _self.usb_devices[x];
			if(!checkbox.is(":checked")) {
				continue;
			}
			obj["usb_devices"].push(USB_DEVICES[checkbox.val()]);
		}
	}
	
	this.start_vm_success = function(start_info) {
		//_self.running_vms.push(start_info);
		//_self.dom_status.text("RUNNING @ 172.29.0.102:" + start_info["port"]);
		update_running_vms();
	}
	
	this.create_html = function() {
		this.dom = $("<div>");
		this.dom.addClass("vm");
		
		this.dom_name = $("<div>");
		this.dom_name.text(this.name);
		this.dom_name.addClass("vm_name");
		this.dom.append(this.dom_name);
		
		this.dom_status = $("<span>");
		this.dom_status.addClass("vm_status");
		this.dom.append(this.dom_status);
		
		this.dom_start = $("<button>");
		this.dom_start.text("START");
		this.dom_start.addClass("vm_start")
		this.dom.append(this.dom_start);
		this.dom_start.click(this.start_vm);
		
		this.dom_info_table = $("<table>");
		this.dom_info_table.addClass("vm_info");
		this.dom.append(this.dom_info_table)
		
		this.dom_path = _create_row_label(this.dom_info_table, "uuid", "vm_info_label");
		this.dom_path.addClass("vm_info_item");
		this.dom_path.text(this.uuid);
		
		this.create_config();
		
		return this.dom;
	}
	
	this.expand_hide_options = function() {
		_self.dom_options_table_div.slideToggle(300, function() {
			if(_self.dom_options_table.is(":visible")) {
				_self.dom_options_expander.text("[-] hide");
			} else {
				_self.dom_options_expander.text("[+] configure");
			}
		});
	}
	
	this.create_config = function() {
		this.dom_options = $("<div>");
		this.dom.append(this.dom_options);
		
		this.dom_options_expander = $("<a>");
		this.dom_options_expander.href = "#";
		this.dom_options_expander.text("[+] configure");
		this.dom_options_expander.addClass("config_expander");
		this.dom_options_expander.click(this.expand_hide_options);
		this.dom_options.append(this.dom_options_expander);
		
		this.dom_options_table_div = $("<div>", {style: "display:none"});
		this.dom_options.append(this.dom_options_table_div);
		
		this.dom_options_table = $("<table>");
		this.dom_options_table.addClass("options_table");
		this.dom_options_table_div.append(this.dom_options_table);
		
		this.dom_config_ram = $("<input>", {type: "text"});
		this.dom_config_ram.val("2048");
		var td = _create_row_label(this.dom_options_table, "ram", "options_label");
		td.append(this.dom_config_ram);	
		
		this.dom_config_vram = $("<input>", {type: "text"});
		this.dom_config_vram.val("56");
		var td = _create_row_label(this.dom_options_table, "vram", "options_label");
		td.append(this.dom_config_vram);
		
		this.dom_config_cpu_cores = $("<input>", {type: "text"});
		this.dom_config_cpu_cores.val("2");
		var td = _create_row_label(this.dom_options_table, "cpu cores", "options_label");
		td.append(this.dom_config_cpu_cores);
		
		this.dom_config_connect_timeout = $("<input>", {type: "text"});
		this.dom_config_connect_timeout.val("300");
		var td = _create_row_label(this.dom_options_table, "connect timeout (-1 = INF)", "options_label");
		td.append(this.dom_config_connect_timeout);
		
		this.dom_close_on_disconnect = $("<input>", {type: "checkbox", value: "close_on_disconnect"});
		this.dom_close_on_disconnect.val("close_on_disconnect");
		this.dom_close_on_disconnect.addClass("padded_checkbox");
		this.dom_close_on_disconnect.prop("checked", true);
		var td = _create_row_label(this.dom_options_table, "close on disconnect", "options_label");
		td.append(this.dom_close_on_disconnect);
		
		this.usb_devices = [];
		for(x in USB_DEVICES) {
			var dev = USB_DEVICES[x];
			var checkbox = $("<input>", {type: "checkbox", value: dev["name"]});
			checkbox.val(dev["name"]);
			checkbox.addClass("padded_checkbox");
			var desc = $("<span>");
			desc.addClass("options_usb_text");
			desc.text(dev["name"]);
			var td = _create_row_label(this.dom_options_table, "USB DEVICE", "options_label");
			td.addClass("usb_device_td");
			td.addClass("options_usb_text");
			td.append(checkbox);
			td.append(dev["name"]);
			this.usb_devices.push(checkbox);
		}
	}
	
	this.hide_config
}

function RunningVm(vm_info) {
	this.name = vm_info.name;
	this.uuid = vm_info.uuid;
	this.memory = vm_info.memory;
	this.vram = vm_info.vram;
	this.cpus = vm_info.cpus;
	this.connect = vm_info.connect;
	
	var _self = this;
	
	this.handle_kill = function() {
		$.get("/api/kill_vm/" + _self.uuid, "", function() {
			update_running_vms();
		});
	};
	
	this.create_info_span = function(name, info) {
		var res = $("<span>");
		
		var span = $("<span>");
		span.addClass("running_vm_info_name");
		span.text(name)
		res.append(span);
		
		var info_span = $("<span>");
		info_span.text(info);
		res.append(info_span);
		
		return res;
	}
	
	this.create_html = function() {
		this.dom = $("<div>");
		this.dom.addClass("running_vm");
		
		this.dom_kill_button = $("<button>");
		this.dom_kill_button.text("KILL");
		this.dom_kill_button.addClass("running_vm_kill_button");
		this.dom_kill_button.click(this.handle_kill);
		this.dom.append(this.dom_kill_button);
		
		this.dom_name = $("<span>");
		this.dom_name.addClass("running_vm_name");
		this.dom_name.text(this.name);
		this.dom.append(this.dom_name);
		
		this.dom.append($("<br>"));	
		
		this.dom_uuid = $("<span>");
		this.dom_uuid.addClass("running_vm_uuid");
		this.dom_uuid.text(this.uuid);
		this.dom.append(this.dom_uuid);
		
		this.dom.append($("<br>"));	
		
		var info_div = $("<div>");
		info_div.addClass("running_vm_info_div");
		this.dom.append(info_div);
		
		info_div.append(this.create_info_span("connect:", this.connect));
		info_div.append(this.create_info_span("memory:", this.memory));
		info_div.append(this.create_info_span("vram:", this.vram));
		info_div.append(this.create_info_span("cpus:", this.cpus));
		
		return this.dom;
	};
}

var USB_DEVICES = {}
var VMS = []
var RUNNING_VMS = {}

function receive_usb_devices(usbs) {
	USB_DEVICES = {};
	for(x in usbs) {
		dev = usbs[x];
		USB_DEVICES[dev["name"]] = dev;
	}
	$.get("/api/vms", "", function(vms) {
		for(var i = 0; i < vms.length; i++) {
			vm_info = vms[i];
			var vm = new Vm(vm_info);
			var vm_dom = vm.create_html();
			$("#vm_list").append(vm_dom);
			
			if(i % 2 == 0) {
				vm_dom.addClass("even_vm");
			} else {
				vm_dom.addClass("odd_vm");
			}
			
			if(i != vms.length - 1) {
				$("#vm_list").append("<hr>");
			}
		}
	});
}

function update_running_vms() {
	$.get("/api/running_vms", "", handle_update_running_vms);
}

function handle_update_running_vms(vms) {
	var new_running_vms = {};
	for(x in vms) {
		var vm = vms[x];
		var new_vm = new RunningVm(vm);
		if(RUNNING_VMS[new_vm.uuid] != undefined) {
			new_vm = RUNNING_VMS[new_vm.uuid];
		} else {
			var html = new_vm.create_html();
			$("#running_vms").prepend(html);
		}
		new_running_vms[new_vm.uuid] = new_vm;
	}
	
	for(x in RUNNING_VMS) {
		var vm = RUNNING_VMS[x];
		if(new_running_vms[vm.uuid] == undefined) {
			vm.dom.remove();
		}
	}
	RUNNING_VMS = new_running_vms;
}

$(document).ready(function(){
	$.get("/api/usb_devices", "", receive_usb_devices);
	update_running_vms();
	
	setInterval(update_running_vms, 1000*30);
});
