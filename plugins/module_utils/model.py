from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Image:
    name: str
    url: str
    checksum: str
    virt_customize_run_command: Optional[str]
    virt_customize_firstboot: Optional[str]
    virt_customize_firstboot_command: Optional[str]
    virt_customize_uninstall_packages: Optional[str]
    virt_customize_install_packages: Optional[str]


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
class ZFS:
    zvol_parent: Optional[str]
    properties: Optional[dict]


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
    zk_vm_image: str
    zk_vm_networks: List[ZkVMNetwork]
    zk_vm_networks_netplan_enabled: bool
    zk_vm_memory_mb: int
    zk_vm_vcpus: int
    zk_vm_qemu_machine_type: str
    zk_vm_prune_dangling_networks: bool
    zk_vm_prune_dangling_disks: bool
    zk_vm_default_users: List[ZkVMUser]
    zk_vm_users: List[ZkVMUser]
    zk_vm_post_setup_script: str
    zk_vm_post_setup_script_timeout: int
    zk_vm_disk_default_zfs_properties: dict
    zk_vm_disk_default_zvol_parent: Optional[str]


@dataclass
class VM:
    name: str
    hostname: str
    disks: List[Disk]
    image: str
    networks: List[VMNetwork]
    networks_netplan_enabled: bool
    memory_mb: int
    vcpus: int
    qemu_machine_type: str
    prune_dangling_networks: bool
    prune_dangling_disks: bool
    users: List[VMUser]
    post_setup_script: str
    post_setup_script_timeout: int
    # disk_default_zfs_properties: dict


@dataclass
class ZkKVMHost:
    ansible_host: str
    zk_kvm_vms: List[ZkVM]
    zk_kvm_images: List[Image]
    zk_kvm_data_dir: str
    zk_kvm_memballoon_mem_limit_mb: int
    zk_kvm_networks: List[ZkVMNetwork]


@dataclass
class KVMHost:
    ansible_host: str
    images: List[Image]
    data_dir: str
    vms: List[VM]
    memballoon_mem_limit_mb: int
