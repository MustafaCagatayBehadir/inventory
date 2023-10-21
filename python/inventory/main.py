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


def get_device_live_status_inventory(root: ncs.maagic.Root, hostname: str, log: ncs.log.Log) -> ncs.maagic.List:
    """Get device inventory data from ned live-status."""
    log.debug("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    inventory_data = root.ncs__devices.device[hostname].live_status.cisco_ios_xr_stats__inventory
    log.info("Device ##" + INDENTATION * 2 + hostname + " inventory data is gathered.")
    return inventory_data


def get_device_live_status_controllers(root: ncs.maagic.Root, hostname: str, log: ncs.log.Log) -> ncs.maagic.List:
    """Get device controllers data from ned live-status."""
    log.debug("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    controllers_data = root.ncs__devices.device[hostname].live_status.cisco_ios_xr_stats__controllers
    log.info("Device ##" + INDENTATION * 2 + hostname + " controllers data is gathered.")
    return controllers_data


def populate_device_grouping(inventory_name: str, device_hostname: str, log: ncs.log.Log) -> None:
    """Populate device information under inventory device."""
    log.debug("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    with ncs.maapi.single_write_trans(USER, 'system') as trans:
        platform = ncs.maagic.get_node(trans, f"/ncs:devices/device{{{device_hostname}}}/platform")
        inventory_manager = ncs.maagic.get_node(trans, f"/inv:inventory-manager{{{inventory_name}}}")
        device = inventory_manager.device[device_hostname]
        device.platform = platform.name
        device.version = platform.version
        device.model = platform.model
        device.serial_number = platform.serial_number
        log.info("Device ##" + INDENTATION * 2 + device_hostname + " platform details are setted.")
        trans.apply()


def populate_inventory_grouping(inventory_data: ncs.maagic.List, inventory_name: str, device_hostname: str,
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


def populate_controllers_grouping(controllers_data: ncs.maagic.List, inventory_name: str, device_hostname: str,
                                  log: ncs.log.Log) -> None:
    """Populate controllers list under inventory device."""
    log.debug("Function ##" + INDENTATION * 2 + inspect.stack()[0][3])
    with ncs.maapi.single_write_trans(USER, 'system') as trans:
        for data in controllers_data.Optics:
            instance = data.instance
            transceiver = instance.transceiver_vendor_details
            inventory_manager = ncs.maagic.get_node(trans, f"/inv:inventory-manager{{{inventory_name}}}")
            device = inventory_manager.device[device_hostname]
            controller = device.controller.create(data.id)
            controller.controller_state = instance.controller_state
            controller.optics_type = transceiver.optics_type
            controller.name = transceiver.name
            controller.part_number = transceiver.part_number
            controller.serial_number = transceiver.serial_number
            controller.pid = transceiver.pid
            log.info("Controller ##" + INDENTATION * 4 + data.id + " is created.")
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
            inventory_data = get_device_live_status_inventory(root, hostname, self.log)
            controllers_data = get_device_live_status_controllers(root, hostname, self.log)
            populate_device_grouping(inventory_name, hostname, self.log)
            populate_inventory_grouping(inventory_data, inventory_name, hostname, self.log)
            populate_controllers_grouping(controllers_data, inventory_name, hostname, self.log)

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
