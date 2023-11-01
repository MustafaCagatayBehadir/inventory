"""Inventory Action Module."""
import re
from typing import List
from collections import namedtuple
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

OPTICAL_MODULE_BRIEF = """
--------------------------------------------------------------------------------
Port                   Status Duplex Type               Wavelength            RxPower     TxPower     Mode             VendorPN
--------------------------------------------------------------------------------
ETH2/0/0               down   full   1G-10km-esfp       1310nm                -40.00dBm   -6.07dBm    SingleMode       LTD1302-BC+1
ETH2/0/4               down   full   1G-10km-esfp       1310nm                -40.00dBm   -5.67dBm    SingleMode       MXPD-243S-01
ETH2/1/1               down   full   1G-10km-esfp       1310nm                -40.00dBm   -6.07dBm    SingleMode       LTD1302-BC+1
ETH2/1/6               down   full   1G-10km-esfp       1310nm                -40.00dBm   -5.95dBm    SingleMode       LTD1302-BC+1
ETH3/1/0               up     full   1G-10km-esfp       1310nm                -11.16dBm   -6.19dBm    SingleMode       LTD1302-BC+1
ETH3/1/1               up     full   1G-10km-esfp       1310nm                -7.74dBm    -6.01dBm    SingleMode       LTD1302-BC+1
ETH3/1/2               up     full   10G-10km-sfp+      1310nm                -6.84dBm    -1.59dBm    SingleMode       FTLX1471D3BCL-HU
ETH3/1/3               up     full   1G-10km-esfp       1310nm                -6.38dBm    -6.04dBm    SingleMode       LTD1302-BC+1
ETH3/1/4               up     full   10G-10km-sfp+      1310nm                -17.72dBm   -1.37dBm    SingleMode       FTLX1471D3BCL-HU
ETH3/1/5               down   full   1G-10km-esfp       1310nm                -40.00dBm   -6.00dBm    SingleMode       LTD1302-BC+1
ETH3/1/6               up     full   1G-10km-esfp       1310nm                -8.50dBm    -5.90dBm    SingleMode       LTD1302-BC+1
ETH3/1/7               down   full   1G-10km-esfp       1310nm                -40.00dBm   -6.22dBm    SingleMode       LTD1302-BC+1
ETH3/1/10              up     full   1G-10km-esfp       1310nm                -17.64dBm   -5.85dBm    SingleMode       LTD1302-BC+1
ETH3/1/11              up     full   1G-10km-esfp       1310nm                -6.47dBm    -5.94dBm    SingleMode       LTD1302-BC+1
ETH3/1/12              up     full   1G-100m-copper     unknown               --          --          CopperMode       OM9150
ETH3/1/14              down   full   1G-100m-copper     unknown               --          --          CopperMode       OM9150
ETH3/1/15              down   full   1G-10km-esfp       1310nm                -40.00dBm   -6.18dBm    SingleMode       LTD1302-BC+1
ETH3/1/20              down   full   1G-100m-copper     unknown               --          --          CopperMode       OM9150
--------------------------------------------------------------------------------
"""


def get_kp_service_id(keypath: ncs.maagic.keypath._KeyPath) -> str:
    """Get service name from keypath."""
    kpath = str(keypath)
    service = kpath[kpath.rfind('{') + 1:len(kpath) - 1]
    return service


def get_device_platform_name(root: ncs.maagic.Root, device_hostname: str, log: ncs.log.Log) -> str:
    """Get device platform name."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    platform = root.ncs__devices.device[device_hostname].platform.name
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " platform is " + platform)
    return platform


def populate_platform_grouping(inventory_name: str, device_hostname: str, log: ncs.log.Log) -> None:
    """Populate device information under inventory device."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    with ncs.maapi.single_write_trans(USER, "system") as trans:
        platform = ncs.maagic.get_node(trans, f"/ncs:devices/device{{{device_hostname}}}/platform")
        inventory_manager = ncs.maagic.get_node(trans, f"/inv:inventory-manager{{{inventory_name}}}")
        device_platform = inventory_manager.device[device_hostname].platform
        device_platform.name = platform.name
        device_platform.version = platform.version
        device_platform.model = platform.model
        device_platform.serial_number = platform.serial_number
        log.info("Device ##" + INDENTATION * 2 + device_hostname + " platform details are set.")
        trans.apply()


def iosxr_get_device_live_status_inventory(root: ncs.maagic.Root, device_hostname: str,
                                           log: ncs.log.Log) -> ncs.maagic.List:
    """Get device inventory data from ned live-status."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    inventory_data = root.ncs__devices.device[device_hostname].live_status.cisco_ios_xr_stats__inventory
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " inventory data is gathered.")
    return inventory_data


def iosxr_get_device_live_status_controllers(root: ncs.maagic.Root, device_hostname: str,
                                             log: ncs.log.Log) -> ncs.maagic.List:
    """Get device controllers data from ned live-status."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    controllers_data = root.ncs__devices.device[device_hostname].live_status.cisco_ios_xr_stats__controllers
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " controllers data is gathered.")
    return controllers_data


def iosxr_populate_inventory_grouping(inventory_data: ncs.maagic.List, inventory_name: str, device_hostname: str,
                                      log: ncs.log.Log) -> None:
    """Populate inventory list under inventory device."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    with ncs.maapi.single_write_trans(USER, "system") as trans:
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
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    with ncs.maapi.single_write_trans(USER, "system") as trans:
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


def huawei_vrp_parse_inventory_data(data: str, device_hostname: str, log: ncs.log.Log) -> List[namedtuple]:
    """Parse 'display elabel brief' cli command output."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    inventory = []
    Inventory = namedtuple('Inventory', ['name', 'descr', 'pid', 'sn'])
    parent_pattern = r'(\w+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(.*)'
    power_pattern = r'(\w+)\s+(\d+)'
    child_pattern = r'\s+(\w+)\s*(\d+)\s+(\S+)\s+(\S+)\s+(.*)'

    for line in data.splitlines():
        parent_match = re.match(parent_pattern, line)
        power_match = re.match(power_pattern, line)
        child_match = re.match(child_pattern, line)

        if parent_match:
            parent_slot, parent_slot_num, pid, serial_number, description = parent_match.groups()
        elif power_match:
            parent_slot, parent_slot_num = power_match.groups()
            pid = serial_number = description = ''
        elif child_match:
            if len(child_match.groups()) == 5:
                child_slot, child_slot_num, pid, serial_number, description = child_match.groups()
            elif len(child_match.groups()) == 4:
                description = ''

        if parent_match or power_match:
            inventory.append(Inventory(f"{parent_slot}{parent_slot_num}", description, pid, serial_number))
        elif child_match:
            child_slot_num = f'{parent_slot_num}/{child_slot_num}'
            inventory.append(Inventory(f"{child_slot}{child_slot_num}", description, pid, serial_number))

    log.info("Device ##" + INDENTATION * 2 + device_hostname + " inventory data is parsed.")
    return inventory


def huawei_vrp_parse_transceiver_data(data: str, device_hostname: str, log: ncs.log.Log) -> List[namedtuple]:
    """Parse 'display optical-module brief' cli command output."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    fields = ['port', 'status', 'type', 'pid']
    Transceiver = namedtuple('Transceiver', fields)
    transceiver_list = []

    lines = data.strip().split('\n')
    # Iterate through the lines starts with Eth
    for line in lines[4:-2]:
        values = line.split()
        transceiver = Transceiver(values[0], values[1], values[3], values[-1])
        transceiver_list.append(transceiver)

    log.info("Device ##" + INDENTATION * 2 + device_hostname + " transceiver data is parsed.")
    return transceiver_list


def huawei_vrp_get_device_live_status_exec_inventory(root: ncs.maagic.Root, device_hostname: str,
                                                     log: ncs.log.Log) -> ncs.maagic.List:
    """Get device inventory data from live-status exec."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    live_status = root.ncs__devices.device[device_hostname].live_status.vrp_stats__exec.display
    action_input = live_status.get_input()
    action_input.args = ["elabel brief"]
    inventory_data = live_status(action_input).result
    parsed_inventory_data = huawei_vrp_parse_inventory_data(inventory_data, device_hostname, log)
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " inventory data is gathered.")
    return parsed_inventory_data


def huawei_vrp_get_device_live_status_exec_transceiver(root: ncs.maagic.Root, device_hostname: str,
                                                       log: ncs.log.Log) -> ncs.maagic.List:
    """Get device transceiver data from live-status exec."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    live_status = root.ncs__devices.device[device_hostname].live_status.vrp_stats__exec.display
    action_input = live_status.get_input()
    action_input.args = ["optical-module brief"]
    transceiver_data = live_status(action_input).result
    parsed_transceiver_data = huawei_vrp_parse_transceiver_data(transceiver_data, device_hostname, log)
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " transceiver data is gathered.")
    return parsed_transceiver_data


def huawei_vrp_populate_inventory_grouping(inventory_data: List[namedtuple], inventory_name: str, device_hostname: str,
                                           log: ncs.log.Log) -> None:
    """Populate inventory list under inventory device."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    with ncs.maapi.single_write_trans(USER, "system") as trans:
        inventory_manager = ncs.maagic.get_node(trans, f"/inv:inventory-manager{{{inventory_name}}}")
        device = inventory_manager.device[device_hostname]
        for data in inventory_data:
            module = device.inventory.create(data.name)
            module.description = data.descr
            module.pid = data.pid
            module.serial_number = data.sn
            log.info("Module ##" + INDENTATION * 4 + data.name + " is created.")
        trans.apply()


def huawei_vrp_populate_controllers_grouping(transceiver_data: List[namedtuple], inventory_name: str,
                                             device_hostname: str, log: ncs.log.Log) -> None:
    """Populate controllers list under inventory device."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    with ncs.maapi.single_write_trans(USER, "system") as trans:
        inventory_manager = ncs.maagic.get_node(trans, f"/inv:inventory-manager{{{inventory_name}}}")
        device = inventory_manager.device[device_hostname]
        for data in transceiver_data:
            controller = device.controller.create(data.port)
            controller.controller_state = data.status
            controller.optics_type = data.type
            controller.pid = data.pid
            log.info("Controller ##" + INDENTATION * 4 + data.port + " is created.")
        trans.apply()


def alu_sr_get_device_live_status_card(root: ncs.maagic.Root, device_hostname: str,
                                       log: ncs.log.Log) -> ncs.maagic.List:
    """Get device card data from ned live-status."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    card_data = root.ncs__devices.device[device_hostname].live_status.alu_stats__card
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " card data is gathered.")
    return card_data


def alu_sr_get_device_live_status_slot(root: ncs.maagic.Root, device_hostname: str,
                                       log: ncs.log.Log) -> ncs.maagic.List:
    """Get device slot data from ned live-status."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    slot_data = root.ncs__devices.device[device_hostname].live_status.alu_stats__slot
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " card data is gathered.")
    return slot_data


def alu_sr_get_device_live_status_ports(root: ncs.maagic.Root, device_hostname: str,
                                        log: ncs.log.Log) -> ncs.maagic.List:
    """Get device pots data from ned live-status."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    ports_data = root.ncs__devices.device[device_hostname].live_status.alu_stats__ports
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " ports data is gathered.")
    return ports_data


def alu_sr_populate_inventory_grouping(card_data: ncs.maagic.List, slot_data: ncs.maagic.List, inventory_name: str,
                                       device_hostname: str, log: ncs.log.Log) -> None:
    """Populate inventory list under inventory device."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    with ncs.maapi.single_write_trans(USER, "system") as trans:
        inventory_manager = ncs.maagic.get_node(trans, f"/inv:inventory-manager{{{inventory_name}}}")
        device = inventory_manager.device[device_hostname]
        for data in card_data:
            module = device.inventory.create(data.card_id)
            module.description = data.provisioned_type
            module.pid = data.part_number
            module.serial_number = data.serial_number
            log.info("Module ##" + INDENTATION * 4 + data.card_id + " is created.")
        for data in slot_data:
            for mda_data in data.mda:
                mda_id = str(data.slot_id) + "/" + str(mda_data.mda_id)
                module = device.inventory.create(mda_id)
                module.description = mda_data.provisioned_type
                module.pid = mda_data.part_number
                module.serial_number = mda_data.serial_number
                log.info("Module ##" + INDENTATION * 4 + mda_id + " is created.")
        trans.apply()


def alu_sr_populate_controllers_grouping(ports_data: ncs.maagic.List, inventory_name: str, device_hostname: str,
                                         log: ncs.log.Log) -> None:
    """Populate controllers list under inventory device."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    with ncs.maapi.single_write_trans(USER, "system") as trans:
        inventory_manager = ncs.maagic.get_node(trans, f"/inv:inventory-manager{{{inventory_name}}}")
        device = inventory_manager.device[device_hostname]
        for data in ports_data:
            controller = device.controller.create(data.port_id)
            controller.controller_state = data.port_state
            transceiver = data.transceiver_data
            controller.optics_type = transceiver.transceiver_type
            controller.part_number = transceiver.part_number
            controller.serial_number = transceiver.serial_number
            controller.pid = transceiver.model_number
            log.info("Controller ##" + INDENTATION * 4 + data.port_id + " is created.")
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
                transceiver_data = huawei_vrp_get_device_live_status_exec_transceiver(root, hostname, self.log)
                huawei_vrp_populate_inventory_grouping(inventory_data, inventory_name, hostname, self.log)
                huawei_vrp_populate_controllers_grouping(transceiver_data, inventory_name, hostname, self.log)

            else:
                self.log.info("Device ##" + INDENTATION * 2 + hostname + " platform is alu-sr.")
                card_data = alu_sr_get_device_live_status_card(root, hostname, self.log)
                slot_data = alu_sr_get_device_live_status_slot(root, hostname, self.log)
                ports_data = alu_sr_get_device_live_status_ports(root, hostname, self.log)
                alu_sr_populate_inventory_grouping(card_data, slot_data, inventory_name, hostname, self.log)
                alu_sr_populate_controllers_grouping(ports_data, inventory_name, hostname, self.log)

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
