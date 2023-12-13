"""Inventory Action Module."""
import inspect
import re
from typing import List, NamedTuple, Tuple

import _ncs
import ncs

INDENTATION = " "
USER = "admin"


class VrpInventory(NamedTuple):
    """Inventory class for Huawei VRP platform."""

    name: str
    descr: str
    pid: str
    sn: str


class VrpTransceiver(NamedTuple):
    """Transceiver class for Huawei VRP platform."""

    port: str
    status: str
    type: str
    pid: str


class PoolInfo(NamedTuple):
    """Resource-Manager id pool class."""

    name: str
    start: int
    end: int


GLOBAL_POOLS = [
    PoolInfo(name="PW_ID_POOL", start=10000, end=20000),
    PoolInfo(name="SERVICE_ID_POOL", start=10000, end=20000),
]
DEVICE_POOLS = [PoolInfo(name="SDP_ID_POOL", start=10000, end=20000)]
INTERFACE_POOLS = [
    PoolInfo(name="CVLAN_ID_POOL", start=2, end=4000),
    PoolInfo(name="SVLAN_ID_POOL", start=2, end=4000),
    PoolInfo(name="SUB_INTF_ID_POOL", start=2, end=4000),
]


def get_kp_service_id(keypath: ncs.maagic.keypath._KeyPath) -> str:
    """Get service name from keypath."""
    kpath = str(keypath)
    service = kpath[kpath.rfind("{") + 1 : len(kpath) - 1]
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


def create_inventory_resource_pools(inventory_name: str, log: ncs.log.Log) -> None:
    """Create id-pools for inventory."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    with ncs.maapi.single_write_trans(USER, "system") as trans:
        root = ncs.maagic.get_root(trans)
        inventory_manager = ncs.maagic.get_node(trans, f"/inv:inventory-manager{{{inventory_name}}}")
        id_pool = root.ralloc__resource_pools.idalloc__id_pool
        for global_pool in GLOBAL_POOLS:
            pool_name = global_pool.name
            if pool_name not in id_pool:
                pool = id_pool.create(pool_name)
                pool.range.start, pool.range.end = global_pool.start, global_pool.end
                log.info("Inventory Pool ##" + INDENTATION * 2 + pool_name + " is created.")
            else:
                log.info("Inventory Pool ##" + INDENTATION * 2 + pool_name + " is already created, skipping.")

        for device in inventory_manager.device:
            device_name = device.name
            for device_pool in DEVICE_POOLS:
                pool_name = device_name + "_" + device_pool.name
                if pool_name not in id_pool:
                    pool = id_pool.create(pool_name)
                    pool.range.start, pool.range.end = device_pool.start, device_pool.end
                    log.info("Device Pool ##" + INDENTATION * 4 + pool_name + " is created.")
                else:
                    log.info("Device Pool ##" + INDENTATION * 4 + pool_name + " is already created, skipping.")

            for interface in device.interface:
                if_size = interface.if_size
                if_number = str(interface.if_number).replace("/", "_")
                for interface_pool in INTERFACE_POOLS:
                    pool_name = device_name + "_" + if_size + "_" + if_number + "_" + interface_pool.name
                    if pool_name not in id_pool:
                        pool = id_pool.create(pool_name)
                        pool.range.start, pool.range.end = interface_pool.start, interface_pool.end
                        log.info("Interface Pool ##" + INDENTATION * 6 + pool_name + " is created.")
                    else:
                        log.info("Interface Pool ##" + INDENTATION * 6 + pool_name + " is already created, skipping.")
        trans.apply()

def iosxr_get_device_live_status_inventory(
    root: ncs.maagic.Root, device_hostname: str, log: ncs.log.Log
) -> ncs.maagic.List:
    """Get device inventory data from ned live-status."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    inventory_data = root.ncs__devices.device[device_hostname].live_status.cisco_ios_xr_stats__inventory
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " inventory data is gathered.")
    return inventory_data


def iosxr_get_device_live_status_controllers(
    root: ncs.maagic.Root, device_hostname: str, log: ncs.log.Log
) -> ncs.maagic.List:
    """Get device controllers data from ned live-status."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    controllers_data = root.ncs__devices.device[device_hostname].live_status.cisco_ios_xr_stats__controllers
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " controllers data is gathered.")
    return controllers_data


def iosxr_get_device_cdb_interfaces(
    root: ncs.maagic.Root, device_hostname: str, log: ncs.log.Log
) -> ncs.maagic.Container:
    """Get device interfaces data from cdb."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    interfaces_data = root.ncs__devices.device[device_hostname].config.cisco_ios_xr__interface
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " interfaces data is gathered.")
    return interfaces_data


def iosxr_populate_inventory_grouping(
    inventory_data: ncs.maagic.List, inventory_name: str, device_hostname: str, log: ncs.log.Log
) -> None:
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


def iosxr_populate_controllers_grouping(
    controllers_data: ncs.maagic.List, inventory_name: str, device_hostname: str, log: ncs.log.Log
) -> None:
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


def iosxr_populate_interfaces_grouping(
    interface_data: ncs.maagic.Container, inventory_name: str, device_hostname: str, log: ncs.log.Log
) -> None:
    """Populate interface list under inventory device."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    if_sizes: List = [
        "Bundle_Ether",
        "FiftyGigE",
        "FortyGigE",
        "FourHundredGigE",
        "GigabitEthernet",
        "HundredGigE",
        "TenGigE",
        "TwentyFiveGigE",
        "TwoHundredGigE",
    ]
    with ncs.maapi.single_write_trans(USER, "system") as trans:
        inventory_manager = ncs.maagic.get_node(trans, f"/inv:inventory-manager{{{inventory_name}}}")
        device = inventory_manager.device[device_hostname]
        del device.interface  # Delete device interface list first to re-create from scratch
        log.info("Device ##" + INDENTATION * 2 + " interface list is deleted.")
        for if_size in if_sizes:
            for size in getattr(interface_data, if_size):
                if_number = str(size.id)
                device.interface.create(size, if_number)
                log.info("Interface ##" + INDENTATION * 4 + if_size + " " + if_number + " is created.")
        trans.apply()


def huawei_vrp_parse_inventory_data(data: str, device_hostname: str, log: ncs.log.Log) -> List[VrpInventory]:
    """Parse 'display elabel brief' cli command output."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    inventory = []
    parent_pattern = r"(\w+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(.*)"
    power_pattern = r"(\w+)\s+(\d+)"
    child_pattern = r"\s+(\w+)\s*(\d+)\s+(\S+)\s+(\S+)\s+(.*)"

    for line in data.splitlines():
        parent_match = re.match(parent_pattern, line)
        power_match = re.match(power_pattern, line)
        child_match = re.match(child_pattern, line)

        if parent_match:
            parent_slot, parent_slot_num, pid, serial_number, description = parent_match.groups()
        elif power_match:
            parent_slot, parent_slot_num = power_match.groups()
            pid = serial_number = description = ""
        elif child_match:
            if len(child_match.groups()) == 5:
                child_slot, child_slot_num, pid, serial_number, description = child_match.groups()
            elif len(child_match.groups()) == 4:
                description = ""

        if parent_match or power_match:
            inventory.append(VrpInventory(f"{parent_slot}{parent_slot_num}", description, pid, serial_number))
        elif child_match:
            child_slot_num = f"{parent_slot_num}/{child_slot_num}"
            inventory.append(VrpInventory(f"{child_slot}{child_slot_num}", description, pid, serial_number))

    log.info("Device ##" + INDENTATION * 2 + device_hostname + " inventory data is parsed.")
    return inventory


def huawei_vrp_parse_transceiver_data(data: str, device_hostname: str, log: ncs.log.Log) -> List[VrpTransceiver]:
    """Parse 'display optical-module brief' cli command output."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    transceiver_list = []

    lines = data.strip().split("\n")
    # Iterate through the lines starts with Eth
    for line in lines[4:-2]:
        values = line.split()
        transceiver = VrpTransceiver(values[0], values[1], values[3], values[-1])
        transceiver_list.append(transceiver)

    log.info("Device ##" + INDENTATION * 2 + device_hostname + " transceiver data is parsed.")
    return transceiver_list


def huawei_vrp_get_device_live_status_exec_inventory(
    root: ncs.maagic.Root, device_hostname: str, log: ncs.log.Log
) -> ncs.maagic.List:
    """Get device inventory data from live-status exec."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    live_status = root.ncs__devices.device[device_hostname].live_status.vrp_stats__exec.display
    action_input = live_status.get_input()
    action_input.args = ["elabel brief"]
    inventory_data = live_status(action_input).result
    parsed_inventory_data = huawei_vrp_parse_inventory_data(inventory_data, device_hostname, log)
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " inventory data is gathered.")
    return parsed_inventory_data


def huawei_vrp_get_device_live_status_exec_transceiver(
    root: ncs.maagic.Root, device_hostname: str, log: ncs.log.Log
) -> ncs.maagic.List:
    """Get device transceiver data from live-status exec."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    live_status = root.ncs__devices.device[device_hostname].live_status.vrp_stats__exec.display
    action_input = live_status.get_input()
    action_input.args = ["optical-module brief"]
    transceiver_data = live_status(action_input).result
    parsed_transceiver_data = huawei_vrp_parse_transceiver_data(transceiver_data, device_hostname, log)
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " transceiver data is gathered.")
    return parsed_transceiver_data


def huawei_vrp_get_device_cdb_interfaces(
    root: ncs.maagic.Root, device_hostname: str, log: ncs.log.Log
) -> ncs.maagic.Container:
    """Get device interfaces data from cdb."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    interfaces_data = root.ncs__devices.device[device_hostname].config.vrp__interface
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " interfaces data is gathered.")
    return interfaces_data


def huawei_vrp_populate_inventory_grouping(
    inventory_data: List[VrpInventory], inventory_name: str, device_hostname: str, log: ncs.log.Log
) -> None:
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


def huawei_vrp_populate_controllers_grouping(
    transceiver_data: List[VrpTransceiver], inventory_name: str, device_hostname: str, log: ncs.log.Log
) -> None:
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


def huawei_vrp_populate_interfaces_grouping(
    interface_data: ncs.maagic.Container, inventory_name: str, device_hostname: str, log: ncs.log.Log
) -> None:
    """Populate interface list under inventory device."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    if_sizes: List = [
        "Eth_Trunk",
        "GigabitEthernet",
        "Ethernet",
    ]
    with ncs.maapi.single_write_trans(USER, "system") as trans:
        inventory_manager = ncs.maagic.get_node(trans, f"/inv:inventory-manager{{{inventory_name}}}")
        device = inventory_manager.device[device_hostname]
        del device.interface  # Delete device interface list first to re-create from scratch
        log.info("Device ##" + INDENTATION * 2 + " interface list is deleted.")
        for if_size in if_sizes:
            for size in getattr(interface_data, if_size):
                if_number = str(size.name).split(".", maxsplit=1)[0]
                device.interface.create(size, if_number)
                log.info("Interface ##" + INDENTATION * 4 + if_size + " " + if_number + " is created.")
        trans.apply()


def alu_sr_get_device_live_status_card(
    root: ncs.maagic.Root, device_hostname: str, log: ncs.log.Log
) -> ncs.maagic.List:
    """Get device card data from ned live-status."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    card_data = root.ncs__devices.device[device_hostname].live_status.alu_stats__card
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " card data is gathered.")
    return card_data


def alu_sr_get_device_live_status_slot(
    root: ncs.maagic.Root, device_hostname: str, log: ncs.log.Log
) -> ncs.maagic.List:
    """Get device slot data from ned live-status."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    slot_data = root.ncs__devices.device[device_hostname].live_status.alu_stats__slot
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " card data is gathered.")
    return slot_data


def alu_sr_get_device_live_status_ports(
    root: ncs.maagic.Root, device_hostname: str, log: ncs.log.Log
) -> ncs.maagic.List:
    """Get device pots data from ned live-status."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    ports_data = root.ncs__devices.device[device_hostname].live_status.alu_stats__ports
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " ports data is gathered.")
    return ports_data


def alu_sr_get_device_cdb_interfaces(
    root: ncs.maagic.Root, device_hostname: str, log: ncs.log.Log
) -> Tuple[ncs.maagic.List, ncs.maagic.List]:
    """Get device ports and lags data from cdb."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    ports_data: ncs.maagic.List = root.ncs__devices.device[device_hostname].config.alu__port
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " ports data is gathered.")
    lags_data: ncs.maagic.List = root.ncs__devices.device[device_hostname].config.alu__lag
    log.info("Device ##" + INDENTATION * 2 + device_hostname + " lags data is gathered.")
    return ports_data, lags_data


def alu_sr_populate_inventory_grouping(
    card_data: ncs.maagic.List, slot_data: ncs.maagic.List, inventory_name: str, device_hostname: str, log: ncs.log.Log
) -> None:
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


def alu_sr_populate_controllers_grouping(
    ports_data: ncs.maagic.List, inventory_name: str, device_hostname: str, log: ncs.log.Log
) -> None:
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


def alu_sr_populate_interfaces_grouping(
    interface_data: Tuple[ncs.maagic.List, ncs.maagic.List], inventory_name: str, device_hostname: str, log: ncs.log.Log
) -> None:
    """Populate interface list under inventory device."""
    log.info("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    ports_data, lags_data = interface_data
    with ncs.maapi.single_write_trans(USER, "system") as trans:
        inventory_manager = ncs.maagic.get_node(trans, f"/inv:inventory-manager{{{inventory_name}}}")
        device = inventory_manager.device[device_hostname]
        del device.interface  # Delete device interface list first to re-create from scratch
        log.info("Device ##" + INDENTATION * 2 + " interface list is deleted.")
        for port in ports_data:
            if_size = "port"
            if_number = str(port.port_id)
            device.interface.create(if_size, if_number)
            log.info("Interface ##" + INDENTATION * 4 + if_size + " " + if_number + " is created.")
        for lag in lags_data:
            if_size = "lag"
            if_number = str(lag.id)
            device.interface.create(if_size, if_number)
            log.info("Interface ##" + INDENTATION * 4 + if_size + " " + if_number + " is created.")
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
                interface_data = iosxr_get_device_cdb_interfaces(root, hostname, self.log)
                iosxr_populate_inventory_grouping(inventory_data, inventory_name, hostname, self.log)
                iosxr_populate_controllers_grouping(controllers_data, inventory_name, hostname, self.log)
                iosxr_populate_interfaces_grouping(interface_data, inventory_name, hostname, self.log)

            elif platform == "huawei-vrp":
                self.log.info("Device ##" + INDENTATION * 2 + hostname + " platform is huawei-vrp.")
                inventory_data = huawei_vrp_get_device_live_status_exec_inventory(root, hostname, self.log)
                transceiver_data = huawei_vrp_get_device_live_status_exec_transceiver(root, hostname, self.log)
                interface_data = huawei_vrp_get_device_cdb_interfaces(root, hostname, self.log)
                huawei_vrp_populate_inventory_grouping(inventory_data, inventory_name, hostname, self.log)
                huawei_vrp_populate_controllers_grouping(transceiver_data, inventory_name, hostname, self.log)
                huawei_vrp_populate_interfaces_grouping(interface_data, inventory_name, hostname, self.log)

            else:
                self.log.info("Device ##" + INDENTATION * 2 + hostname + " platform is alu-sr.")
                card_data = alu_sr_get_device_live_status_card(root, hostname, self.log)
                slot_data = alu_sr_get_device_live_status_slot(root, hostname, self.log)
                ports_data = alu_sr_get_device_live_status_ports(root, hostname, self.log)
                interface_data = alu_sr_get_device_cdb_interfaces(root, hostname, self.log)
                alu_sr_populate_inventory_grouping(card_data, slot_data, inventory_name, hostname, self.log)
                alu_sr_populate_controllers_grouping(ports_data, inventory_name, hostname, self.log)
                alu_sr_populate_interfaces_grouping(interface_data, inventory_name, hostname, self.log)

        create_inventory_resource_pools(inventory_name, self.log)
        output.result = f"Devices processed: {len(devices)}"


# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Main(ncs.application.Application):
    """Inventory action class."""

    def setup(self):
        """Register service and actions."""
        self.log.info("Main RUNNING")

        # inventory service registration
        self.register_service("inventory-manager-servicepoint", InventoryCallbacks)

        # inventory update-inventory-manager action
        self.register_action("update-inventory-manager", InventoryUpdate)

        self.log.info("Main Application Started")

    def teardown(self):
        """Teardown."""
        self.log.info("Main FINISHED")
