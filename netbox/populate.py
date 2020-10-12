from contextlib import suppress
from django.db.utils import IntegrityError
from utilities.choices import ColorChoices
from dcim.choices import InterfaceTypeChoices, PortTypeChoices, PowerPortTypeChoices, ConsolePortTypeChoices, RackTypeChoices

# Find an item with the given unique filter.  If it exists, update;
# if it does not exist, create.  Return the object.
def make(klass, filter, **defaults):
    instance, created = klass.objects.get_or_create(defaults=defaults, **filter)
    if not created:
        for attr, value in defaults.items():
            setattr(instance, attr, value)
        instance.save()
    return instance

def slugize(v):
    return v.lower().replace(" ", "_")

manuf = {}
manuf["cisco"] = make(Manufacturer, dict(slug="cisco"), name="Cisco")
manuf["unknown"] = make(Manufacturer, dict(slug="unknown"), name="Unknown")

platform = {}
platform["ios_xe"] = make(Platform, dict(slug="ios_xe"), name="IOS XE", manufacturer=manuf["cisco"], napalm_driver="ios")
platform["ubuntu"] = make(Platform, dict(slug="ubuntu"), name="Ubuntu")

device_type = {}
# IOSv
dt = device_type["iosv"] = make(DeviceType, dict(slug="iosv"),
    model="IOSv",
    manufacturer=manuf["cisco"],
    u_height=1,
    is_full_depth=True,
)
for i in range(4):
    make(InterfaceTemplate, dict(device_type=dt, name="GigabitEthernet0/%d" % i),
         type=InterfaceTypeChoices.TYPE_1GE_FIXED)   # maybe border Gi0/0 needs to change to TYPE_1GE_SFP

for i in range(1, 3):
    make(PowerPortTemplate, dict(device_type=dt, name="PSU%d" % i),
         type=PowerPortTypeChoices.TYPE_IEC_C14)

make(ConsolePortTemplate, dict(device_type=dt, name="CONSOLE"),
     type=ConsolePortTypeChoices.TYPE_RJ45)
make(ConsolePortTemplate, dict(device_type=dt, name="AUX"),
     type=ConsolePortTypeChoices.TYPE_RJ45)
# IOSvL2
dt = device_type["iosvl2"] = make(DeviceType, dict(slug="iosvl2"),
    model="IOSvL2",
    manufacturer=manuf["cisco"],
    u_height=1,
    is_full_depth=True,
)
for i in range(4):
    for j in range(4):
        make(InterfaceTemplate, dict(device_type=dt, name="GigabitEthernet%d/%d" % (i, j)),
             type=InterfaceTypeChoices.TYPE_1GE_FIXED)

for i in range(1, 3):
    make(PowerPortTemplate, dict(device_type=dt, name="PSU%d" % i),
         type=PowerPortTypeChoices.TYPE_IEC_C14)

make(ConsolePortTemplate, dict(device_type=dt, name="CONSOLE"),
     type=ConsolePortTypeChoices.TYPE_RJ45)
make(ConsolePortTemplate, dict(device_type=dt, name="AUX"),
     type=ConsolePortTypeChoices.TYPE_RJ45)
# Server
dt = device_type["generic_2u_server"] = make(DeviceType, dict(slug="generic_2u_server"),
    model="Generic 2U Server",
    manufacturer=manuf["unknown"],
    u_height=2,
    is_full_depth=True,
)
for i in range(2):
    make(InterfaceTemplate, dict(device_type=dt, name="eth%d" % i),
         type=InterfaceTypeChoices.TYPE_1GE_FIXED,
         mgmt_only=(i > 0))

for i in range(1, 3):
    make(PowerPortTemplate, dict(device_type=dt, name="PSU%d" % i),
         type=PowerPortTypeChoices.TYPE_IEC_C14)

# Fibre patch panel
dt = device_type["patch_fibre_12"] = make(DeviceType, dict(slug="patch_fibre_12"),
    model="Patch Fibre 12",
    manufacturer=manuf["unknown"],
    u_height=1,
    is_full_depth=False,
)
for i in range(1, 13):
    rp = make(RearPortTemplate, dict(device_type=dt, name="R%d" % i),
              positions=1, type=PortTypeChoices.TYPE_LC)
    fp = make(FrontPortTemplate, dict(device_type=dt, name="F%d" % i),
              rear_port=rp, rear_port_position=1, type=PortTypeChoices.TYPE_LC)

device_role = {}
for name, color, vm_role in [
    ("Border Router", ColorChoices.COLOR_DARK_GREEN, False),
    ("Core Router", ColorChoices.COLOR_GREEN, False),
    ("Distribution Switch", ColorChoices.COLOR_BLUE, False),
    ("Edge Switch", ColorChoices.COLOR_LIGHT_BLUE, False),
    ("Monitoring", ColorChoices.COLOR_DARK_RED, True),
    ("Patching", ColorChoices.COLOR_BLACK, False),
]:
    device_role[slugize(name)] = make(DeviceRole, dict(slug=slugize(name)), name=name, color=color, vm_role=vm_role)

site = {}
rack = {}
device = {}
for i in range(1,7):
    print("--- Campus %d ---" % i)
    s = site[i] = make(Site, dict(slug="campus_%d" % i), name="Campus %d" % i)
    rack[i] = {}
    rg = make(RackGroup, dict(site=s, slug="campus%d-core"), name="Campus %d Core" % i)
    rack[i]["c1"] = make(Rack, dict(site=s, group=rg, name="C1"),
                         type=RackTypeChoices.TYPE_CABINET)
    rg = make(RackGroup, dict(site=s, slug="campus%d-b1"), name="Campus %d Building 1" % i)
    rack[i]["b1-1"] = make(Rack, dict(site=s, group=rg, name="B1-1"),
                           type=RackTypeChoices.TYPE_WALLCABINET, u_height=6)
    rg = make(RackGroup, dict(site=s, slug="campus%d-b2"), name="Campus %d Building 2" % i)
    rack[i]["b2-1"] = make(Rack, dict(site=s, group=rg, name="B2-1"),
                           type=RackTypeChoices.TYPE_WALLCABINET, u_height=6)
    device[i] = {}
    # Core rack
    device[i]["pp-c1"] = make(Device, dict(site=s, name="pp-c1"),
                              rack=rack[i]["c1"], position=42, face="front",
                              device_type=device_type["patch_fibre_12"],
                              device_role=device_role["patching"])
    device[i]["bdr1"] = make(Device, dict(site=s, name="bdr1"),
                              rack=rack[i]["c1"], position=40, face="front",
                              device_type=device_type["iosv"],
                              device_role=device_role["border_router"],
                              platform=platform["ios_xe"])
    device[i]["core1"] = make(Device, dict(site=s, name="core1"),
                              rack=rack[i]["c1"], position=39, face="front",
                              device_type=device_type["iosvl2"],
                              device_role=device_role["core_router"],
                              platform=platform["ios_xe"])
    device[i]["srv1"] = make(Device, dict(site=s, name="srv1"),
                              rack=rack[i]["c1"], position=37, face="front",
                              device_type=device_type["generic_2u_server"],
                              device_role=device_role["monitoring"],
                              platform=platform["ubuntu"])
    # Building 1
    device[i]["pp-b1-1"] = make(Device, dict(site=s, name="pp-b1-1"),
                              rack=rack[i]["b1-1"], position=6, face="front",
                              device_type=device_type["patch_fibre_12"],
                              device_role=device_role["patching"])
    device[i]["dist1-b1"] = make(Device, dict(site=s, name="dist1-b1"),
                              rack=rack[i]["b1-1"], position=5, face="front",
                              device_type=device_type["iosvl2"],
                              device_role=device_role["distribution_switch"],
                              platform=platform["ios_xe"])
    device[i]["edge1-b1"] = make(Device, dict(site=s, name="edge1-b1"),
                              rack=rack[i]["b1-1"], position=4, face="front",
                              device_type=device_type["iosvl2"],
                              device_role=device_role["edge_switch"],
                              platform=platform["ios_xe"])
    device[i]["edge2-b1"] = make(Device, dict(site=s, name="edge2-b1"),
                              rack=rack[i]["b1-1"], position=3, face="front",
                              device_type=device_type["iosvl2"],
                              device_role=device_role["edge_switch"],
                              platform=platform["ios_xe"])
    # Building 2
    device[i]["pp-b2-1"] = make(Device, dict(site=s, name="pp-b2-1"),
                              rack=rack[i]["b2-1"], position=6, face="front",
                              device_type=device_type["patch_fibre_12"],
                              device_role=device_role["patching"])
    device[i]["dist1-b2"] = make(Device, dict(site=s, name="dist1-b2"),
                              rack=rack[i]["b2-1"], position=5, face="front",
                              device_type=device_type["iosvl2"],
                              device_role=device_role["distribution_switch"],
                              platform=platform["ios_xe"])
    device[i]["edge1-b2"] = make(Device, dict(site=s, name="edge1-b2"),
                              rack=rack[i]["b2-1"], position=4, face="front",
                              device_type=device_type["iosvl2"],
                              device_role=device_role["edge_switch"],
                              platform=platform["ios_xe"])
    device[i]["edge2-b2"] = make(Device, dict(site=s, name="edge2-b2"),
                              rack=rack[i]["b2-1"], position=3, face="front",
                              device_type=device_type["iosvl2"],
                              device_role=device_role["edge_switch"],
                              platform=platform["ios_xe"])

## Use virtualization model for hostX
lxd = make(ClusterType, dict(slug="lxd"), name="lxd", description="lxd containers")
for i in range(1,7):
    print("--- Campus %d ---" % i)
    for j in range(1,7):
        cluster = make(Cluster, dict(name="campus%d-cluster1" % i),
                       type=lxd, site=site[i])
        srv1 = device[i]["srv1"]
        srv1.cluster = cluster
        srv1.save()
        vm = make(VirtualMachine, dict(cluster=cluster, name="host%d" % j),
                  platform=platform["ubuntu"], role=device_role["monitoring"])
        eth0 = make(VMInterface, dict(virtual_machine=vm, name="eth0"))
        ip4 = make(IPAddress, dict(address="100.68.%d.%d/28" % (i, 130+j)),
                   assigned_object=eth0, dns_name="eth0.host%d.campus%d.ws.nsrc.org" % (j, i))
        ip6 = make(IPAddress, dict(address="2001:DB8:%d:1::%d/64" % (i, 130+j)),
                   assigned_object=eth0, dns_name="eth0.host%d.campus%d.ws.nsrc.org" % (j, i))
        vm.primary_ip4 = ip4
        vm.primary_ip6 = ip6
        vm.save()
        eth1 = make(VMInterface, dict(virtual_machine=vm, name="eth1"))
        ip4 = make(IPAddress, dict(address="100.64.0.%d/22" % (i*10 + j)),
                   assigned_object=eth1, dns_name="eth1.host%d.campus%d.ws.nsrc.org" % (j, i))

# End
