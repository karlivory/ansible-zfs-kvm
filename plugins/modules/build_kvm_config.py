#!/usr/bin/python
from dataclasses import asdict
from typing import List

from ansible_collections.karlivory.zk.plugins.module_utils.model import (
    VM, ZFS, KVMHost, VMNetwork, VMUser, ZkKVMHost, ZkVM, ZkVMNetwork)
from ansible_collections.karlivory.zk.plugins.module_utils.utils import (
    ModuleResult, Utils)


def vm_from_conf(vm: ZkVM) -> VM:
    users = []
    existing_user_names = {zk_user.name for zk_user in vm.zk_vm_users}
    for zk_default_user in vm.zk_vm_default_users:
        if zk_default_user.name not in existing_user_names:
            vm.zk_vm_users.append(zk_default_user)
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
    for disk in vm.zk_vm_disks:
        zfs_props = {
            **vm.zk_vm_disk_default_zfs_properties,
            **(disk.zfs.properties if disk.zfs and disk.zfs.properties else {}),
        }
        zvol_parent = (
            disk.zfs.zvol_parent
            if disk.zfs and disk.zfs.zvol_parent
            else vm.zk_vm_disk_default_zvol_parent
        )
        zfs_props.setdefault("volsize", disk.size)
        disk.zfs = ZFS(zvol_parent=zvol_parent, properties=zfs_props)

    return VM(
        name=vm.zk_vm_name,
        hostname=vm.zk_vm_hostname,
        disks=vm.zk_vm_disks,
        image=vm.zk_vm_image,
        networks=[],
        networks_netplan_enabled=vm.zk_vm_networks_netplan_enabled,
        memory_mb=vm.zk_vm_memory_mb,
        vcpus=vm.zk_vm_vcpus,
        qemu_machine_type=vm.zk_vm_qemu_machine_type,
        prune_dangling_disks=vm.zk_vm_prune_dangling_disks,
        prune_dangling_networks=vm.zk_vm_prune_dangling_networks,
        users=users,
        post_setup_script=vm.zk_vm_post_setup_script,
        post_setup_script_timeout=vm.zk_vm_post_setup_script_timeout,
    )


def build_vm(zk_vm: ZkVM, kvm_networks: List[ZkVMNetwork]) -> VM:
    new_networks = []
    for zk_vm_network in zk_vm.zk_vm_networks:
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
        vm_name = f"vm.name == {zk_vm.zk_vm_name}"
        nic_bus = Utils.try_from_values(
            vm_name,
            "vm.network.nic_bus",
            [zk_vm_network.nic_bus, kvm_network.nic_bus],
        )
        nic_device_model = Utils.try_from_values(
            vm_name,
            "vm.network.nic_device_model",
            [zk_vm_network.nic_device_model, kvm_network.nic_device_model],
        )
        nic_source = Utils.try_from_values(
            vm_name,
            "vm.network.nic_source",
            [zk_vm_network.nic_source, kvm_network.nic_source],
        )
        nic_type = Utils.try_from_values(
            vm_name,
            "vm.network.nic_type",
            [zk_vm_network.nic_type, kvm_network.nic_type],
        )
        subnet = Utils.try_from_values(
            vm_name,
            "vm.network.subnet",
            [zk_vm_network.subnet, kvm_network.subnet, "0.0.0.0/0"],
        )

        netplan = Utils.dict_merge(kvm_network.netplan, zk_vm_network.netplan)
        if netplan is None:
            netplan = {}
        else:
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

    vm: VM = vm_from_conf(zk_vm)
    vm.networks = new_networks
    return vm


def build_vms(zk_vms: List[ZkVM], kvm_networks: List[ZkVMNetwork]):
    result = []
    for zk_vm in zk_vms:
        result += [build_vm(zk_vm, kvm_networks)]
    return result


def build_kvm_config(_, args: ZkKVMHost) -> ModuleResult:
    new_vms = build_vms(args.zk_kvm_vms, args.zk_kvm_networks)
    config = KVMHost(
        vms=new_vms,
        images=args.zk_kvm_images,
        data_dir=args.zk_kvm_data_dir,
        ansible_host=args.ansible_host,
        memballoon_mem_limit_mb=args.zk_kvm_memballoon_mem_limit_mb,
    )

    return ModuleResult(output=asdict(config))


def main():
    Utils.run_module(ZkKVMHost, build_kvm_config)


if __name__ == "__main__":
    main()
