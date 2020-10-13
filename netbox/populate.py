from contextlib import suppress
from django.db.utils import IntegrityError
from utilities.choices import ColorChoices
from dcim.choices import (
    InterfaceTypeChoices, InterfaceModeChoices, PortTypeChoices, PowerPortTypeChoices, ConsolePortTypeChoices,
    RackTypeChoices, CableTypeChoices, CableLengthUnitChoices,
)
from ipam.choices import PrefixStatusChoices, IPAddressStatusChoices, IPAddressRoleChoices
from circuits.choices import CircuitTerminationSideChoices

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
    return v.lower().replace(" ", "-")

manuf = {}
manuf["cisco"] = make(Manufacturer, dict(slug="cisco"), name="Cisco")
manuf["generic"] = make(Manufacturer, dict(slug="generic"), name="Generic")

platform = {}
platform["ios-xe"] = make(Platform, dict(slug="ios-xe"), name="IOS XE", manufacturer=manuf["cisco"], napalm_driver="ios")
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
dt = device_type["2u-server"] = make(DeviceType, dict(slug="2u-server"),
    model="2U Server",
    manufacturer=manuf["generic"],
    u_height=2,
    is_full_depth=True,
)
for i in range(2):
    make(InterfaceTemplate, dict(device_type=dt, name="ens%d" % (i+3)),
         type=InterfaceTypeChoices.TYPE_1GE_FIXED)

for i in range(1, 3):
    make(PowerPortTemplate, dict(device_type=dt, name="PSU%d" % i),
         type=PowerPortTypeChoices.TYPE_IEC_C14)

# Fibre patch panel
dt = device_type["patch-fibre-12"] = make(DeviceType, dict(slug="patch-fibre-12"),
    model="Patch Fibre 12",
    manufacturer=manuf["generic"],
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
    ("Monitoring", ColorChoices.COLOR_ORANGE, True),
    ("Patching", ColorChoices.COLOR_BLACK, False),
]:
    device_role[slugize(name)] = make(DeviceRole, dict(slug=slugize(name)), name=name, color=color, vm_role=vm_role)

## Campuses, campus racks and devices
site = {}
rack = {}
device = {}
for i in range(1,7):
    print("--- Campus %d devices ---" % i)
    s = site[i] = make(Site, dict(slug="campus-%d" % i), name="Campus %d" % i, asn=i*10)
    rack[i] = {}
    rg = make(RackGroup, dict(site=s, slug="campus%d-core" % i), name="Campus %d Core" % i)
    rack[i]["c1"] = make(Rack, dict(site=s, group=rg, name="C1"),
                         type=RackTypeChoices.TYPE_CABINET)
    rg = make(RackGroup, dict(site=s, slug="campus%d-b1" % i), name="Campus %d Building 1" % i)
    rack[i]["b1-1"] = make(Rack, dict(site=s, group=rg, name="B1-1"),
                           type=RackTypeChoices.TYPE_WALLCABINET, u_height=6)
    rg = make(RackGroup, dict(site=s, slug="campus%d-b2" % i), name="Campus %d Building 2" % i)
    rack[i]["b2-1"] = make(Rack, dict(site=s, group=rg, name="B2-1"),
                           type=RackTypeChoices.TYPE_WALLCABINET, u_height=6)
    device[i] = {}
    # Core rack
    device[i]["pp-c1"] = make(Device, dict(site=s, name="pp-c1"),
                              rack=rack[i]["c1"], position=42, face="front",
                              device_type=device_type["patch-fibre-12"],
                              device_role=device_role["patching"])
    # bdr1
    d = device[i]["bdr1"] = make(Device, dict(site=s, name="bdr1"),
                              rack=rack[i]["c1"], position=40, face="front",
                              device_type=device_type["iosv"],
                              device_role=device_role["border-router"],
                              platform=platform["ios-xe"])
    intf = make(Interface, dict(device=d, name="GigabitEthernet0/0"))
    ip4 = make(IPAddress, dict(address="100.68.0.%d/30" % ((i-1)*4 + 2)),
               assigned_object=intf, dns_name="gi0-0.bdr1.campus%d.ws.nsrc.org" % i)
    ip6 = make(IPAddress, dict(address="2001:db8:100:%d::1/127" % i),
               assigned_object=intf, dns_name="gi0-0.bdr1.campus%d.ws.nsrc.org" % i)
    intf = make(Interface, dict(device=d, name="GigabitEthernet0/1"))
    ip4 = make(IPAddress, dict(address="100.68.%d.1/28" % i),
               assigned_object=intf, dns_name="gi0-1.bdr1.campus%d.ws.nsrc.org" % i)
    ip6 = make(IPAddress, dict(address="2001:db8:%d::1/64" % i),
               assigned_object=intf, dns_name="gi0-1.bdr1.campus%d.ws.nsrc.org" % i)
    intf = make(Interface, dict(device=d, name="GigabitEthernet0/2"), enabled=False)
    ip4 = make(IPAddress, dict(address="100.68.0.%d/30" % ((i-1)*4 + 130)),
               status=IPAddressStatusChoices.STATUS_RESERVED,
               assigned_object=intf, dns_name="gi0-2.bdr1.campus%d.ws.nsrc.org" % i)
    ip6 = make(IPAddress, dict(address="2001:db8:100:%d::1/127" % (i + 32)),
               status=IPAddressStatusChoices.STATUS_RESERVED,
               assigned_object=intf, dns_name="gi0-2.bdr1.campus%d.ws.nsrc.org" % i)
    intf = make(Interface, dict(device=d, name="Loopback0"),
                type=InterfaceTypeChoices.TYPE_VIRTUAL)
    ip4 = make(IPAddress, dict(address="100.68.%d.241/32" % i),
               role=IPAddressRoleChoices.ROLE_LOOPBACK,
               assigned_object=intf, dns_name="lo0.bdr1.campus%d.ws.nsrc.org" % i)
    ip6 = make(IPAddress, dict(address="2001:db8:%d:2::241/128" % i),
               role=IPAddressRoleChoices.ROLE_LOOPBACK,
               assigned_object=intf, dns_name="lo0.bdr1.campus%d.ws.nsrc.org" % i)
    d.primary_ip4 = ip4
    d.primary_ip6 = ip6
    d.save()
    # core1
    d = device[i]["core1"] = make(Device, dict(site=s, name="core1"),
                              rack=rack[i]["c1"], position=39, face="front",
                              device_type=device_type["iosvl2"],
                              device_role=device_role["core-router"],
                              platform=platform["ios-xe"])
    intf = make(Interface, dict(device=d, name="GigabitEthernet0/0"))
    ip4 = make(IPAddress, dict(address="100.68.%d.2/28" % i),
               assigned_object=intf, dns_name="gi0-1.core1.campus%d.ws.nsrc.org" % i)
    ip6 = make(IPAddress, dict(address="2001:db8:%d::2/64" % i),
               assigned_object=intf, dns_name="gi0-1.core1.campus%d.ws.nsrc.org" % i)
    intf = make(Interface, dict(device=d, name="GigabitEthernet0/3"))
    ip4 = make(IPAddress, dict(address="100.68.%d.129/28" % i),
               assigned_object=intf, dns_name="gi0-3.core1.campus%d.ws.nsrc.org" % i)
    ip6 = make(IPAddress, dict(address="2001:db8:%d:1::1/64" % i),
               assigned_object=intf, dns_name="gi0-3.core1.campus%d.ws.nsrc.org" % i)
    intf = make(Interface, dict(device=d, name="Loopback0"),
                type=InterfaceTypeChoices.TYPE_VIRTUAL)
    ip4 = make(IPAddress, dict(address="100.68.%d.242/32" % i),
               role=IPAddressRoleChoices.ROLE_LOOPBACK,
               assigned_object=intf, dns_name="lo0.core1.campus%d.ws.nsrc.org" % i)
    ip6 = make(IPAddress, dict(address="2001:db8:%d:2::242/128" % i),
               role=IPAddressRoleChoices.ROLE_LOOPBACK,
               assigned_object=intf, dns_name="lo0.core1.campus%d.ws.nsrc.org" % i)
    d.primary_ip4 = ip4
    d.primary_ip6 = ip6
    d.save()
    for vid in [10, 11, 12, 20, 21, 22]:
        intf = make(Interface, dict(device=d, name="Vlan%d" % vid),
                    type=InterfaceTypeChoices.TYPE_VIRTUAL)
        ip4 = make(IPAddress, dict(address="172.%d.%d.1/24" % (i + 20, vid)),
                   assigned_object=intf, dns_name="vlan%d.core1.campus%d.ws.nsrc.org" % (vid, i))
        ip6 = make(IPAddress, dict(address="2001:db8:%d:%d::1/64" % (i, vid)),
                   assigned_object=intf, dns_name="vlan%d.core1.campus%d.ws.nsrc.org" % (vid, i))
    # srv1
    d = device[i]["srv1"] = make(Device, dict(site=s, name="srv1"),
                              rack=rack[i]["c1"], position=37, face="front",
                              device_type=device_type["2u-server"],
                              device_role=device_role["monitoring"],
                              platform=platform["ubuntu"])
    intf = make(Interface, dict(device=d, name="br0"),
                type=InterfaceTypeChoices.TYPE_VIRTUAL)
    ip4 = make(IPAddress, dict(address="100.68.%d.130/28" % i),
               assigned_object=intf, dns_name="br0.srv1.campus%d.ws.nsrc.org" % i)
    ip6 = make(IPAddress, dict(address="2001:db8:%d:1::130/64" % i),
               assigned_object=intf, dns_name="br0.srv1.campus%d.ws.nsrc.org" % i)
    d.primary_ip4 = ip4
    d.primary_ip6 = ip6
    d.save()
    intf = make(Interface, dict(device=d, name="br1"),
                type=InterfaceTypeChoices.TYPE_VIRTUAL)
    ip4 = make(IPAddress, dict(address="100.64.0.%d/22" % (i*10)),
               assigned_object=intf, dns_name="br1.srv1.campus%d.ws.nsrc.org" % i)
    # Patch panels
    device[i]["pp-b1-1"] = make(Device, dict(site=s, name="pp-b1-1"),
                              rack=rack[i]["b1-1"], position=6, face="front",
                              device_type=device_type["patch-fibre-12"],
                              device_role=device_role["patching"])
    device[i]["pp-b2-1"] = make(Device, dict(site=s, name="pp-b2-1"),
                              rack=rack[i]["b2-1"], position=6, face="front",
                              device_type=device_type["patch-fibre-12"],
                              device_role=device_role["patching"])
    # Switches
    for name, r, position, role, vid, offset in [
        ("dist1-b1", "b1-1", 5, "distribution-switch", 10, 2),
        ("edge1-b1", "b1-1", 4, "edge-switch", 10, 3),
        ("edge2-b1", "b1-1", 3, "edge-switch", 10, 4),
        ("dist1-b2", "b2-1", 5, "distribution-switch", 20, 2),
        ("edge1-b2", "b2-1", 4, "edge-switch", 20, 3),
        ("edge2-b2", "b2-1", 3, "edge-switch", 20, 4),
    ]:
        d = device[i][name] = make(Device, dict(site=s, name=name),
                              rack=rack[i][r], position=position, face="front",
                              device_type=device_type["iosvl2"],
                              device_role=device_role[role],
                              platform=platform["ios-xe"])
        intf = make(Interface, dict(device=d, name="Vlan%d" % vid),
                    type=InterfaceTypeChoices.TYPE_VIRTUAL)
        ip4 = make(IPAddress, dict(address="172.%d.%d.%d/24" % (i + 20, vid, offset)),
                   assigned_object=intf, dns_name="%s.campus%d.ws.nsrc.org" % (name, i))
        ip6 = make(IPAddress, dict(address="2001:db8:%d:%d::%d/64" % (i, vid, offset)),
                   assigned_object=intf, dns_name="%s.campus%d.ws.nsrc.org" % (name, i))
        d.primary_ip4 = ip4
        d.primary_ip6 = ip6
        d.save()

## NREN
nren = make(Site, dict(slug="nren"), name="NREN", asn=65534)
device[0] = {}
for n in range(1,3):
    name = "transit%d-nren" % n
    d = device[0][name] = make(Device, dict(site=nren, name=name),
            device_type=device_type["iosv"],
            device_role=device_role["border-router"],
            platform=platform["ios-xe"])
    intf = make(Interface, dict(device=d, name="GigabitEthernet0/0"),
                type=InterfaceTypeChoices.TYPE_1GE_FIXED)
    ip4 = make(IPAddress, dict(address="100.64.0.%d/22" % (n+1)),
               assigned_object=intf, dns_name="gi0-0.transit%d.ws.nsrc.org" % n)
    ip6 = make(IPAddress, dict(address="2001:db8::%d/64" % (n+1)),
               assigned_object=intf, dns_name="gi0-0.transit%d.ws.nsrc.org" % n)
    for i in range(1,7):
        linknet = i + (n-1)*32
        intf = make(Interface, dict(device=d, name="GigabitEthernet0/%d" % i),
                    type=InterfaceTypeChoices.TYPE_1GE_FIXED)
        ip4 = make(IPAddress, dict(address="100.68.0.%d/30" % (4*linknet - 3)),
                   assigned_object=intf, dns_name="gi0-%d.transit%d.ws.nsrc.org" % (i, n))
        ip6 = make(IPAddress, dict(address="2001:db8:100:%d::/127" % linknet),
                   assigned_object=intf, dns_name="gi0-%d.transit%d.ws.nsrc.org" % (i, n))
    intf = make(Interface, dict(device=d, name="Loopback0"),
                type=InterfaceTypeChoices.TYPE_VIRTUAL)
    ip4 = make(IPAddress, dict(address="100.68.0.%d/32" % (n+250)),
               role=IPAddressRoleChoices.ROLE_LOOPBACK,
               assigned_object=intf, dns_name="lo0.transit%d.ws.nsrc.org" % n)
    ip6 = make(IPAddress, dict(address="2001:db8:100:ff::%d/128" % (n+250)),
               role=IPAddressRoleChoices.ROLE_LOOPBACK,
               assigned_object=intf, dns_name="lo0.transit%d.ws.nsrc.org" % n)
    d.primary_ip4 = ip4
    d.primary_ip6 = ip6
    d.save()

intf = make(Interface, dict(device=device[0]["transit1-nren"], name="GigabitEthernet0/0"))
ip4 = make(IPAddress, dict(address="100.64.0.254/22"),
           role=IPAddressRoleChoices.ROLE_SECONDARY,
           assigned_object=intf, dns_name="transit.nren.ws.nsrc.org")
ip6 = make(IPAddress, dict(address="2001:db8::254/64"),
           role=IPAddressRoleChoices.ROLE_SECONDARY,
           assigned_object=intf, dns_name="transit.nren.ws.nsrc.org")

## IPAM: vlans and subnets
private = make(RIR, dict(slug="private"), name="Private", is_private=True)
make(Aggregate, dict(prefix="192.168.0.0/16"), rir=private, description="RFC 1918 private use")
make(Aggregate, dict(prefix="172.16.0.0/12"), rir=private, description="RFC 1918 private use")
make(Aggregate, dict(prefix="10.0.0.0/8"), rir=private, description="RFC 1918 private use")
make(Aggregate, dict(prefix="100.64.0.0/10"), rir=private, description="RFC 6598 shared address space for CGN")
make(Aggregate, dict(prefix="2001:db8::/32"), rir=private, description="RFC 3849 documentation prefix")
make(Prefix, dict(prefix="100.64.0.0/22"),
     description="Class backbone")
make(Prefix, dict(prefix="100.68.0.0/24"),
     site=nren, status=PrefixStatusChoices.STATUS_CONTAINER,
     description="NREN")
make(Prefix, dict(prefix="2001:db8:100::/48"),
     site=nren, status=PrefixStatusChoices.STATUS_CONTAINER,
     description="NREN")
for i in range(1,7):
    print("--- Campus %d ipam ---" % i)
    make(Prefix, dict(prefix="100.68.0.%d/30" % ((i-1)*4)),
         site=site[i],
         description="Campus %d NREN P2P" % i)
    make(Prefix, dict(prefix="2001:db8:100:%d::/127" % i),
         site=site[i],
         description="Campus %d NREN P2P" % i)
    make(Prefix, dict(prefix="100.68.0.%d/30" % (((i-1)*4)+128)),
         site=site[i],
         description="Campus %d NREN backup P2P" % i)
    make(Prefix, dict(prefix="2001:db8:100:%d::/127" % (i+32)),
         site=site[i],
         description="Campus %d NREN backup P2P" % i)
    make(Prefix, dict(prefix="100.68.%d.0/24" % i),
         site=site[i], status=PrefixStatusChoices.STATUS_CONTAINER,
         description="Campus %d public IPv4" %i)
    make(Prefix, dict(prefix="172.%d.0.0/16" % (20+i)),
         site=site[i], status=PrefixStatusChoices.STATUS_CONTAINER,
         description="Campus %d private IPv4" % i)
    make(Prefix, dict(prefix="2001:db8:%d::/48" % i),
         site=site[i], status=PrefixStatusChoices.STATUS_CONTAINER,
         description="Campus %d IPv6" % i)
    make(Prefix, dict(prefix="100.68.%d.0/28" % i),
         site=site[i],
         description="Router core")
    make(Prefix, dict(prefix="2001:db8:%d::/64" % i),
         site=site[i],
         description="Router core")
    make(Prefix, dict(prefix="100.68.%d.32/28" % i),
         site=site[i],
         description="NAT pool", is_pool=True)
    make(Prefix, dict(prefix="100.68.%d.128/28" % i),
         site=site[i],
         description="Servers")
    make(Prefix, dict(prefix="2001:db8:%d:1::/64" % i),
         site=site[i],
         description="Servers")
    make(Prefix, dict(prefix="100.68.%d.240/28" % i),
         site=site[i],
         description="Loopbacks", is_pool=True)
    make(Prefix, dict(prefix="2001:db8:%d:2::/64" % i),
         site=site[i],
         description="Loopbacks", is_pool=True)
    for vid, description in [
        (10, "Building 1 Management"),
        (11, "Building 1 Staff"),
        (12, "Building 1 Student"),
        (20, "Building 2 Management"),
        (21, "Building 2 Staff"),
        (22, "Building 2 Student"),
    ]:
        vlan = make(VLAN, dict(site=site[i], vid=vid), description=description)
        make(Prefix, dict(prefix="172.%d.%d.0/24" % (20+i, vid)),
             site=site[i],
             description=description, vlan=vlan)
        make(Prefix, dict(prefix="2001:db8:%d:%d::/64" % (i, vid)),
             site=site[i],
             description=description, vlan=vlan)

## Cabling and tagging
tt_rearport = ContentType.objects.get(app_label="dcim",model="rearport")
tt_frontport = ContentType.objects.get(app_label="dcim",model="frontport")
tt_interface = ContentType.objects.get(app_label="dcim",model="interface")
tt_termination = ContentType.objects.get(app_label="circuits",model="circuittermination")
for i in range(1,7):
    # Rear port connections between patch panels
    make(Cable, dict(
            termination_a_type=tt_rearport,
            termination_a_id=RearPort.objects.get(device=device[i]["pp-c1"], name="R1").pk,
            termination_b_type=tt_rearport,
            termination_b_id=RearPort.objects.get(device=device[i]["pp-b1-1"], name="R1").pk,
         ), type=CableTypeChoices.TYPE_SMF_OS2, color=ColorChoices.COLOR_PURPLE)
    make(Cable, dict(
            termination_a_type=tt_rearport,
            termination_a_id=RearPort.objects.get(device=device[i]["pp-c1"], name="R2").pk,
            termination_b_type=tt_rearport,
            termination_b_id=RearPort.objects.get(device=device[i]["pp-b2-1"], name="R1").pk,
         ), type=CableTypeChoices.TYPE_SMF_OS2, color=ColorChoices.COLOR_PURPLE)
    # bdr1 to core1
    make(Cable, dict(
            termination_a_type=tt_interface,
            termination_a_id=Interface.objects.get(device=device[i]["bdr1"], name="GigabitEthernet0/1").pk,
            termination_b_type=tt_interface,
            termination_b_id=Interface.objects.get(device=device[i]["core1"], name="GigabitEthernet0/0").pk,
         ), type=CableTypeChoices.TYPE_CAT5E, color=ColorChoices.COLOR_GREY)
    # core1 to pp (change interfaces to SFP)
    intf = make(Interface, dict(device=device[i]["core1"], name="GigabitEthernet0/1"),
                type=InterfaceTypeChoices.TYPE_1GE_SFP, mode=InterfaceModeChoices.MODE_TAGGED)
    intf.tagged_vlans.set(VLAN.objects.filter(site=site[i], vid__in=[10,11,12]))
    make(Cable, dict(
            termination_a_type=tt_interface,
            termination_a_id=intf.pk,
            termination_b_type=tt_frontport,
            termination_b_id=FrontPort.objects.get(device=device[i]["pp-c1"], name="F1").pk,
         ), type=CableTypeChoices.TYPE_SMF_OS2, color=ColorChoices.COLOR_YELLOW,
            length=100, length_unit=CableLengthUnitChoices.UNIT_CENTIMETER)
    intf = make(Interface, dict(device=device[i]["core1"], name="GigabitEthernet0/2"),
                type=InterfaceTypeChoices.TYPE_1GE_SFP, mode=InterfaceModeChoices.MODE_TAGGED)
    intf.tagged_vlans.set(VLAN.objects.filter(site=site[i], vid__in=[20,21,22]))
    make(Cable, dict(
            termination_a_type=tt_interface,
            termination_a_id=intf.pk,
            termination_b_type=tt_frontport,
            termination_b_id=FrontPort.objects.get(device=device[i]["pp-c1"], name="F2").pk,
         ), type=CableTypeChoices.TYPE_SMF_OS2, color=ColorChoices.COLOR_YELLOW,
            length=100, length_unit=CableLengthUnitChoices.UNIT_CENTIMETER)
    # core1 to srv
    make(Cable, dict(
            termination_a_type=tt_interface,
            termination_a_id=Interface.objects.get(device=device[i]["core1"], name="GigabitEthernet0/3").pk,
            termination_b_type=tt_interface,
            termination_b_id=Interface.objects.get(device=device[i]["srv1"], name="ens3").pk,
         ), type=CableTypeChoices.TYPE_CAT5E, color=ColorChoices.COLOR_GREY)
    for b in range(1,3):
        # dist1-bX to pp
        intf = make(Interface, dict(device=device[i]["dist1-b%d" % b], name="GigabitEthernet0/0"),
                    type=InterfaceTypeChoices.TYPE_1GE_SFP, mode=InterfaceModeChoices.MODE_TAGGED_ALL)
        make(Cable, dict(
            termination_a_type=tt_interface,
            termination_a_id=intf.pk,
            termination_b_type=tt_frontport,
            termination_b_id=FrontPort.objects.get(device=device[i]["pp-b%d-1" % b], name="F1").pk,
            ), type=CableTypeChoices.TYPE_SMF_OS2, color=ColorChoices.COLOR_YELLOW,
            length=100, length_unit=CableLengthUnitChoices.UNIT_CENTIMETER)
        # dist-bX to edge1-bX
        make(Cable, dict(
                termination_a_type=tt_interface,
                termination_a_id=Interface.objects.get(device=device[i]["dist1-b%d" % b], name="GigabitEthernet1/0").pk,
                termination_b_type=tt_interface,
                termination_b_id=Interface.objects.get(device=device[i]["edge1-b%d" % b], name="GigabitEthernet0/0").pk,
             ), type=CableTypeChoices.TYPE_CAT5E, color=ColorChoices.COLOR_GREY)
        make(Cable, dict(
                termination_a_type=tt_interface,
                termination_a_id=Interface.objects.get(device=device[i]["dist1-b%d" % b], name="GigabitEthernet1/1").pk,
                termination_b_type=tt_interface,
                termination_b_id=Interface.objects.get(device=device[i]["edge1-b%d" % b], name="GigabitEthernet0/1").pk,
             ), type=CableTypeChoices.TYPE_CAT5E, color=ColorChoices.COLOR_GREY)
        # dist-bX to edge2-bX
        make(Cable, dict(
                termination_a_type=tt_interface,
                termination_a_id=Interface.objects.get(device=device[i]["dist1-b%d" % b], name="GigabitEthernet2/0").pk,
                termination_b_type=tt_interface,
                termination_b_id=Interface.objects.get(device=device[i]["edge2-b%d" % b], name="GigabitEthernet0/0").pk,
             ), type=CableTypeChoices.TYPE_CAT5E, color=ColorChoices.COLOR_GREY)
        # create Port-channel1
        lag = make(Interface, dict(device=device[i]["dist1-b%d" % b], name="Port-channel1"),
                   type=InterfaceTypeChoices.TYPE_LAG, mode=InterfaceModeChoices.MODE_TAGGED_ALL)
        for ifname in ["GigabitEthernet1/0", "GigabitEthernet1/1"]:
            intf = Interface.objects.get(device=device[i]["dist1-b%d" % b], name=ifname)
            intf.lag = lag
            intf.save()
        lag = make(Interface, dict(device=device[i]["edge1-b%d" % b], name="Port-channel1"),
                   type=InterfaceTypeChoices.TYPE_LAG, mode=InterfaceModeChoices.MODE_TAGGED_ALL)
        for ifname in ["GigabitEthernet0/0", "GigabitEthernet0/1"]:
            intf = Interface.objects.get(device=device[i]["edge1-b%d" % b], name=ifname)
            intf.lag = lag
            intf.save()
        # mark other interfaces as tagged
        for dev, ifname in [
            ("dist1-b%d" % b, "GigabitEthernet2/0"),
            ("edge2-b%d" % b, "GigabitEthernet0/0"),
        ]:
            intf = Interface.objects.get(device=device[i][dev], name=ifname)
            intf.mode = InterfaceModeChoices.MODE_TAGGED_ALL
            intf.save()
        # mark access ports
        for e in range(1,3):        # which edge switch
            for blk in range(1,3):  # which block of ports
                v = VLAN.objects.get(site=site[i], vid=b*10 + blk)
                for port in range(4):
                    intf = Interface.objects.get(device=device[i]["edge%d-b%d" % (e, b)], name="GigabitEthernet%d/%d" % (blk, port))
                    intf.mode = InterfaceModeChoices.MODE_ACCESS
                    intf.untagged_vlan = v
                    intf.save()

## Circuits between NREN and campuses
provider = make(Provider, dict(slug="pelican-crossing"),
                name="Pelican Crossing", portal_url="https://nsrc.org/", comments="A fake provider")
circuit_type = make(CircuitType, dict(slug="metro"),
                name="Metro")
for n in range(1,3):  # transit1-nren and transit2-nren
    for i in range(1,7):
        circuit = make(Circuit, dict(provider=provider, cid="campus%d-%02d" % (i, n)),
                       type=circuit_type, commit_rate=1000000)
        term_a = make(CircuitTermination, dict(circuit=circuit, term_side=CircuitTerminationSideChoices.SIDE_A),
                      site=nren, port_speed=1000000, upstream_speed=1000000)
        term_z = make(CircuitTermination, dict(circuit=circuit, term_side=CircuitTerminationSideChoices.SIDE_Z),
                      site=site[i], port_speed=1000000, upstream_speed=1000000)
        # A end to NREN router
        make(Cable, dict(
                termination_a_type=tt_interface,
                termination_a_id=Interface.objects.get(device=device[0]["transit%d-nren" % n], name="GigabitEthernet0/%d" % i).pk,
                termination_b_type=tt_termination,
                termination_b_id=term_a.pk,
            ))
        # Z end to campus bdr1
        make(Cable, dict(
                termination_a_type=tt_interface,
                termination_a_id=Interface.objects.get(device=device[i]["bdr1"], name="GigabitEthernet0/%d" % ((n-1)*2)).pk,
                termination_b_type=tt_termination,
                termination_b_id=term_z.pk,
            ))

## Use virtualization model for hostX
lxd = make(ClusterType, dict(slug="lxd"), name="lxd", description="lxd containers")
for i in range(1,7):
    print("--- Campus %d virtualization ---" % i)
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
