from dataclasses import dataclass, field
from typing import Any, List, Optional

from ansible_collections.karlivory.zk.plugins.module_utils.utils import Utils


@dataclass
class Images:
    name: str
    url: str
    checksum: str
    firstboot_script: str
    pre_firstboot_uninstall_packages: str
    pre_firstboot_install_packages: str


# @dataclass
# class NetplanNameservers:
#     search: Optional[List[str]]
#     addresses: List[str]


# @dataclass
# class NetplanRoute:
#     to: Optional[str]
#     via: Optional[str]


# @dataclass
# class Netplan:
#     dhcp4: Optional[bool]
#     dhcp6: Optional[bool]
#     routes: Optional[List[NetplanRoute]]
#     addresses: Optional[List[str]]
#     nameservers: Optional[NetplanNameservers]


@dataclass
class ZkVMNetwork:
    name: str
    subnet: Optional[str]
    nic_type: Optional[str]  #  = field(metadata={"choices": ["network", "bridge"]})
    nic_source: Optional[str]
    nic_device_model: Optional[str]
    nic_bus: Optional[int]
    netplan: Optional[dict[str, Any]]


@dataclass
class VMNetwork:
    name: str
    subnet: str
    nic_type: str
    nic_source: str
    nic_device_model: str
    nic_bus: int
    netplan: Optional[dict[str, Any]]


@dataclass
class ZFSAutosnapPolicy:
    frequently: Optional[int]
    hourly: Optional[int]
    daily: Optional[int]
    monthly: Optional[int]
    yearly: Optional[int]


@dataclass
class ZFSProperties:
    volblocksize: Optional[str]
    compression: Optional[str]


@dataclass
class ZFS:
    autosnap_policy: Optional[ZFSAutosnapPolicy]
    properties: Optional[ZFSProperties]


@dataclass
class Disk:
    name: str
    size: str
    dev: str
    zfs: Optional[ZFS]


@dataclass
class VirtualNetworkForward:
    mode: str = field(metadata={"choices": ["nat", "route", "open"]})
    dev: Optional[str]


@dataclass
class VirtualNetworkIPv4DHCP:
    start: str
    end: str


@dataclass
class VirtualNetworkIPv4:
    address: str
    dev: Optional[str]
    dhcp: Optional[VirtualNetworkIPv4DHCP]


@dataclass
class LibvirtVirtualNetwork:
    name: str
    active: bool
    mode: str
    forward: Optional[VirtualNetworkForward]
    domain: Optional[str]
    ipv4: Optional[VirtualNetworkIPv4]


@dataclass
class VMUser:
    name: str
    groups: List[str]
    ssh_keys: List[str]
    passwordless_sudo: bool
    password: Optional[str]


@dataclass
class ZkVMUser:
    name: str
    groups: Optional[List[str]]
    ssh_keys: Optional[List[str]]
    passwordless_sudo: Optional[bool]
    password: Optional[str]


@dataclass
class ZkVM:
    zk_vm_name: str
    zk_vm_hostname: str
    zk_vm_disks: List[Disk]
    zk_vm_boot_disk_dev: str
    zk_vm_image: str
    zk_vm_networks: List[ZkVMNetwork]
    zk_vm_memory_mb: int
    zk_vm_vcpus: int
    zk_vm_qemu_machine_type: str
    zk_vm_prune_dangling_networks: bool
    zk_vm_prune_dangling_disks: bool
    zk_vm_users: List[ZkVMUser]


@dataclass
class VM:
    name: str
    hostname: str
    disks: List[Disk]
    boot_disk_dev: str
    image: str
    zk_networks: List[ZkVMNetwork]  # TODO can I get rid of this?
    networks: List[VMNetwork]
    memory_mb: int
    vcpus: int
    qemu_machine_type: str
    prune_dangling_networks: bool
    prune_dangling_disks: bool
    users: List[VMUser]

    @staticmethod
    def from_conf(vm: ZkVM):
        users = []
        for zk_user in vm.zk_vm_users:
            users.append(
                VMUser(
                    name=zk_user.name,
                    groups=Utils.try_from_values(
                        f"vm.name == {vm.zk_vm_name}",
                        f"vm.users[name == {zk_user.name}].groups",
                        [zk_user.groups, []],
                    ),
                    ssh_keys=Utils.try_from_values(
                        f"vm.name == {vm.zk_vm_name}",
                        f"vm.users[name == {zk_user.name}].ssh_keys",
                        [zk_user.ssh_keys, []],
                    ),
                    passwordless_sudo=Utils.try_from_values(
                        f"vm.name == {vm.zk_vm_name}",
                        f"vm.users[name == {zk_user.name}].passwordless_sudo",
                        [zk_user.passwordless_sudo, False],
                    ),
                    password=zk_user.password,
                )
            )
        return VM(
            name=vm.zk_vm_name,
            hostname=vm.zk_vm_hostname,
            disks=vm.zk_vm_disks,
            boot_disk_dev=vm.zk_vm_boot_disk_dev,
            image=vm.zk_vm_image,
            zk_networks=vm.zk_vm_networks,
            networks=[],
            memory_mb=vm.zk_vm_memory_mb,
            vcpus=vm.zk_vm_vcpus,
            qemu_machine_type=vm.zk_vm_qemu_machine_type,
            prune_dangling_disks=vm.zk_vm_prune_dangling_disks,
            prune_dangling_networks=vm.zk_vm_prune_dangling_networks,
            users=users,
        )


@dataclass
class ZkKVMHost:
    ansible_host: str
    zk_kvm_vms: List[VM]
    zk_kvm_images: List[Images]
    zk_kvm_zvol_parent: str
    zk_kvm_data_dir: str
    zk_kvm_memballoon_mem_limit_mb: int
    zk_kvm_networks: List[ZkVMNetwork]


@dataclass
class KVMHost:
    ansible_host: str
    images: List[Images]
    data_dir: str
    zvol_parent: str
    vms: List[VM]
    memballoon_mem_limit_mb: int
    networks: List[ZkVMNetwork]

    @staticmethod
    def with_merged_networks(
        vms: List[VM], kvm_networks: List[ZkVMNetwork]
    ) -> List[VM]:
        result = []
        for vm in vms:
            new_networks = []
            for zk_vm_network in vm.zk_networks:
                kvm_network = next(
                    (
                        kvm_network
                        for kvm_network in kvm_networks
                        if kvm_network.name == zk_vm_network.name
                    ),
                    ZkVMNetwork(
                        name=zk_vm_network.name,
                        subnet=None,
                        nic_bus=None,
                        nic_type=None,
                        nic_source=None,
                        nic_device_model=None,
                        netplan=None,
                    ),
                )
                nic_bus = Utils.try_from_values(
                    f"vm.name == {vm.name}",
                    "vm.network.nic_bus",
                    [zk_vm_network.nic_bus, kvm_network.nic_bus],
                )
                nic_device_model = Utils.try_from_values(
                    f"vm.name == {vm.name}",
                    "vm.network.nic_device_model",
                    [zk_vm_network.nic_device_model, kvm_network.nic_device_model],
                )
                nic_source = Utils.try_from_values(
                    f"vm.name == {vm.name}",
                    "vm.network.nic_source",
                    [zk_vm_network.nic_source, kvm_network.nic_source],
                )
                nic_type = Utils.try_from_values(
                    f"vm.name == {vm.name}",
                    "vm.network.nic_type",
                    [zk_vm_network.nic_type, kvm_network.nic_type],
                )
                subnet = Utils.try_from_values(
                    f"vm.name == {vm.name}",
                    "vm.network.subnet",
                    [zk_vm_network.subnet, kvm_network.subnet, "0.0.0.0/0"],
                )

                netplan = Utils.dict_merge(kvm_network.netplan, zk_vm_network.netplan)
                if netplan == {}:
                    netplan = None
                if netplan is not None:
                    netplan = {"network": {"ethernets": {f"enp{nic_bus}s0": netplan}}}

                network = VMNetwork(
                    name=zk_vm_network.name,
                    subnet=subnet,
                    nic_type=nic_type,
                    nic_bus=nic_bus,
                    nic_source=nic_source,
                    nic_device_model=nic_device_model,
                    netplan=netplan,
                )
                new_networks.append(network)

            vm.networks = new_networks
            result += [vm]
        return result

    @staticmethod
    def from_conf(conf: ZkKVMHost):
        kvm_networks = conf.zk_kvm_networks
        return KVMHost(
            vms=KVMHost.with_merged_networks(conf.zk_kvm_vms, kvm_networks),
            images=conf.zk_kvm_images,
            zvol_parent=conf.zk_kvm_zvol_parent,
            data_dir=conf.zk_kvm_data_dir,
            ansible_host=conf.ansible_host,
            memballoon_mem_limit_mb=conf.zk_kvm_memballoon_mem_limit_mb,
            networks=kvm_networks,
        )
