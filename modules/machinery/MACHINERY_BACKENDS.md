# Machine management backends

The scheduler uses the configured backend to manage analysis machines. Each adapter implements the lifecycle operations supported by its platform.

| Source | Role |
| --- | --- |
| [aws.py](aws.py) | Manages analysis instances in Amazon EC2. |
| [az.py](az.py) | Manages Azure analysis machines and their pool. |
| [esx.py](esx.py) | Controls ESX and ESXi guests through libvirt. |
| [gcp.py](gcp.py) | Manages analysis instances on Google Cloud. |
| [hyperv.py](hyperv.py) | Controls virtual machines on Microsoft Hyper-V. |
| [kvm.py](kvm.py) | Controls local KVM guests through libvirt. |
| [kvmremote.py](kvmremote.py) | Controls KVM guests on a remote virtualization host. |
| [multi.py](multi.py) | Delegates operations to multiple configured machinery backends. |
| [physical.py](physical.py) | Coordinates analysis on physical machines. |
| [proxmox.py](proxmox.py) | Manages guests through Proxmox. |
| [qemu.py](qemu.py) | Runs analysis guests with QEMU. |
| [qemu_external.py](qemu_external.py) | Manages QEMU guests with per-machine boot settings and traffic capture. |
| [virtualbox.py](virtualbox.py) | Controls VirtualBox analysis guests. |
| [vmware.py](vmware.py) | Controls VMware Workstation guests through vmrun. |
| [vmwarerest.py](vmwarerest.py) | Controls remote VMware guests through the REST API. |
| [vmwareserver.py](vmwareserver.py) | Manages remote VMware Workstation guests through vmrun. |
| [vsphere.py](vsphere.py) | Controls vSphere and ESXi guests through pyVmomi. |
| [xenserver.py](xenserver.py) | Manages XenServer guests through XenAPI. |
