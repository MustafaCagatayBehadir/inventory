"""Inventory Action Module."""
import inspect
import ncs
import _ncs

INDENTATION = " "
USER = "admin"


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
            controller = device.controller.create
            

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
                interface_data = huawei_vrp_get_device_live_status_interface(root, hostname, self.log)
                transceiver_data = huawei_vrp_get_device_live_status_transceiver(root, hostname, self.log)


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
