"""Inventory Action Module."""
import inspect
import ncs
import _ncs

INDENTATION = " "
USER = "admin"
ELABEL_BRIEF = """
Elabel brief information:
-------------------------------------------------------------------------------------------------------------------------------------------------
Slot #          BoardType                                BarCode                 Description
-------------------------------------------------------------------------------------------------------------------------------------------------
LPU 1           CR57EMGFB23                              210305505310HA000037    LPUI-51-E-48xFE/GE-SFP-A
  PIC 0         CR57EFGFB2                               030PMH10HA000226        24x100/1000Base-X-SFP
  PIC 1         CR57EFGFB2                               030PMH10HA000103        24x100/1000Base-X-SFP
LPU 6           CR57LBXF20                               210305468110E6000203    LPUI-120-12x10GBase LAN/WAN-SFP+ -A
  PIC 0         CR57LBXF2                                030QKK10E5000519        P120-12x10GBase LAN/WAN-SFP+ -A
LPU 7           CR57LBXF20                               210305468110JA000271    LPUI-120-12x10GBase LAN/WAN-SFP+ -A
  PIC 0         CR57LBXF2                                030QKKW0J9000915        P120-12x10GBase LAN/WAN-SFP+ -A
LPU 8           CR57LBXF20                               210305468110JA000259    LPUI-120-12x10GBase LAN/WAN-SFP+ -A
  PIC 0         CR57LBXF2                                030QKKW0J9000241        P120-12x10GBase LAN/WAN-SFP+ -A
MPU 9           CR57SRUA1TA91                            210305726110JA000041    SRUA-1T-A
MPU 10          CR57SRUA1TA91                            210305726110JA000030    SRUA-1T-A
SFU 11          CR57SFU1TC00                             210305609410JA000109    SFUI-1T-C
SFU 12          CR57SFU1TC00                             210305609410JA000106    SFUI-1T-C
PWR 17
 PM1            PDC-2200WB                               2102311CNPLUJ9003290
 PM2            PDC-2200WB                               2102311CNPLUJ9003448
 PM3            PDC-2200WB                               2102311CNPLUJ9003458
 PM4            PDC-2200WB                               2102311CNPLUJ9003381
 PM5            PDC-2200WB                               2102311CNPLUJ9003405
 PM6            PDC-2200WB                               2102311CNPLUJ9003309
FAN 19          CR56FCBJ                                 2102120866P0J8002257
FAN 20          CR56FCBJ                                 2102120866P0J8002255
FAN 21          CR56FCBJ                                 2102120866P0J9000129
PMU 22          CR56PMUA                                 2102310QUCP0J8000739
PMU 23          CR56PMUA                                 2102310QUCP0J8000713
-------------------------------------------------------------------------------------------------------------------------------------------------
"""


def get_kp_service_id(keypath: ncs.maagic.keypath._KeyPath) -> str:
    """Get service name from keypath."""
    kpath = str(keypath)
    service = kpath[kpath.rfind('{') + 1:len(kpath) - 1]
    return service


def get_device_platform_name(root: ncs.maagic.Root, hostname: str, log: ncs.log.Log) -> str:
    """Get device platform name."""
    log.debug("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    platform = root.ncs__devices.device[hostname].platform.name
    log.info("Device ##" + INDENTATION * 2 + hostname + " platform is " + platform)
    return platform


def populate_platform_grouping(inventory_name: str, device_hostname: str, log: ncs.log.Log) -> None:
    """Populate device information under inventory device."""
    log.debug("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    with ncs.maapi.single_write_trans(USER, 'system') as trans:
        platform = ncs.maagic.get_node(trans, f"/ncs:devices/device{{{device_hostname}}}/platform")
        inventory_manager = ncs.maagic.get_node(trans, f"/inv:inventory-manager{{{inventory_name}}}")
        device_platform = inventory_manager.device[device_hostname].platform
        device_platform.name = platform.name
        device_platform.version = platform.version
        device_platform.model = platform.model
        device_platform.serial_number = platform.serial_number
        log.info("Device ##" + INDENTATION * 2 + device_hostname + " platform details are setted.")
        trans.apply()


def iosxr_get_device_live_status_inventory(root: ncs.maagic.Root, hostname: str, log: ncs.log.Log) -> ncs.maagic.List:
    """Get device inventory data from ned live-status."""
    log.debug("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    inventory_data = root.ncs__devices.device[hostname].live_status.cisco_ios_xr_stats__inventory
    log.info("Device ##" + INDENTATION * 2 + hostname + " inventory data is gathered.")
    return inventory_data


def iosxr_get_device_live_status_controllers(root: ncs.maagic.Root, hostname: str, log: ncs.log.Log) -> ncs.maagic.List:
    """Get device controllers data from ned live-status."""
    log.debug("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    controllers_data = root.ncs__devices.device[hostname].live_status.cisco_ios_xr_stats__controllers
    log.info("Device ##" + INDENTATION * 2 + hostname + " controllers data is gathered.")
    return controllers_data


def iosxr_populate_inventory_grouping(inventory_data: ncs.maagic.List, inventory_name: str, device_hostname: str,
                                log: ncs.log.Log) -> None:
    """Populate inventory list under inventory device."""
    log.debug("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    with ncs.maapi.single_write_trans(USER, 'system') as trans:
        inventory_manager = ncs.maagic.get_node(trans, f"/inv:inventory-manager{{{inventory_name}}}")
        device = inventory_manager.device[device_hostname]
        for data in inventory_data:
            module = device.inventory.create(data.name)
            module.description = data.descr
            module.pid = data.pid
            module.serial_number = data.sn
            log.info("Module ##" + INDENTATION * 4 + data.name + " is created.")
        trans.apply()


def iosxr_populate_controllers_grouping(controllers_data: ncs.maagic.List, inventory_name: str, device_hostname: str, 
                                        log: ncs.log.Log) -> None:
    """Populate controllers list under inventory device."""
    log.debug("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    with ncs.maapi.single_write_trans(USER, 'system') as trans:
        inventory_manager = ncs.maagic.get_node(trans, f"/inv:inventory-manager{{{inventory_name}}}")
        device = inventory_manager.device[device_hostname]
        for data in controllers_data.Optics:
            instance = data.instance
            transceiver = instance.transceiver_vendor_details
            controller = device.controller.create(data.id)
            controller.controller_state = instance.controller_state
            controller.optics_type = transceiver.optics_type
            controller.name = transceiver.name
            controller.part_number = transceiver.part_number
            controller.serial_number = transceiver.serial_number
            controller.pid = transceiver.pid
            log.info("Controller ##" + INDENTATION * 4 + data.id + " is created.")
        trans.apply()


def huawei_vrp_parse_inventory_data(data: str, log: ncs.log.Log):
    import re
    # Define a regular expression pattern to match lines with Slot, BoardType, BarCode, and Description
    pattern = r'(\w+)\s(\d+)\s+(\S+)\s+(\S+)\s+(.*)'
    # Find all matches in the data
    matches = re.findall(pattern, data)
    # Define a dictionary to store the hierarchy
    hierarchy = {}
    # Initialize variables to keep track of the current parent
    current_parent = None
    # Iterate through the matches
    for match in matches:
        slot, slot_number, board_type, barcode, description = match
        # Check if the current slot is a parent (e.g., LPU, PWR)
        if slot in ['LPU', 'MPU', 'SFU', 'PWR', 'FAN', 'PMU']:
            current_parent, current_parent_number = slot, slot_number
            hierarchy[current_parent] = {current_parent_number: {}}
        else:
            if current_parent is not None:
                # Add the current match as a child to the current parent
                hierarchy[current_parent][current_parent_number][slot][slot_number] = {
                    "BoardType": board_type,
                    "BarCode": barcode,
                    "Description": description
                }
    import json
    log.info(json.dumps(hierarchy, indent=2))


def huawei_vrp_get_device_live_status_exec_inventory(root: ncs.maagic.Root, hostname: str, log: ncs.log.Log) -> ncs.maagic.List:
    """Get device inventory data from live-status exec."""
    log.debug("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    # live_status = root.ncs__devices.device[hostname].live_status.vrp_stats__exec.display
    # action_input = live_status.get_input()
    # action_input.args = ["elabel brief"]
    # inventory_data = live_status(action_input).result
    inventory_data = huawei_vrp_parse_inventory_data(ELABEL_BRIEF, log)
    log.info("Device ##" + INDENTATION * 2 + hostname + " inventory data is gathered.")
    return inventory_data


def huawei_vrp_get_device_live_status_interface(root: ncs.maagic.Root, hostname: str, log: ncs.log.Log) -> ncs.maagic.List:
    """Get device interface data from ned live-status."""
    log.debug("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    interface_data = root.ncs__devices.device[hostname].live_status.vrp_stats__interface
    log.info("Device ##" + INDENTATION * 2 + hostname + " interface data is gathered.")
    return interface_data


def huawei_vrp_get_device_live_status_transceiver(root: ncs.maagic.Root, hostname: str, log: ncs.log.Log) -> ncs.maagic.List:
    """Get device transceiver data from ned live-status."""
    log.debug("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    transceiver_data = root.ncs__devices.device[hostname].live_status.vrp_stats__transceiver
    log.info("Device ##" + INDENTATION * 2 + hostname + " transceiver data is gathered.")
    return transceiver_data


def huawei_vrp_populate_controllers_grouping(interface_data: ncs.maagic.List, transceiver_data: ncs.maagic.List, 
                                             inventory_name: str, device_hostname: str, log: ncs.log.Log) -> None:
    """Populate controllers list under inventory device."""
    log.debug("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    with ncs.maapi.single_write_trans(USER, 'system') as trans:
        inventory_manager = ncs.maagic.get_node(trans, f"/inv:inventory-manager{{{inventory_name}}}")
        device = inventory_manager.device[device_hostname]
        for data in interface_data:
            controller = device.controller.create(data.name)
            controller.controller_state = data.admin_state ## TODO Think for sustainability
        for data in transceiver_data:
            controller = device.controller[data.interface]
            controller.optics_type = data.transceiver_type
            controller.name = data.vendor_name
            controller.part_number = data.vendor_part_number
            controller.serial_number = data.manufacture_serial_number
            log.info("Controller ##" + INDENTATION * 4 + data.interface + " is created.")
        trans.apply()

# ------------------------
# Service CALLBACK
# ------------------------
class InventoryCallbacks(ncs.application.Service):
    """Service class."""

    @ncs.application.Service.create
    def cb_create(self, tctx, root, service, proplist):
        """Create method for service."""
        self.log.info("Provisioning inventory group ", service.name)


# ------------------------
# Action CALLBACK
# ------------------------
class InventoryUpdate(ncs.dp.Action):
    """Inventory update action class."""

    @ncs.dp.Action.action
    def cb_action(self, uinfo, name, kp, input, output, trans):
        """Update inventory."""
        self.log.info("Action triggered ##" + INDENTATION + name)
        _ncs.dp.action_set_timeout(uinfo, 1800)
        root = ncs.maagic.get_root(trans)
        inventory_name = get_kp_service_id(kp)
        inventory_manager = root.inv__inventory_manager[inventory_name]
        self.log.info("Inventory Manager ##" + INDENTATION + inventory_manager.name)
        target = input.target_devices

        if target == "all":
            self.log.info("Action ##" + INDENTATION + name + " target all")
            devices = inventory_manager.device
        elif target == "specify":
            self.log.info("Action ##" + INDENTATION + name + " target specify")
            devices = input.device.as_list()

        self.log.info("Sync ##" + INDENTATION + "Processing device:")
        for device in devices:
            hostname = device.name if isinstance(device, ncs.maagic.ListElement) else device
            self.log.info("Sync ##" + INDENTATION * 2 + hostname)
            platform = get_device_platform_name(root, hostname, self.log)
            populate_platform_grouping(inventory_name, hostname, self.log)
            
            if platform == "ios-xr":
                self.log.info("Device ##" + INDENTATION * 2 + hostname + " platform is ios-xr.")
                inventory_data = iosxr_get_device_live_status_inventory(root, hostname, self.log)
                controllers_data = iosxr_get_device_live_status_controllers(root, hostname, self.log)
                iosxr_populate_inventory_grouping(inventory_data, inventory_name, hostname, self.log)
                iosxr_populate_controllers_grouping(controllers_data, inventory_name, hostname, self.log)
            
            elif platform == "huawei-vrp":
                self.log.info("Device ##" + INDENTATION * 2 + hostname + " platform is huawei-vrp.")
                inventory_data = huawei_vrp_get_device_live_status_exec_inventory(root, hostname, self.log)
                interface_data = huawei_vrp_get_device_live_status_interface(root, hostname, self.log)
                transceiver_data = huawei_vrp_get_device_live_status_transceiver(root, hostname, self.log)
                huawei_vrp_populate_controllers_grouping(interface_data, transceiver_data, inventory_name, hostname, self.log)

        output.result = f"Devices processed: {len(devices)}"


# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Main(ncs.application.Application):
    """Inventory action class."""

    def setup(self):
        """Register service and actions."""
        self.log.info('Main RUNNING')

        # inventory service registration
        self.register_service('inventory-manager-servicepoint', InventoryCallbacks)

        # inventory update-inventory-manager action
        self.register_action('update-inventory-manager', InventoryUpdate)

        self.log.info('Main Application Started')

    def teardown(self):
        """Teardown."""
        self.log.info('Main FINISHED')
