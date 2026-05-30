Cloud Storage
Scalable, flexible storage solutions for your cloud infrastructure with
multiple options to meet diverse data management needs.

Block Storage
Scalable, high-performance block-level storage volumes that can be
attached to Vultr instances for expanded storage capacity and data
management.

Provisioning
A guide explaining how to set up and configure Vultr Block Storage
volumes for your virtual machines

How to Provision Vultr Block
Storage Volume
Introduction
Vultr Block Storage volume is a mountable HDD or NVMe disk volume you can
attach to Vultr Cloud Compute instances. These high-speed volumes offer raw
block-level storage to expand your application storage needs for databases,
images, audio, and video-based applications. To attach Vultr Block Storage
volume to Vultr Cloud Compute instance, both resources must be in the same
Vultr Location. Vultr Block Storage volumes support up to 10 TB of data
encrypted with Advanced Encryption Standard (AES-256).
Follow this guide to provision Vultr Block Storage volume using the Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Cloud Storage.
2. Click Block Storage and select Add Block Storage.
3. Select a HDD or NVMe storage type.
4. Choose a storage location depending on where you've provisioned the
Vultr Cloud Compute instances.
5. Move the slider to customize the storage size.
6. Enter a label and click Add Block Storage.
Vultr API
1. Send a GET request to the List Regions endpoint and note the ID of your
preferred region. For instance, ewr for the New Jersey region.

```bash
$ curl "https://api.vultr.com/v2/regions" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Create Block Storage endpoint to create a
Vultr Block Storage volume.
```bash
$ curl "https://api.vultr.com/v2/blocks" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "region" : "ewr",
        "size_gb" : 80,
        "label" : "Remote-Block-Storage",
        "block_type": "high_perf"
    }'
```
Visit the Create Block Storage endpoint to view additional attributes to
add to your request.
3. Send a GET  request to the List Block Storages endpoint to list all Vultr
Block Storage volumes.
```bash
$ curl "https://api.vultr.com/v2/blocks" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json"
```
Vultr CLI
1. List the available Vultr Block Storage volume regions and choose your
preferred region. For instance ewr  for the New Jersey region.

```bash
$ vultr-cli regions list
```
2. Create a new Vultr Block Storage volume.
```bash
$ vultr-cli block-storage create \
--block-type high_perf \
--region ewr \
--size 80 \
--label Remote-Block-Storage
```
3. List all Vultr Block Storage volumes.
```bash
$ vultr-cli block-storage list
```
Run vultr-cli block-storage create --help  to view all options.
Terraform
1. Ensure the Vultr Terraform provider is configured in your Terraform project.
2. Define the Block Storage volume resource.
```hcl
terraform {
required_providers {
vultr = {
source = "vultr/vultr"
version = "~> 2.23"
}
}
}

provider "vultr" {}
resource "vultr_block" "remote_block_storage" {
region = "ewr"
size_gb = 80
label = "Remote-Block-Storage"
block_type = "high_perf"
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Management
Centralized tools and features for administering your Vultr account,
resources, and infrastructure.

Monitor Block Storage
Learn how to monitor your Vultr Block Storage volumes performance and
usage metrics.

How to Monitor Vultr Block Storage
Volume
Introduction
Monitoring Vultr Block Storage volume lets you view the volume storage size,
Disk IO, monthly charges, attachment status, usage data, mount ID, location,
disk type, and more. Monitoring gives you usage insights so that you can
upgrade the storage size as your data grows.
Follow this guide to monitor a Vultr Block Storage volume using the Vultr
Console.
1. Navigate to Products and select Cloud Storage.
2. Click Block Storage. Then, select the target Vultr Block Storage volume.
3. Review the size, Disk IO, and attachment status under Overview.
4. Click Usage Data to view the disk usage information for the last 30 days.

Attach Instances
Learn how to connect and manage Block Storage volumes with your Vultr
instances for expanded storage capacity.

How to Manage Attachments for
Vultr Block Storage Volume
Introduction
Attaching a Vultr Block Storage volume to a Vultr Cloud Compute instance
allows the instance to discover the new storage device. You can then mount the
volume to the file system to expand storage. Ensure the Vultr Block Storage
volume and the Vultr Cloud Compute instance are in the same region before
attaching the volume. You can also remove the attachment if you no longer
wish to associate the volume with the instance.
Follow this guide to manage attachments for Vultr Block Storage volume using
the Vultr Console, Vultr API, and Vultr CLI.
Vultr Console
1. Navigate to Products and select Cloud Storage.
2. Click Block Storage. Then, select the target Vultr Block Storage volume.
3. Navigate to Attach to: and select the Cloud Compute instance.
4. Confirm that you want to attach the Block Storage volume.
5. Click Detach if you want to remove the Block Storage volume from the
Vultr Cloud Compute instance.
Vultr API
1. Send a GET request to the List Block Storages endpoint and note the
Vultr Block Storage volume ID .
```bash
$ curl "https://api.vultr.com/v2/blocks" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Cloud Compute Instances endpoint and note
the Vultr Cloud Compute instance ID .
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Attach Block Storage endpoint, specify a Vultr
Block Storage volume ID and a Vultr Cloud Compute instance ID. Then,
specify the "live" : true  option to attach the volume without restarting the
Vultr Cloud Compute instance.
```bash
$ curl "https://api.vultr.com/v2/blocks/block_storage_id/
attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "instance_id" : "cloud_compute_instance_id",
        "live" : true
    }'
```
4. Send a POST  request to the Detach Block Storage endpoint to detach the
Block Storage volume from the Vultr Cloud Compute instance.
```bash
$ curl "https://api.vultr.com/v2/blocks/block_storage_id/
detach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{

        "live" : true
    }'
```
Visit the Detach Block Storage endpoint to view additional attributes to
add to your request.
Vultr CLI
1. List all Vultr Block Storage volumes and note the ID of the target volume.
For instance, 6856bb78-e67b-416c-8fc1-2473c66fa016 .
```bash
$ vultr-cli block-storage list
```
2. List all Vultr Cloud Compute instances and note the instance ID. For
instance, 6cd130db-ae61-4995-8f44-7c57daa532fe .
```bash
$ vultr-cli instance list
```
3. Attach the volume to the instance by specifying the Vultr Block Storage
volume ID and Vultr Cloud Compute instance ID.
```bash
$ vultr-cli block-storage attach block_storage_id \
--instance instance_id
```
4. Detach a Vultr Block Storage volume from a Vultr Cloud Compute instance
by specifying the Vultr Block Storage volume ID.
```bash
$ vultr-cli block-storage detach block_storage_id
```
Run vultr-cli block-storage detach --help to view all options.
Terraform
1. Open your existing Terraform configuration for the volume (and instance).
2. Attach: add attached_to_instance to your vultr_block resource and apply.
```hcl
resource "vultr_block" "remote_block_storage" {
```
# ...existing fields (region, size_gb, label, block_type)
attached_to_instance = vultr_instance.server.id
}
3. Detach: remove the field from the resource and apply.
```hcl
resource "vultr_block" "remote_block_storage" {
```
# ...existing fields (region, size_gb, label, block_type)
# attached_to_instance removed to detach
}

Resize Block Storage
Learn how to increase the capacity of your Vultr Block Storage volume to
accommodate growing data needs.

How to Resize Vultr Block Storage
Volume
Introduction
Resizing a Vultr Block Storage volume allows you to scale up your storage needs
when your data grows. For instance, you can scale the storage size from 80 GB
to 160 GB to create more room for business assets like databases, images,
audio, and video. You can't shrink a Vultr Block Storage volume to a smaller size
unless you create a new instance and copy over the files.
Resizing a Block Storage volume involves two steps:
1. Resize the volume using the Vultr Console, API, CLI, or Terraform.
2. Expand the filesystem on the attached instance to use the new space.
Resize the Volume
Follow this guide to resize a Vultr Block Storage volume using the Vultr Console,
API, CLI or Terraform.
Vultr Console
1. Navigate to Products and select Cloud Storage.
2. Click Block Storage. Then, select the target Vultr Block Storage volume.
3. Click the current storage size. For instance, 80 GB .
4. Enter a new size in GB. For instance, 160 . Type YES to confirm and click
Continue.

Vultr API
1. Send a GET  request to the List Block Storages endpoint and note the
Vultr Block Storage volume ID.
```bash
$ curl "https://api.vultr.com/v2/blocks" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Block Storage endpoint, specify a
Vultr Block storage volume ID, and a new size in GB.
```bash
$ curl "https://api.vultr.com/v2/blocks/block_storage_id" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "size_gb": 160
    }'
```
Visit the Update Block Storage endpoint to view additional attributes to
add to your request.
Vultr CLI
1. List all Vultr Block Storage volumes and note the ID. For instance, 6856bb78-e67b-416c-8fc1-2473c66fa016 .
```bash
$ vultr-cli block-storage list
```
2. Specify a Vultr Block Storage volume ID and the new storage size in GB.
```bash
$ vultr-cli block-storage resize block_storage_id \
--size=160
```
Run vultr-cli block-storage resize --help to view all options.
Terraform
1. Open your Terraform configuration for the existing Block Storage resource.
2. Update the size_gb argument with the new volume size.
```hcl
resource "vultr_block" "remote_block_storage" {
label = "Remote-Block-Storage"
region = "ewr"
block_type = "high_perf"
size_gb = 160 # Updated size
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.
Expand the Filesystem
After resizing the volume, you must expand the filesystem on the attached
instance to use the additional space.
1. Connect to your instance via SSH.

2. Verify the block storage device path. For example, /dev/vdb .
```bash
$ lsblk
```
3. If the block storage uses a partition (for example, /dev/vdb1 ), expand the
partition using growpart .
```bash
$ sudo growpart /dev/vdb 1
```
4. Resize the filesystem based on the filesystem type.
- For ext4 filesystems:
```bash
$ sudo resize2fs /dev/vdb1
```
- For XFS filesystems:
```console
$ sudo xfs_growfs /mount/point
```
5. Verify the new size is available.
```bash
$ df -h

Delete Block Storage
A guide explaining how to permanently remove a Block Storage volume
from your Vultr account.
```

How to Delete Vultr Block Storage
Volume
Introduction
Deleting a Vultr Block Storage volume removes the volume from your account
and stops further charges. The operation also wipes any data in the volume.
Backup any important files before performing this operation because you can't
undo the change. You can migrate the files to a different Vultr Block Storage
volume or a Vultr Cloud Compute instance. Ensure you've not attached the
volume to any Vultr Cloud Compute instance before deleting.
Follow this guide to delete Vultr Block Storage volume using the Vultr Console,
API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Cloud Storage.
2. Click Block Storage.
3. Then, select the target Vultr Block Storage volume.
4. Click the delete icon to remove the Vultr Block Storage volume.
Vultr API
1. Send a GET request to the List Block Storages endpoint and note the
Vultr Block Storage volume ID.
```bash
$ curl "https://api.vultr.com/v2/blocks" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete Block Storage endpoint and specify
a Vultr Block Storage volume ID.
```bash
$ curl "https://api.vultr.com/v2/blocks/block-storage-id" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Visit the Delete Block Storage endpoint to view additional attributes to
add to your request.
Vultr CLI
1. List all Vultr Block Storage volumes and note the ID. For instance, 6856bb78-
.
e67b-416c-8fc1-2473c66fa016
```bash
$ vultr-cli block-storage list
```
2. Delete a Vultr Block Storage volume by specifying the ID.
```bash
$ vultr-cli block-storage delete block_storage_id
```
Run vultr-cli block-storage delete --help  to view all options.
Terraform
1. Open your Terraform configuration for the existing Block Storage resource.

2. Remove the vultr_block resource block, or destroy it by target.
```hcl
resource "vultr_block" "remote_block_storage" {
```
# ...existing fields (label, region, size_gb, block_type)
}
# To delete, either remove this block from configuration
# or run: terraform destroy -target
vultr_block.remote_block_storage
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 0 changed, 1 destroyed.

Shrink Block Storage
A guide explaining how to reduce the size of a Vultr Block Storage volume

How to Shrink Vultr Block Storage
Volume
Introduction
Vultr doesn't support direct shrinking of Block Storage volumes. To reduce
volume size, create a smaller volume, copy the necessary data from the
original, and delete the larger one.
Follow this guide to migrate your data to a smaller Vultr Block Storage volume.
Manual Migration
1. Inventory your files to determine the space needed.
- On Windows, you can use the File explorer, or use the fsutil tool.
```pwsh
> fsutil volume diskfree E:\
```
- On Linux and FreeBSD based instance, use the df command.
```bash
$ sudo df -h /mnt/blockstorage
```
2. Create a new Vultr Block Storage volume of the required size in the same
region as your instance.
3. Attach the new volume on your instance, then mount it.

4. Copy your files from the larger block storage volume to the new, smaller
volume. Use the tools appropriate for your platform.
- On Windows, use the robocopy tool.
```pwsh
> robocopy E:\ F:\ /E /XD "temp"
This command copies all the files from E:\  to F:\ , excluding the temp
folder. The /E option recursively copies the subfolders.
```
- On Linux, use the rsync tool.
```bash
$ sudo rsync -avc /mnt/blockstorage/ /mnt/
smallblockstorage/ --exclude "lost+found"
```
- On FreeBSD, use the rsync  tool. You may need to install it first.
```console
```
# pkg install -y rsync
# rsync -avc /mnt/blockstorage/ /mnt/smallblockstorage/
--exclude "lost+found"
5. Verify the migrated data in your new Vultr Block Storage volume.
- On Windows, compare the source and destination Vultr Block Storage
volume and list any files that are different, without actually
performing any copy operation.
```pwsh
> robocopy E:\ F:\ /L /E
The /L  option simulates the copy and reports what would be done. In
case of a successful data migration, the Mismatch  field shows 0 .
```

- On Linux and FreeBSD, use rsync with --dry-run  option.
```bash
$ sudo rsync -avc --dry-run /mnt/blockstorage/ /mnt/
smallblockstorage/ --exclude "lost+found"
If the data migration was successful, the command does not list any
individual file names between the header sending incremental file list
and the final summary.
```
6. Detach your old Vultr Block Storage volume.
7. When satisfied with the new volume, destroy your old Vultr Block Storage
volume.
Terraform
1. Shrinking an existing Block Storage volume is not supported. Use Terraform
to create a new, smaller volume, attach it, and later remove the original.
```hcl
terraform {
required_providers {
vultr = {
source = "vultr/vultr"
version = "~> 2.23"
}
}
}
provider "vultr" {}
```
# Existing instance
resource "vultr_instance" "server" {
region = "ewr"
plan = "vc2-1c-1gb"
os_id = 215
label = "app-server"
}

# New smaller volume
resource "vultr_block" "small_block" {
region = "ewr"
size_gb = 40
label = "Remote-Block-Storage-Small"
block_type = "high_perf"
attached_to_instance = vultr_instance.server.id
}
2. After you migrate and verify data, detach and delete the original larger
volume by removing its resource from configuration (or targeting destroy),
then apply.

Mount
A command that attaches a filesystem to a specific directory in the Linux
file hierarchy, making it accessible to the system.

FreeBSD
A Unix-like operating system known for its stability, security, and
advanced networking capabilities, derived from BSD Unix.

How to Mount Vultr Block Storage
Volume on FreeBSD
Introduction
Mounting Vultr Block Storage volume on FreeBSD provides flexible and scalable
file storage for Vultr Cloud Compute instances. FreeBSD supports NVMe and
VirtIO-based Vultr Block Storage volumes. VirtIO volumes appear as vtbd
devices and NVMe volumes appear as nda devices. This guide uses VirtIO
device names (vtbd ) in all examples. If your instance uses NVMe-based Block
Storage, replace all vtbd references with the corresponding nda device names
throughout the steps below.
Follow this guide to mount Vultr Block Storage volume on FreeBSD.
Warning
The following commands may destroy data on existing volumes. Use a new
Vultr Block Storage volume to avoid data loss due to file system changes and
partitioning.
1. Attach Vultr Block Storage volume to FreeBSD.
2. List all VirtIO Block Devices (vtbd ) attached to FreeBSD.
```bash
$ ls -al /dev/vtbd*
Output:
crw-r----- 1 root operator 0x58 Oct 29 14:17 /dev/vtbd0
crw-r----- 1 root operator 0x59 Oct 29 14:17 /dev/vtbd0p1

crw-r----- 1 root operator 0x5a Oct 29 14:17 /dev/vtbd0p2
crw-r----- 1 root operator 0x65 Oct 29 14:30 /dev/vtbd1
The Vultr Block Storage volume attaches as /vtbd1 based on the above
output. The first Vultr Block Storage volume attaches to FreeBSD as /dev/
vtbd1 and additional volume disk names increment in numeric order, such
as /dev/vtbd2 and /dev/vtbd3 .
```
3. View all active partitions and verify the root filesystem disk name.
```bash
$ gpart show
Output:
=> 40 52428720 vtbd0 GPT (25G)
40 1024 1 freebsd-boot (512K)
1064 52427696 2 freebsd-ufs (25G)
vtbd0 is the root filesystem disk with two active storage partitions based
on the above output.
```
4. Create a new GPT partition table for the vtbd1 Vultr Block Storage volume.
```bash
$ sudo gpart create -s GPT vtbd1
Output:
vtbd1 created
```
5. Create a new partition with the UFS2 partition and a label such as
vultr_block_storage .
```bash
$ sudo gpart add -t freebsd-ufs -l vultr_block_storage
vtbd1
Output:
vtbd1p1 added
```
6. Initialize the UFS2 filesystem on the new Vultr Block Storage volume
partition.
```bash
$ sudo newfs -U vtbd1p1
Output:
/dev/vtbd1p1: 40960.0MB (83886000 sectors) block size 32768, fragment size 4096
using 66 cylinder groups of 625.22MB, 20007 blks, 80128 inodes.
with soft updates
super-block backups (for fsck_ffs -b #) at:
192, 1280640, 2561088, 3841536, 5121984, 6402432, 7682880, 8963328, 10243776,
11524224,
12804672, 14085120, 15365568, 16646016, 17926464, 19206912, 20487360, 21767808,
23048256,
24328704, 25609152, 26889600, 28170048, 29450496, 30730944, 32011392, 33291840,
34572288,
35852736, 37133184, 38413632, 39694080, 40974528, 42254976, 43535424, 44815872,
46096320,
47376768, 48657216, 49937664, 51218112, 524985
```
7. Create a new mount point directory for the Vultr Block Storage volume
partition.
```bash
$ sudo mkdir /mnt/blockstorage
```
8. Mount the Vultr Block Storage volume partition.

```bash
$ sudo mount -t ufs /dev/vtbd1p1 /mnt/blockstorage
```
9. View all active partitions to verify the new partition is available.
```bash
$ sudo gpart show
Output:
=> 40 52428720 vtbd0 GPT (25G)
40 1024 1 freebsd-boot (512K)
1064 52427696 2 freebsd-ufs (25G)
=> 40 83886000 vtbd1 GPT (40G)
40 83886000 1 freebsd-ufs (40G)
The vtbd1 Vultr Block Storage volume partition is active on FreeBSD based
on the above output.
```
10. List the Vultr Block Storage volume partition information and note the
rawuuid value in the command output.
```bash
$ gpart list /dev/vtbd1
Output:
Geom name: vtbd1
modified: false
state: OK
fwheads: 16
fwsectors: 63
last: 83886039
first: 40
entries: 128

scheme: GPT
Providers:
```
1. Name: vtbd1p1
Mediasize: 42949632000 (40G)
Sectorsize: 512
Stripesize: 0
Stripeoffset: 20480
Mode: r1w1e1
efimedia: HD(1,GPT,e805ef8b-9618-11ef-bc70-315e9870b088,0x28,0x4ffffb0)
rawuuid: e805ef8b-9618-11ef-bc70-315e9870b088
rawtype: 516e7cb6-6ecf-11d6-8ff8-00022d09712b
label: vultr_block_storage
length: 42949632000
offset: 20480
type: freebsd-ufs
index: 1
end: 83886039
start: 40
..........
e805ef8b-9618-11ef-bc70-315e9870b088 is the Vultr Block Storage volume
partition UUID based on the above output. You can use the UUID value to
mount the Vultr Block Storage volume partition when FreeBSD restarts.
11. Add a new entry to /etc/fstab to automatically mount the Vultr Block
Storage volume partition at boot. Replace UUID-VALUE with the actual Vultr
Block Storage volume UUID.
```bash
$ echo "" | sudo tee -a /etc/fstab
$ echo "/dev/gptid/UUID-VALUE /mnt/blockstorage ufs rw 0 0"
sudo tee -a /etc/fstab
```
12. View the Vultr Block Storage volume usage.
```bash
$ df -h /mnt/blockstorage
Output:

Filesystem Size Used Avail Capacity Mounted on
/dev/vtbd1p1 39G 8.0K 36G 0% /mnt/blockstorage

Linux
A family of open-source operating systems based on the Linux kernel,
offering stability, security, and flexibility for various server environments.
```

How to Mount Vultr Block Storage
Volume on Linux
Introduction
Mounting Vultr Block Storage volume on Linux provides flexible and scalable file
storage for Vultr Cloud Compute instances. Linux distributions including Debian,
Ubuntu, CentOS, Rocky Linux, Alma Linux, Arch Linux, and Alpine Linux support
NVMe and HDD-based Vultr Block Storage volumes.
Follow this guide to mount a Vultr Block Storage volume on Linux.
Warning
The following commands may destroy data on existing volumes. Use a new
Vultr Block Storage volume to avoid data loss due to file system changes and
partitioning.
1. Attach a Vultr Block Storage volume to the Linux instance.
2. Use the lsblk utility to list all storage disks attached to the Vultr Cloud
Compute instance and verify the Vultr Block Storage volume disk name.
```bash
$ lsblk
Output:
NAME MAJ:MIN RM SIZE RO TYPE MOUNTPOINTS
sr0 11:0 1 1024M 0 rom
vda 254:0 0 25G 0 disk
├─vda1 254:1 0 512M 0 part /boot/efi
└─vda2 254:2 0 24.5G 0 part /
vdb 254:16 0 40G 0 disk

The Vultr Block Storage volume is attached to the instance as /vdb based
on the above output. The first Vultr Block storage volume attaches to Linux
as /dev/vdb and additional volume disk names increment in alphabetical
order such as /dev/vdc and /dev/vdd .
```
3. Create a new disk label using the parted utility.
```bash
$ sudo parted -s /dev/vdb mklabel gpt
```
4. Create a primary partition to fill the entire disk space.
```bash
$ sudo parted -s /dev/vdb unit mib mkpart primary 0% 100%
```
5. Create an EXT4 file system on the primary partition and format it.
```bash
$ sudo mkfs.ext4 /dev/vdb1
Output:
mke2fs 1.47.0 (5-Feb-2023)
Discarding disk blocks: done
Creating filesystem with 10485248 4k blocks and 2621440 inodes
Filesystem UUID: 95b1f596-e044-4dcd-beb3-a94877960e4d
Superblock backups stored on blocks:
32768, 98304, 163840, 229376, 294912, 819200, 884736, 1605632, 2654208,
4096000, 7962624
Allocating group tables: done
Writing inode tables: done
Creating journal (65536 blocks): done
Writing superblocks and filesystem accounting information: done
```
6. Create a new mount point directory for the Vultr Block Storage volume
partition.
```bash
$ sudo mkdir /mnt/blockstorage
```
7. View detailed information about the Vultr Block Storage volume partition
and note its UUID value.
```bash
$ sudo blkid /dev/vdb1
Output:
/dev/vdb1: UUID="95b1f596-e044-4dcd-beb3-a94877960e4d" BLOCK_SIZE="4096"
TYPE="ext4" PARTLABEL="primary" PARTUUID="a7eb098c-288d-4040-9aac-38b36d4e63e7"
```
8. Add a new entry to the /etc/fstab  file to automatically mount the Vultr
Block Storage volume at boot. Replace UUID-VALUE  with the actual Vultr
Block Storage volume partition UUID.
```bash
$ echo "UUID=<UUID-VALUE> /mnt/blockstorage ext4
defaults,noatime,nofail 0 0" sudo tee -a /etc/fstab
```
9. Reload systemd to apply the /etc/fstab changes.
```bash
$ sudo systemctl daemon-reload
```
10. Mount the Vultr Block Storage volume partition.
```bash
$ sudo mount /mnt/blockstorage
```
11. View all active storage volumes on the Vultr Cloud Compute instance and
verify that the new Vultr Block Storage volume is available.
```bash
$ lsblk
Output:
NAME MAJ:MIN RM SIZE RO TYPE MOUNTPOINTS
sr0 11:0 1 1024M 0 rom
vda 254:0 0 25G 0 disk
├─vda1 254:1 0 512M 0 part /boot/efi
└─vda2 254:2 0 24.5G 0 part /
vdb 254:16 0 40G 0 disk
└─vdb1 254:17 0 40G 0 part /mnt/blockstorage

Windows
A family of Microsoft operating systems that provides a graphical user
interface and supports various applications and services for personal and
business computing.
```

How to Mount Vultr Block Storage
Volume on Windows Server
Introduction
Mounting Vultr Block Storage volume on Windows provides flexible and scalable
file storage for Vultr Cloud Compute instances. Windows Server supports NVMe
and HDD-based Vultr Block Storage volumes.
Follow this guide to mount Vultr Block Storage volume on Windows Server.
Warning
The following commands may destroy data on existing volumes. Use a new
Vultr Block Storage volume to avoid data loss due to file system changes and
partitioning.
1. Attach Vultr Block Storage volume to Windows Server.
2. Open the Windows Server Manager application and click File and Storage
Services on the left navigation menu.

3. Click Disks.
4. Find the Vultr Block Storage volume and verify that its status is Offline.
5. Right-click the Vultr Block Storage volume and select Bring Online.

6. Click Yes when prompted to bring the disk online.
7. Right-click the disk again and select Initialize to set up Vultr Block Storage
volume as a GPT disk.
8. Click Yes when prompted to initialize the disk.
9. Right-click the Vultr Block Storage volume again and select New Volume.
10. Click Next in the New Volume Wizard.

11. Select the target Windows Server, verify the Vultr Block Storage volume
capacity, and click Next to set up the size.

12. Keep the default value in the Volume Size field or enter a new value to
set the Vultr Block Storage volume partition size.
13. Click Next to set up additional partition details.
14. Click the Drive letter drop-down to select a letter to assign the Vultr Block
Storage volume partition and click Next.
15. Select the partition file system, enter a custom name in the Volume label
field to identify the Vultr Block Storage volume partition, and click Next.

16. Verify the Vultr Block Storage volume settings and click Create to apply
changes.
17. Monitor the partitioning process, verify that all tasks are completed, and
click Close.

18. Click the Vultr Block Storage volume and verify that the new volume is
available in the Volumes section.
19. Open the Windows File Explorer and click This PC on the left navigation
menu to view all active storage volumes.
20. Verify that the Vultr Block Storage volume is available.

FAQ
Common questions and answers about Vultr's Block Storage service for
expanding server storage capacity.

69
011 Is Vultr Block Storage volume encrypted at rest? 70

Frequently Asked Questions (FAQs)
About Block Storage
Introduction
These are the frequently asked questions for Vultr Block Storage volume.
Can I upgrade or downgrade a Vultr Block
Storage volume?
You can upgrade Vultr Block Storage volume using the steps described here. You
must resize your file system manually, which does pose the risk of possible data
loss if performed incorrectly. You cannot perform an in-place downgrade of Vultr
Block Storage volume, but you can use these steps to migrate your files to a
smaller Vultr Block Storage volume.
Can I attach Vultr Block Storage volume to a
Vultr Cloud Compute instance in a different
Vultr location?
No, before attaching a Vultr Block Storage volume to a Vultr Cloud Compute
instance, ensure both resources are in the same Vultr location.

Is there a minimum size for Vultr Block
Storage volumes?
Yes, the minimum Vultr Block Storage volume size is 1 GB for an NVMe-based
volume and 40 GB for an HDD-based volume.
Can I take or restore snapshots with Vultr
Block Storage volumes?
No, Vultr automated server backup does not back up any attached Vultr Block
Storage volumes. Instead, you should back up your Vultr Block Storage volumes
using OS-level tools such as Rclone. Refer to the guide on How to Set Up
Automatic Backups with Rclone and Vultr Object Storage
Can I mount Vultr Block Storage volume to
multiple Vultr Cloud Compute instances at
the same time?
No, you can only attach a Vultr Block Storage volume to one Vultr Cloud
Compute instance at a time. However, you can move the Vultr Block Storage
volume between Vultr Cloud Compute instances in the same data location.
Note
If you need to move Vultr Block Storage volumes between different Vultr
Cloud Compute instances and preserve data, do not re-partition, create a new
filesystem, or perform any volume initialization steps.

Can I attach multiple Vultr Block Storage
volumes to the same Vultr Cloud Compute
instance?
Yes, you can attach up to 16 Vultr Block Storage volumes to the same Vultr
Cloud Compute instance.
Can I attach Vultr Block Storage volume to
Vultr Bare Metal server?
No, Vultr Block Storage volumes do not support Vultr Bare Metal Servers.
Are there any limits on the size or number
of Vultr Block Storage volumes I can deploy?
Vultr offers high limits on the total number of Vultr Block Storage volumes and
the aggregate storage per account. If you have questions about your account
limits, please open a support ticket.
Where is Vultr Block Storage volume data
physically located?
Vultr offers the flexibility of choosing a location when deploying a Vultr Block
Storage volume. The data remains in that location unless you copy it to a
different location. Data residency is important to customers, and therefore, Vultr
does not copy or back up your data outside that location.

Is Vultr Block Storage volume encrypted at
rest?
Vultr encrypts your data at rest with Advanced Encryption Standard, using 256-bit keys (AES-256). This level of encryption is approved by many regulatory
compliance standards such as PCI-DSS, GDPR, FedRAMP, FIPS 140-2, ISO/IEC
18033-3, and SOC 1, 2, and 3. AES is the only publicly accessible cipher
approved by the U.S. National Security Agency.

Storage Performance for
Vultr Block Storage
Comprehensive benchmarking analysis of Vultr Block Storage
performance, rate limits, tiers, and fio-based replication methodology.

Introduction
We've run extensive benchmarking of Vultr Block Storage. For additional
context on the performance metrics referenced throughout this document and
to better understand how storage performance is measured, benchmarked, and
compared, see What Are the Fundamentals of Storage Performance?. Vultr Block
Storage is designed for use with Vultr Cloud Compute instances and is offered in
two performance tiers: HDD Block and NVMe Block.
HDD Block is designed to be cost effective by relatively low performance. It’s
available at all Vultr sites. As the name suggests, it is largely composed of hard
disk drives, but it also has some flash storage that it uses to accelerate certain
types of metadata operations and caches. Your data is also spread redundantly
across a large number of such drives to increase performance, but it is still
fundamentally limited by the speed of hard disk drives.
NVMe Block is designed to be much higher performance, but as a consequence,
it costs more. It is available at a large number of Vultr sites, especially those
with GPU or high-performing CPU systems. As the name suggests, it is
composed of NVMe flash drives and so needs no further acceleration. It too is
redundant, but its mode of redundancy is chosen for speed, not lower cost.
Again, your data is spread across a large number of such drives to increase
performance, but the increased performance of NVMe drives makes it
significantly faster.
Rate Limits
Tiers of Vultr Block Storage are limited at the hypervisor to not allow a given
subscription to exceed certain IOPS and throughput levels for sustained periods.
These limits are imposed to avoid situations where one VM instance consumes
all the available network throughput or processing power for its storage
workload, limiting what would be available for competing workloads.
Block Storage rate limits also allow for short bursts of up to 60 seconds where
up to 150% of the sustained limit can be achieved. The burst capability requires

a period of time where lower than the sustained limits are requested in order to
make burst capacity available after being consumed.
| Tier | Sustained IOPS Limit | Sustained Throughput Limit |
| --- | --- | --- |
| HDD Block | 500 IOPS | 100 MB per second (95.3 MiB) |
| NVMe Block | 10,000 IOPS | 400 MB per second (381.4 MiB) |
It is important to understand how these limits interact with choice of block size.
For instance, 500 IOPS at 4 KB block size will result in only 2 MB/s. For example,
you will need a block size in excess of 209.7 KB to reach the 100 MB/s
throughput limit of HDD Block before hitting the 500 IOPS limit. That is to say
that 209.7 KB × 500 IOPS = 104.85 MB (≈100 MiB).
Benchmark Results
We used the utility fio  to measure performance for several block sizes, 4 KB,
64 KB, 512 KB, 1024 KB, and 4096 KB. We performed tests with 100% read
(both random and sequential), 100% write (again both random and sequential),
and a mixed workload of both reads and writes (50%/50%).
We performed these tests across a wide variety of VM instance plans so as to
see any break points where insufficient CPU or memory in the plan could impact
storage performance. We did not find such a break point with block
performance even on plans with only 1 core and 1 GB of RAM.
NVMe Block
This table shows the performance results for each of the three IO Types at each
of the tested block sizes. In each case we used a queue depth of 4, and a job
count of 4.
| IO Type | Block Size | Mean IOPS | Mean Throughput (MiB/s) | Mean Latency (ms) |
| --- | --- | --- | --- | --- |
| randwrite, randread, and randrw | 4 KB | ≈10,000 | ≈40 | 2.7 - 3.2 |
| randwrite, randread, and randrw | 64 KB | ≈6,000 | ≈381 | 4 - 5 |
| randwrite, randread, and randrw | 512 KB | ≈750 | ≈381 | 40 - 50 |
| randwrite, randread, and randrw | 1 MB | ≈380 | ≈381 | 80 - 100 |
| randwrite, randread, and randrw | 4 MB | ≈95 | ≈381 | 320 - 420 |
It is important to note that this table lists mean throughput in MiB/s whereas the
rate limits are in MB/s. For example, 381.4 MiB/s is 400 MB/s which is the
throughput rate limit for NVMe Block storage.
At the 4 KB block size, the individual IOs are so small that the limitation to
throughput is the number of IOPS reaching the IOPS rate limit. For larger block
sizes, the throughput rate limits are instead hit and that keeps the number of
IOPS lower than the IOPS rate limit.
Latency rises as block size increases because we’ve hit the throughput rate
limit. Rate limiting operates by not answering requests until doing so would
keep the throughput below its rate limit, effectively injecting latency.
HDD Block
For HDD Block, results are similar in that either the IOPS rate limit or the
throughput rate limits are hit. The primary difference is that the rate limits for
HDD Block are lower.
Overall Conclusion
The overall conclusion is that both HDD Block and NVMe Block can achieve their
rate limited speeds of 500 IOPS and 100 MB/s for HDD and 10,000 IOPS
and 400 MB/s for NVMe, even on the smallest instance plans.

Replicating These Results
You can replicate these results for yourself by using fio at any of the blocksizes
mentioned at any operations mix you would like.
1. Install the fio utility and any dependencies. It can be found on
git.kernel.org, but your distribution likely has it available as a package. In
most distributions the package is simply called fio . You should also install
libaio so that it is available to fio . The package is usually called either
libaio_dev or libaio_devel , depending on your distribution.
2. When running fio , you will need to create a job configuration file that you
can reference and then run a command line that points at the job file.
```ini
[FIOJOB]
filename=/mnt/vbs/fio.raw
size=500G
random_generator=lfsr
buffered=0
direct=1
invalidate=0
ioengine=libaio
rw=randwrite
bs=4k
iodepth=4
numjobs=16
runtime=900
loops=1
time_based=1
Key values to change to match the workload you are testing are:
```
- filename= This should be a file on the file system where you are
testing. If you are testing directly on the block device itself,
understand that the test is destructive to any data contained in the
file and will destroy any file system on the raw device.

- direct= 1 enables O_DIRECT , 0 disables it. Use direct=1 with
ioengine=libaio .
- ioengine= We recommend libaio for best results, but you may wish to
compare it with sync or psync . We used libaio in our testing.
- rw= randread , randwrite , and randrw are the most useful options.
- bs= Block size. We used 4k, 64k, 512k, 1M, and 4M in our testing.
- iodepth= The queue depth per job. We used 4 in our testing.
- numjobs= The number of simultaneous jobs to run. We used 4 in our
testing.
3. Then you can reference the job config from the command line:
```bash
$ fio \
--eta=never \
--status-interval=5000ms \
--output-format=json+ \
$FIOJOBFILE
Where $FIOJOBFILE is the path to the job file created above. See the fio
documentation for more details.
Tuning Tips for Best Performance with Vultr
Block Storage
• Enable higher levels of parallelism by making more simultaneous requests.
Increase the number of processes, threads, or workers issuing I/O
operations. In the fio benchmarking utility, parallelism can be increased
by increasing numjobs and iodepth (the number of requests each job allows
to be in flight without a response).
• Larger queue depths allow more requests to remain in flight while waiting
for responses, preventing high latency from artificially reducing
throughput.

• In many cases, asynchronous I/O can increase performance. Some
applications can leverage libaio  via a configurable option. In fio , enable
asynchronous I/O with ioengine=libaio .
• In most cases, caches should be disabled to use Direct I/O. In fio , this is
achieved with direct=1 and buffered=0 .

Block Storage Snapshot
Understand Vultr block storage snapshots for backups, cloning, and
efficient volume management.
```

Create
Create Vultr Block Storage snapshots via API for cloning and backup
workflows efficiently.

How to Create a Block Storage
Snapshot
Introduction
A Block Storage Snapshot captures the state of a block storage volume at a
point in time. Snapshots are independent objects retained until explicitly
deleted. Use a snapshot as the source image to clone a Bootable Block Storage
volume for VX1™ instance provisioning.
Follow this guide to create a Block Storage Snapshot using the Vultr API.
1. Send a GET  request to the List Block Storages endpoint and note the id
of the Bootable Block Storage volume to snapshot.
```bash
$ curl "https://api.vultr.com/v2/blocks" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Create Block Storage Snapshot endpoint to
create a snapshot. Replace BLOCK-ID  with the volume ID from the previous
step, and SNAPSHOT-DESCRIPTION  with a description for the snapshot.
```bash
$ curl "https://api.vultr.com/v2/blocks/snapshots" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "block_id": "BLOCK-ID",
        "description": "SNAPSHOT-DESCRIPTION"
    }'
```
Note the id from the response. The snapshot is ready to use when the
state field shows COMPLETE .

Delete
Delete Vultr block storage snapshots via API without affecting existing
cloned volumes.

Introduction
Deleting a Block Storage Snapshot removes it permanently from the account.
Block storage volumes already cloned from the snapshot are independent and
are not affected by its deletion.
Follow this guide to delete a Block Storage Snapshot using the Vultr API.
1. Send a GET  request to the List Block Storage Snapshots endpoint and
note the id of the snapshot to delete.
```bash
$ curl "https://api.vultr.com/v2/blocks/snapshots" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete Block Storage Snapshot endpoint
to delete the snapshot. Replace SNAPSHOT-ID  with the snapshot ID.
```bash
$ curl "https://api.vultr.com/v2/blocks/snapshots/{snapshot-id}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
A successful request returns a 204 No Content  response.
```

Clone Volume
Clone a bootable block storage volume via snapshot and deploy a VX1
instance.

Introduction
Cloning a Bootable Block Storage volume creates an independent copy from a
Block Storage Snapshot. Each clone is a standalone high_perf Block Storage
volume, marked bootable, and usable as the boot device for a new VX1™
instance. This removes the need to manually replicate a boot environment
across multiple deployments.
Follow this guide to snapshot an existing Bootable Block Storage volume, create
a cloned Bootable Block Storage volume from that snapshot, and provision a
VX1™ instance using the clone.
Note
Bootable Block Storage volume cloning is available in regions that support
high_perf NVMe block storage.
Vultr API
A Block Storage Snapshot of the source Block Storage volume serves as the
image for cloning. Create a Block Storage Snapshot of the Bootable Block
Storage volume you want to clone, then confirm the snapshot is ready before
proceeding.
1. Send a GET request to the List Block Storage Snapshots endpoint and
note the id of the snapshot. Confirm that state shows COMPLETE before
proceeding.
```bash
$ curl "https://api.vultr.com/v2/blocks/snapshots" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST request to the Create Block Storage endpoint to create a
cloned Bootable Block Storage volume. Each clone is a new high_perf Block

Storage volume created from the snapshot. The size must be equal to or
greater than the snapshot size. Replace REGION  with the region ID (for
example, ewr ), SIZE-GB  with the volume size in GB, CLONE-LABEL  with a label,
and SNAPSHOT-ID with the snapshot ID.
```bash
$ curl "https://api.vultr.com/v2/blocks" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "region": "REGION",
        "size_gb": SIZE-GB,
        "label": "CLONE-LABEL",
        "block_type": "high_perf",
        "snapshot_id": "SNAPSHOT-ID",
        "bootable": true
    }'
```
Note the  id  from the response. The os_id  for a Block Storage volume
cloned from a Block Storage Snapshot is always 164  — this is the Snapshot
OS type that Vultr assigns to snapshot-cloned Block Storage volumes. You
must pass "os_id": 164  when provisioning the instance, as the API requires
the instance OS identifier to exactly match the Block Storage volume's OS
identifier.
3. Send a GET  request to the Get Block Storage endpoint to confirm the
clone status. Replace BLOCK-ID  with the ID from the previous step.
```bash
$ curl "https://api.vultr.com/v2/blocks/{block-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
Verify that status  is active  and block_type  is high_perf  before provisioning
an instance.
```
4. Send a POST  request to the Create Instance endpoint to provision a VX1™
instance. For more information on VX1™ provisioning, see Provisioning

VX1™ Cloud Compute Instances. Replace REGION  with the same region as
the clone, VX1-PLAN  with the VX1™ plan ID (for example, vx1-g-2c-8g ),
INSTANCE-LABEL  with a label, INSTANCE-HOSTNAME  with a hostname, and BLOCK-ID
with the clone ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "region": "REGION",
        "plan": "VX1-PLAN",
        "label": "INSTANCE-LABEL",
        "hostname": "INSTANCE-HOSTNAME",
        "os_id": 164,
        "block_devices": [
            {
                "block_id": "BLOCK-ID",
                "bootable": true
            }
        ]
    }'
```
5. Send a GET  request to the Get Instance endpoint to confirm the instance
status. Replace INSTANCE-ID  with the ID from the previous step.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
Verify that status  shows active  and power_status  shows running .
```

Terraform
Block Storage Snapshot operations are not currently supported by the Vultr
Terraform provider. Create a Block Storage Snapshot using the Vultr API, then
note the snapshot ID before continuing.
1. Define a vultr_block_storage  resource using the snapshot ID. Replace REGION ,
, CLONE-LABEL , and SNAPSHOT-ID  with your values. The size_gb  must be
SIZE-GB
equal to or greater than the snapshot size.
```hcl
resource "vultr_block_storage" "clone" {
region = "REGION"
size_gb = SIZE-GB
label = "CLONE-LABEL"
block_type = "high_perf"
snapshot_id = "SNAPSHOT-ID"
bootable = true
}
```
2. After applying, retrieve the cloned Block Storage volume ID and os_id  from
the Terraform state:
```bash
$ terraform state show vultr_block_storage.clone
```
Note the id  before provisioning the VX1™ instance.
3. Provision a VX1™ instance using the cloned Block Storage volume as the
boot device. See Provisioning VX1™ Cloud Compute Instances for
instructions. Use os_id  and vultr_block_storage.clone.id  as the boot
164
device Block Storage volume ID.

Object Storage
Secure, scalable cloud storage solution for storing and retrieving any
amount of data from anywhere on the web with S3 compatibility.

Provisioning
A guide explaining how to set up and activate a Vultr Object Storage
subscription for cloud-based data storage.

How to Provision a Vultr Object
Storage Subscription
Introduction
Vultr Object Storage is an S3-compatible solution that lets you store and serve
large amounts of data as objects. It provides scalable, durable, and secure
storage for a variety of data types, such as documents, images, videos, and
backups. It's ideal for big data storage, data backups, and content distribution
using a secure S3-compatible endpoint.
Follow this guide to provision a Vultr Object Storage Subscription using the Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Cloud Storage.
2. Select Object Storage from the list of options.
3. Click Create Object Storage
4. Select a Vultr Object Storage tier from the following options:
- Accelerated: High-performance NVMe storage optimized for write-intensive workloads. Supports up to 10,000 IOPS and 5 Gbps
throughput.
- Performance: Low-latency NVMe storage designed for datacenter
workloads. Supports up to 4,000 IOPS and 1 Gbps throughput.
- Premium: Reliable and durable storage for general-purpose
applications. Stored on HDD, indexed on SSD, with up to 1,000 IOPS
and 800 Mbps throughput.

- Standard: Cost-effective, high-availability bulk storage. Stored on
HDD, indexed on SSD, with up to 800 IOPS and 600 Mbps throughput.
- Archive: Low-cost storage for infrequently accessed data. Objects
transition to the VULTR_ARCHIVE storage class via a lifecycle policy.
Includes 1000 GB of archived storage, 100 GB of unarchived storage,
and 1 TB of bandwidth at $6/month. Archived data beyond the
included capacity is billed at $0.006 per GB-month.
5. Enter a descriptive name in the Name field.
6. Select your desired Vultr location.
7. Click Create Object Storage to provision the Vultr Object Storage
subscription.
Vultr API
1. Send a GET request to the Get All Clusters endpoint and note your target
cluster ID depending on the Vultr region.
```bash
$ curl "https://api.vultr.com/v2/object-storage/clusters" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET request to the Get All Tiers endpoint to view all available Vultr
Object Storage tiers and note your target tier ID.
```bash
$ curl "https://api.vultr.com/v2/object-storage/tiers" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST request to the Create Object Storage endpoint to provision
a Vultr Object Storage subscription with your target tier and region.

Replace CLUSTER_ID  with the cluster ID from the previous step, TIER_ID  with
your target tier ID, and LABEL  with a descriptive name for the subscription.
```bash
$ curl "https://api.vultr.com/v2/object-storage" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "label": "LABEL",
        "cluster_id": CLUSTER_ID,
        "tier_id": TIER_ID
    }'
```
Visit the Create Object Storage endpoint to view additional attributes to
apply to your Vultr Object Storage subscription request.
4. Send a GET  request to the List Object Storages endpoint to view all
available Vultr Object Storage subscriptions in your account.
```bash
$ curl "https://api.vultr.com/v2/object-storage" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json"
```
Vultr CLI
1. List all available Vultr Object Storage clusters and note your target cluster
ID depending on the Vultr region.
```bash
$ vultr-cli object-storage list-clusters
```
2. Provision a Vultr Object Storage subscription. Replace CLUSTER_ID  with your
target cluster ID and LABEL  with a descriptive name.

```bash
$ vultr-cli object-storage create --cluster-id CLUSTER_ID --
label LABEL
```
3. List all Vultr Object Storage subscriptions in your account.
```bash
$ vultr-cli object-storage list
```
Run vultr-cli object-storage create --help  to view all available options to
apply to your Vultr Object Storage subscription request.
Terraform
1. Ensure the Vultr Terraform provider is configured in your Terraform project.
2. Define the Object Storage subscription resource.
```hcl
terraform {
required_providers {
vultr = {
source = "vultr/vultr"
version = "~> 2.23"
}
}
}
provider "vultr" {}
resource "vultr_object_storage" "object_storage" {
cluster_id = 4  # Object Storage cluster (region).
tier_id = 1  # Performance tier ID.
label = "Object-Storage"
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

S3 Compatibility Matrix
A reference guide outlining the supported Amazon S3 API operations and
features available in Vultr Object Storage.

S3 Compatibility Matrix
Introduction
Vultr Object Storage is designed to be compatible with the S3 protocol.
However, specific features and capabilities may vary depending on the S3 tool
used to access Object Storage.
Feature Compatibility List
Below is a detailed list of supported and unsupported features for Vultr Object
Storage.
• Bucket ACLs (Get, Put): Yes
• Bucket Access Logging: No
• Bucket Inventory: No
• Bucket Lifecycle: Yes
• Bucket Location: Yes
• Bucket Notification: No
• Bucket Object Versions: Yes
• Bucket Replication: No
• Bucket Request Payment: Yes
• Bucket Website: No
• CORS: Yes
• Copy Object: Yes
• Create Bucket: Yes
• Delete Bucket: Yes
• Delete Object: Yes
• Get Bucket Info (HEAD): Yes
• Get Object: Yes
• Get Object Info (HEAD): Yes
• List Buckets: Yes
• Multipart Uploads: Yes

• Object ACLs (Get, Put): Yes
• Object Metadata: Yes
• Object Tagging: Yes
• POST Object: Yes
• Policy (Buckets, Objects): Yes
• Pre-Signed URLs: Yes
• Put Object: Yes
Important Notes
Please review the following key points regarding feature compatibility and
potential issues when using Vultr Object Storage
• Feature Compatibility: Refer to the list above for details on supported
features and functionality. Ensure the S3 tool you are using is compatible
with the required features for your workflow.
• Content-Length Header Discrepancy: For download requests, the
Content-Length header might not match the actual file size. This occurs
because files are gzip-compressed to enhance performance. If this
discrepancy impacts your automation systems, you can disable gzip
compression on requests to ensure the Content-Length matches the file
size.
More Resources
• Provision Vultr Object Storage
• Manage Vultr Object Storage Subscription
• Frequently Asked Questions for Vultr Object Storage Subscription

Management
Centralized tools and settings for administering your Vultr account,
resources, and infrastructure.

Manage Buckets
Learn how to create, view, and manage storage buckets for your Vultr
Object Storage subscription.

How to Manage Buckets for Vultr
Object Storage Subscription
Introduction
Buckets for Vultr Object Storage subscriptions are containers for storing objects
using the simple storage service (S3) protocol. You can create folders and
upload files into buckets when storing business assets such as images, videos,
audio, and application files.
Follow this guide to manage buckets for Vultr Object Storage subscription using
the Vultr Console.
1. Navigate to Products and select Cloud Storage.
2. Click Object Storage and select the target Vultr Object Storage
subscription.
3. Navigate to Buckets and click Create Bucket.
4. Enter the bucket name and follow the naming conventions.
5. Turn Bucket Versioning ON or OFF depending on your application use
case.
6. Turn the object lock ON or OFF and click Create Bucket.
7. Click Add Folder to link a new folder to the bucket.
8. Click the delete icon to delete the bucket from the Vultr Object Storage
subscription.

Monitor
A guide explaining how to track and analyze usage metrics for your Vultr
Object Storage subscription

How to Monitor Vultr Object
Storage Subscription
Introduction
Monitoring a Vultr Object Storage subscription allows you to view the storage
usage, bandwidth usage, and current charges. Monitoring detects service
disruptions, tracks storage cost-effectiveness, and creates alerts for scalability
issues.
Follow this guide to monitor Vultr Object Storage subscription using the Vultr
Console.
1. Navigate to Products and select Cloud Storage.
2. Click Object Storage.
3. Then, select the target Vultr Object Storage subscription.
4. Review the inbound and outbound data by clicking Usage Data.

Delete
Learn how to permanently delete your Vultr Object Storage subscription
when its no longer needed.

How to Delete Vultr Object Storage
Subscription
Introduction
Deleting Vultr Object Storage subscription removes the S3-compatible store
from your account and stops further charges. You should only delete the
subscription after backing up any important business assets to a different
storage. The process is irreversible, and you can't undo it, so you should take
great care.
Follow this guide to delete Vultr Object Storage subscription using the Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Cloud Storage.
2. Click Object Storage.
3. Then, select the target Vultr Object Storage subscription and click the
delete icon.
Vultr API
1. Send a GET request to List Object Storages endpoint and note the Vultr
Object Storage subscription ID.
```bash
$ curl "https://api.vultr.com/v2/object-storage" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json"
```
2. Send a DELETE  request to the Delete Object Storage endpoint and
specify a Vultr Object Storage subscription ID.
```bash
$ curl "https://api.vultr.com/v2/object-storage/
object_storage_id" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Visit the Delete Object Storage endpoint to view additional attributes to
add to your request.
Vultr CLI
1. List all Vultr Object Storage subscriptions and note the ID. For instance,
6856bb78-e67b-416c-8fc1-2473c66fa016 .
```bash
$ vultr-cli object-storage list
```
2. Delete a Vultr Object Storage subscription by specifying the ID.
```bash
$ vultr-cli object-storage delete object_storage_id
```
Run vultr-cli object-storage delete --help  to view all options.
Terraform
1. Open your Terraform configuration where the Object Storage subscription
is defined.
2. Remove the vultr_object_storage  resource block, or destroy it by target.

```hcl
resource "vultr_object_storage" "object_storage" {
```
# ...existing fields (cluster_id, tier_id, label)
}
# To delete, either remove this block from configuration
# or run: terraform destroy -target
vultr_object_storage.object_storage
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 0 changed, 1 destroyed.

Manage Credentials
Learn how to view and regenerate access credentials for your Vultr Object
Storage S3-compatible buckets.

How to Manage S3 Credentials for
Vultr Object Storage Subscription
Introduction
Managing S3 Credentials for Vultr Object Storage subscription allows viewing
and regenerating access credentials for S3-compatible storage buckets. These
credentials include the hostname, secret key, and access key. Your apps use
these credentials to authenticate to the Vultr Object Storage subscription
programmatically. You can also use these credentials to access a Vultr Object
Storage subscription using any S3-compatible command-line tool like S3cmd.
Follow this guide to manage S3 Credentials for Vultr Object Storage subscription
using the Vultr Console, API, and CLI.
Vultr Console
1. Navigate to Products and select Cloud Storage.
2. Click Object Storage and select the target Vultr Object Storage
subscription.
3. Select Overview, and navigate to S3 Credentials.
4. Click Regenerate Keys if you need a new copy of the S3 credentials.
Vultr API
1. Send a GET request to List Object Storages endpoint and note the
s3_hostname , s3_access_key , and s3_secret_key for your target Vultr Object
Storage subscription.
```bash
$ curl "https://api.vultr.com/v2/object-storage" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json"
```
2. Send a POST  request to the Regenerate Object Storage Keys endpoint
endpoint and specify a Vultr Object Storage subscription ID if you need to
regenerate the keys.
```bash
$ curl "https://api.vultr.com/v2/object-storage/
object_storage_id/regenerate-keys" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Visit the Regenerate Object Storage Keys endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all Vultr Object Storage subscriptions and note the S3 HOSTNAME ,
, and the S3 SECRET KEY for your target subscription.
S3 ACCESS KEY
```bash
$ vultr-cli object-storage list
```
2. Regenerate the keys by specifying a Vultr object storage subscription ID if
you need a fresh copy of the credentials.
```bash
$ vultr-cli object-storage regenerate-keys object_storage_id
```
Run vultr-cli object-storage regenerate-keys --help  to view all options.

Archival Storage
Vultr archival storage provides cost-effective long-term data storage with
lifecycle policies and flexible object transitions.

Enable Archival Storage
Enable archival storage on Vultr Object Storage with lifecycle policies and
cost-efficient data tiering.

How to Enable Archival Storage on
a Standard Object Storage
Subscription
Introduction
Standard Object Storage subscriptions support an optional Archive add-on that
moves objects from selected buckets into the VULTR_ARCHIVE storage class via a
lifecycle policy. Unlike the dedicated Archive subscription, this option allows
choosing which buckets participate in archival and customizing the lifecycle
policy to control which objects transition. Archived data is billed at $0.006 per
GB-month on top of the Standard subscription cost.
Follow this guide to enable Archival Storage on a Standard Object Storage
bucket using the Vultr Console or the Vultr API.
Note
The target bucket name must be between 3 and 53 characters long. Archival
Storage cannot be enabled on a bucket that has versioning enabled, or that
previously had versioning enabled.
Vultr Console
1. Navigate to Products and click Cloud Storage.
2. Select Object Storage and click the target Standard subscription.
3. Click Buckets.
4. Click the wrench icon next to the target bucket.
5. Under Options, toggle Archival Storage to enabled.

The Archival Storage Policy editor appears with a default lifecycle policy
pre-filled. To customize the policy, see How to Manage Lifecycle Policies for
Archival Storage.
6. Click Save Changes.
Vultr API
1. Send a GET  request to the List Object Storages endpoint to retrieve your
Standard subscription ID.
```bash
$ curl "https://api.vultr.com/v2/object-storage" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Note the  id  of your Standard subscription (tier_id: 2 ). Use this value as
{object-storage-id}  in the next step.
2. Enable Archival Storage on the target bucket. Replace {object-storage-id}
with your subscription ID and {bucket-name}  with the name of the bucket.
```bash
$ curl "https://api.vultr.com/v2/object-storage/{object-storage-id}/bucket/{bucket-name}/archival" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
-d '{"archival": true}'
The default lifecycle policy is applied to the bucket. To customize it, see
How to Manage Lifecycle Policies for Archival Storage.

Disable Archival Storage
Disable archival storage on Vultr Object Storage and restore archived
data back to standard tier.
```

How to Disable Archival Storage on
a Standard Object Storage
Subscription
Introduction
Disabling Archival Storage removes the lifecycle policy and triggers a
background job that moves all archived objects back to the Standard bucket.
This process runs in the background and may take time depending on the
volume of data.
Follow this guide to disable Archival Storage on a Standard Object Storage
bucket using the Vultr Console or the Vultr API.
Vultr Console
1. Navigate to Products and click Cloud Storage.
2. Select Object Storage and click the target Standard subscription.
3. Click Buckets.
4. Click the wrench icon next to the target bucket.
5. Under Options, toggle Archival Storage to disabled.
6. Click Save Changes.
Vultr API
1. Send a GET request to the List Object Storages endpoint to retrieve your
Standard subscription ID.
```bash
$ curl "https://api.vultr.com/v2/object-storage" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Note the   of your Standard subscription (tier_id: 2 ). Use this value as
id
{object-storage-id}  in the next step.
2. Disable Archival Storage on the target bucket. Replace {object-storage-id}
with your subscription ID and {bucket-name}  with the name of the bucket.
```bash
$ curl "https://api.vultr.com/v2/object-storage/{object-storage-id}/bucket/{bucket-name}/archival" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
-d '{"archival": false}'

Lifecycle Policies
Manage lifecycle policies for Vultr archival storage to control object
transitions and optimize storage costs.
```

How to Manage Lifecycle Policies
for Archival Storage
Introduction
A lifecycle policy defines which objects in a bucket transition to the VULTR_ARCHIVE
storage class and when. Policies run at 00:00 UTC each day. Setting the
transition delay to 0 days queues objects for transition in the next nightly run.
The Filter element in a lifecycle policy supports the following criteria:
• Prefix : matches objects under a specified path
• ObjectSizeGreaterThan : matches objects larger than the specified size in
bytes
• ObjectSizeLessThan : matches objects smaller than the specified size in bytes
Combine multiple criteria by wrapping them inside an And element.
Note
• Lifecycle policies on Archive subscriptions (tier_id 6) are locked to the
default and cannot be modified via the API, Console, or S3-compatible
tools.
• Bucket names must be between 3 and 53 characters to be eligible for
Archival Storage. Applying a lifecycle policy to a bucket with a name
longer than 53 characters returns an error.
• Buckets with versioning enabled — or that previously had versioning
enabled — are not eligible for Archival Storage.
Follow this guide to view, set, and suspend lifecycle policies on Standard Object
Storage buckets with Archival Storage enabled.

XML policy examples
Move all objects to archive immediately:
XML
<LifecycleConfiguration>
<Rule>
<ID>MoveAllToArchive</ID>
<Filter>
<Prefix></Prefix>
</Filter>
<Status>Enabled</Status>
<Transition>
<Days>0</Days>
<StorageClass>VULTR_ARCHIVE</StorageClass>
</Transition>
</Rule>
</LifecycleConfiguration>
Move a subset of objects to archive after 4 days:
This example moves objects under the cold-data/ prefix that are larger than 1
GB. Adjust the Prefix , ObjectSizeGreaterThan , and Days values to match your
requirements.
XML
<LifecycleConfiguration>
<Rule>
<ID>MoveSubsetToArchive</ID>
<Filter>
<And>
<Prefix>cold-data/</Prefix>
<ObjectSizeGreaterThan>1000000000</
ObjectSizeGreaterThan>
</And>
</Filter>
<Status>Enabled</Status>
<Transition>
<Days>4</Days>
<StorageClass>VULTR_ARCHIVE</StorageClass>
</Transition>

</Rule>
</LifecycleConfiguration>
To pause archival without removing the policy, set the rule's Status to Suspended
in the XML before reapplying.
Vultr Console
• To retrieve the current lifecycle policy:
1. Navigate to Products and click Cloud Storage.
2. Select Object Storage and click the target Standard subscription.
3. Click Buckets.
4. Click the wrench icon next to the target bucket.
The Archival Storage Policy editor displays the current policy XML.
• To set or update the lifecycle policy:
1. Navigate to Products and click Cloud Storage.
2. Select Object Storage and click the target Standard subscription.
3. Click Buckets.
4. Click the wrench icon next to the target bucket.
5. In the Archival Storage Policy editor, paste the updated policy XML.
6. Click Save Changes.
• To pause archival:
1. Navigate to Products and click Cloud Storage.
2. Select Object Storage and click the target Standard subscription.
3. Click Buckets.
4. Click the wrench icon next to the target bucket.
5. In the Archival Storage Policy editor, update the <Status> element
to Suspended .
6. Click Save Changes.

Vultr API
Note
Replace {object-storage-id} with your subscription ID and {bucket-name} with
the bucket name in all commands below.
• To retrieve the current lifecycle policy:
```bash
$ curl "https://api.vultr.com/v2/object-storage/{object-storage-id}/bucket/{bucket-name}/lifecycle" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
Verify that the response contains a rule with StorageClass: VULTR_ARCHIVE . If
no policy is set, the endpoint returns an error.
• To set a lifecycle policy (move all objects):
```
```console
$ curl "https://api.vultr.com/v2/object-storage/{object-storage-id}/bucket/{bucket-name}/lifecycle" \
```
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
-d '{
"archive_rules": [
{
"ID": "MoveAllToArchive",
"Status": "Enabled",
"Filter": [],
"Transitions": [
{
"Days": 0,
"StorageClass": "VULTR_ARCHIVE"
}
]
}

]
}'
To move a subset of objects, use the XML policy examples above with
s3cmd. See the S3cmd tab for instructions.
• To pause archival, set the Status field to Suspended in the request body:
```console
$ curl "https://api.vultr.com/v2/object-storage/{object-storage-id}/bucket/{bucket-name}/lifecycle" \
```
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
-d '{
"archive_rules": [
{
"ID": "MoveAllToArchive",
"Status": "Suspended",
"Filter": [],
"Transitions": [
{
"Days": 0,
"StorageClass": "VULTR_ARCHIVE"
}
]
}
]
}'
S3cmd
Note
Replace S3_CONFIG with the path to your s3cmd configuration file and
BUCKET_NAME with the bucket name in all commands below.
• To retrieve the current lifecycle policy:
```bash
$ s3cmd -c S3_CONFIG getlifecycle s3://BUCKET_NAME/
• To set a lifecycle policy, save one of the XML policy examples above as
lifecycle.xml , then apply it to the bucket:
```
```console
$ s3cmd -c S3_CONFIG setlifecycle lifecycle.xml s3://
BUCKET_NAME/
• To pause archival, update lifecycle.xml  to set <Status>Suspended</Status> ,
then reapply:
```
```console
$ s3cmd -c S3_CONFIG setlifecycle lifecycle.xml s3://
BUCKET_NAME/
```

Restore Objects
Restore archived objects in Vultr using s3cmd with direct download or
restore requests for large files.

How to Restore Archived Objects
from Vultr Archival Storage
Introduction
Archived objects appear with a size of 0 bytes in the bucket. Small objects can
be retrieved directly by downloading them. Larger objects require an explicit
restore request before they can be downloaded. The default restore window is 7
days.
Follow this guide to restore archived objects using s3cmd.
Note
Replace S3_CONFIG with your s3cmd config file path, BUCKET_NAME with the
bucket name, and OBJECT_KEY with the object's path in all commands below.
Restore a small object
For small objects, a standard download triggers retrieval from archive.
```bash
$ s3cmd -c S3_CONFIG get s3://BUCKET_NAME/OBJECT_KEY
Restore a large object
For larger objects, issue an explicit restore request before downloading. Replace
DAYS with the number of days to keep the object available.
```
```console
```

$ s3cmd -c S3_CONFIG --restore-days=DAYS restore s3://
BUCKET_NAME/OBJECT_KEY
If the object is still being retrieved from archive, the following error appears.
Wait a few minutes and retry.
ERROR: S3 error: 400 (RequestTimeout): restore is still in progress
Once the restore completes, download the object:
```console
$ s3cmd -c S3_CONFIG get s3://BUCKET_NAME/OBJECT_KEY
```

Advanced
Provides enhanced server resources with more CPU, RAM, and storage for
demanding applications and workloads.

CORS
A security feature that controls which websites can access resources on
your server through cross-origin requests.

How to Apply CORS Policies to Vultr
Object Storage Subscription
Buckets
Introduction
Vultr Object Storage subscription allows users to configure Cross-Origin
Resource Sharing (CORS) policies to control which external origins can access
resources within their buckets. By setting appropriate CORS rules, users can
specify which domains are permitted to interact with their stored data, along
with allowed HTTP methods and headers. This feature is essential for web
applications that require secure access to assets from multiple domains while
ensuring data protection. Configuring CORS policies helps manage resource
access while maintaining security standards.
Follow this guide to apply CORS policies to Vultr Object Storage subscription
buckets using s3cmd and AWS CLI.
S3cmd
1. Deploy Vultr Object Storage subscription and create a bucket.
2. Configure s3cmd with Vultr Object Storage subscription.
```bash
$ s3cmd --configure
```
Follow the prompts and provide bucket credentials like Access Key,
Secret Key, Default Region and S3 Endpoint. You can retrieve these
credentials from the Vultr Object Storage subscription Overview page.

3. Enter the DNS-style template. For example, if you choose the New Jersey
location, use %(bucket)s.ewr1.vultrobjects.com .
DNS-style bucket+hostname:port template for accessing a
bucket [%(bucket)s.s3.amazonaws.com]: %(bucket)s.ewr1.vultrobjects.com
4. Upload a file in the bucket. Replace LOCAL_FILE_PATH with the local file path
and BUCKET_NAME with your bucket name.
```bash
$ s3cmd put LOCAL_FILE_PATH s3://BUCKET_NAME/
```
5. Create a new xml file, such as cors_rules.xml to set up a CORS bucket
policy.
```bash
$ nano cors_rules.xml
```
6. Copy the content below and paste it into the xml file.
XML
<CORSConfiguration>
<CORSRule>
<AllowedOrigin>*</AllowedOrigin>
<AllowedMethod>GET</AllowedMethod>
<AllowedMethod>POST</AllowedMethod>
<AllowedMethod>PUT</AllowedMethod>
<MaxAgeSeconds>3000</MaxAgeSeconds>
<AllowedHeader>*</AllowedHeader>
</CORSRule>
</CORSConfiguration>
Save and close the file.
7. Apply the CORS policy. Replace BUCKET_NAME with your bucket name.

```bash
$ s3cmd setcors cors_rules.xml s3://BUCKET_NAME
```
8. Verify the CORS policy if needed.
```bash
$ s3cmd getcors s3://BUCKET_NAME
AWS CLI
```
1. Deploy Vultr Object Storage and create a bucket.
2. Configure AWS CLI with Vultr Object Storage subscription.
```bash
$ aws configure --profile my-config
```
Follow the prompts and provide bucket credentials like Access Key,
Secret Key, and Default Region. These credentials can be retrieved
from the overview page of the Vultr Object Storage subscription.
3. Upload a file in the bucket. Replace HOSTNAME  with your S3 endpoint
hostname, BUCKET_NAME  with your bucket name, OBJECT_KEY  with the
destination key, and LOCAL_FILE_PATH  with the local file path.
```bash
$ aws --endpoint-url https://HOSTNAME --profile my-config
s3api put-object --bucket BUCKET_NAME --key OBJECT_KEY --
body LOCAL_FILE_PATH
```
4. Create a new json file to set up a CORS bucket policy.

```bash
$ nano cors_rules.json
```
5. Copy and paste the below content into the file.
```json
[
{
"AllowedOrigins": ["*"],
"AllowedMethods": ["GET", "POST", "PUT"],
"AllowedHeaders": ["*"],
"MaxAgeSeconds": 3000
}
]
Save and close the file.
```
6. Set the policy for the bucket. Replace HOSTNAME  with your S3 endpoint
hostname and BUCKET_NAME with your bucket name.
```bash
$ aws --endpoint-url https://HOSTNAME s3api put-bucket-cors
--bucket BUCKET_NAME --cors-configuration file://
cors_rules.json --profile my-config
```
7. Check the policy applied to the bucket if needed.
```bash
$ aws --endpoint-url https://HOSTNAME s3api get-bucket-cors
--bucket BUCKET_NAME --profile my-config

Public Read
Learn how to configure public read access for Vultr Object Storage
buckets to share files with anyone on the internet without authentication.
```

How to Apply a Public Read Policy
for Vultr Object Storage
Subscription
Introduction
Vultr Object Storage subscription public read setting provides a method for
sharing data with anyone on the internet. Setting a bucket access to public
allows anyone to retrieve files without authenticating to your subscription.
Therefore, only grant access to assets specifically intended for public like static
website hosting files.
Follow this guide to set Vultr Object Storage subscription to Public Read using
s3cmd and AWS CLI.
S3cmd
1. Deploy Vultr Object Storage subscription and create a bucket.
2. Configure s3cmd with Vultr Object Storage subscription.
```bash
$ s3cmd --configure
```
Follow the prompts and provide Bucket credentials like Access Key,
Secret Key, Default Region, and S3 Endpoint. You can retrieve these
credentials from Vultr Object Storage subscription Overview page.
3. Enter the DNS-style template. For example, if you choose the New Jersey
location, use %(bucket)s.ewr1.vultrobjects.com .

DNS-style bucket+hostname:port template for accessing a
bucket [%(bucket)s.s3.amazonaws.com]: %(bucket)s.ewr1.vultrobjects.com
4. Upload a file to the bucket. Replace LOCAL_FILE_PATH  with the local file path
and BUCKET_NAME with your bucket name.
```bash
$ s3cmd put LOCAL_FILE_PATH s3://BUCKET_NAME/
```
5. Copy the file URL.
6. Access the file in a browser. The output displayed in the image below
shows that you've not enable public access to objects in the bucket.
7. Create a new json  file to set up a bucket policy.
```bash
$ nano public-policy.json
```
8. Copy the content below and paste it into the json  file.
```json
{
"Version": "2012-10-17",
"Statement": [
{
"Sid": "PublicReadGetObject",
"Effect": "Allow",
"Principal": "*",
"Action": [
```

"s3:GetObject"
],
"Resource": [
"arn:aws:s3:::BUCKET_NAME/*"
]
}
]
}
Replace BUCKET_NAME  with your bucket name. Save and close the file.
The above S3 bucket policy grants public read-only access to all objects in
the bucket. In the above settings:
- Version : Uses AWS policy format as of 2012-10-17.
- Statement ID (Sid) : Label PublicReadGetObject  identifies this rule.
- Effect : "Allow" grants permission.
- Principal : "*" allows everyone public access.
- Action : "s3:GetObject" permits downloading objects.
- Resource : Applies to all objects in the bucket mentioned in the policy.
9. Set the bucket policy. Replace BUCKET_NAME  with your bucket name.
```bash
$ s3cmd setpolicy public-policy.json s3://BUCKET_NAME
```
10. Verify the bucket policy if needed.
```bash
$ s3cmd info s3://BUCKET_NAME
```
11. Confirm the new policy by accessing the object URL in a browser.
Note
If you want to access objects from another website, you must also apply a
CORS (Cross-Origin Resource Sharing) policy. Refer to the guide on How to
Apply CORS Policies to Vultr Object Storage subscription Buckets.

AWS CLI
1. Configure the AWS CLI.
```bash
$ aws configure --profile my-config
```
Follow the prompts and provide Bucket credentials like Access Key,
Secret Key, and Default Region. You can retrieve these credentials from
Vultr Object Storage subscription Overview page.
2. Upload a file to the bucket. Replace HOSTNAME with your S3 endpoint
hostname, BUCKET_NAME with your bucket name, OBJECT_KEY with the
destination key, and LOCAL_FILE_PATH with the local file path.
```bash
$ aws --endpoint-url https://HOSTNAME --profile my-config
s3api put-object --bucket BUCKET_NAME --key OBJECT_KEY --
body LOCAL_FILE_PATH
```
3. Copy the file URL.
4. Access the file in a browser. The output displayed in the image below
shows that you've not enabled public access to objects in the bucket.
5. Create a new json file, such as public-policy.json to set up a bucket policy.
```bash
$ nano public-policy.json
```
6. Copy the content below and paste it into the json file.
```json
{
"Version": "2012-10-17",
"Statement": [
{
"Sid": "PublicReadGetObject",
"Effect": "Allow",
"Principal": "*",
"Action": [
"s3:GetObject"
],
"Resource": [
"arn:aws:s3:::BUCKET_NAME/*"
]
}
]
}
Replace BUCKET_NAME  with your bucket name. Save and close the file.
```
7. Set the policy for the bucket. Replace HOSTNAME  with your S3 endpoint
hostname and BUCKET_NAME with your bucket name.
```bash
$ aws --profile my-config --endpoint-url https://HOSTNAME
s3api put-bucket-policy --bucket BUCKET_NAME --policy file://
public-policy.json
```
8. Verify the bucket policy if needed.
```bash
$ aws --profile my-config --endpoint-url https://HOSTNAME
s3api get-bucket-policy --bucket BUCKET_NAME
```
9. Confirm the new policy by accessing the object URL in a browser.

Note
If you want to access objects from another website, you must also apply a
CORS (Cross-Origin Resource Sharing) policy. Refer to the guide on How to
Apply CORS Policies to Vultr Object Storage subscription Buckets.

Limits
Defines the maximum capacity and usage restrictions for Vultr Object
Storage subscriptions.

Vultr Object Storage Subscription
Limits
Introduction
Vultr Object Storage is an S3-compatible solution that offers on-demand data
storage for business assets. The solution is ideal for storing web application
assets like images, audio, and videos.
Operations Limit
Vultr Object Storage subscription operations refer to the activities and
processes involved in managing a Vultr Object Storage subscription. This
includes creating, maintaining, and scaling Vultr Objects Storage subscription.
• Each Vultr Object Storage subscription supports up to 400 operations per
second, allowing for high-performance data access, retrieval, and
management at scale.
Bucket Limit
Vultr Object Storage subscription buckets are the primary organizational units
used to store and manage data. A bucket acts as a container for objects (files,
metadata, and data streams) and provides a structured way to store and
retrieve data. Buckets are globally unique within the Vultr Object Storage
system and can be configured with specific permissions, settings, and access
controls to manage how data is stored, secured, and accessed.
• Each Vultr Object Storage subscription includes a default limit of 100
buckets, with the option to request an increase by contacting support.

• Bucket names must be between 3 and 63 characters long. If you plan to
enable Archival Storage on a bucket, the name must be between 3 and 53
characters at creation time. Archival Storage cannot be enabled on a
bucket whose name exceeds 53 characters.
Storage Tiers and Performance
Vultr Object Storage offers multiple tiers to support a variety of workload needs.
Choose the tier that best matches your performance and cost requirements:
• Accelerated: High-performance NVMe storage optimized for write-intensive workloads.
Up to 10,000 IOPS, up to 5 Gbps throughput.
• Performance: Low-latency NVMe storage designed for datacenter
workloads.
Up to 4,000 IOPS, up to 1 Gbps throughput.
• Premium: Reliable and durable storage for general-purpose applications.
Stored on HDD, indexed on SSD.
Up to 1,000 IOPS, up to 800 Mbps throughput.
• Standard: Cost-effective, high-availability bulk storage. Stored on HDD,
indexed on SSD. Up to 800 IOPS, up to 600 Mbps throughput.
• Archive: Ultra low-cost storage for infrequently accessed data. Base price
is $6/month, which includes 100 GB of unarchived storage, 1000 GB of
archive storage, and 1 TB of bandwidth. Additional unarchived storage is
billed at $0.018 per GB-month; additional archive storage at $0.006 per
GB-month; additional bandwidth at $10/TB. Archived objects appear as 0
bytes in the bucket and must be restored before they can be accessed
directly. Shares the same rate limits as Standard.

Archival Storage Limits
Vultr Archival Object Storage is available on Standard (tier_id 2) and Archive
(tier_id 6) subscriptions. Accelerated, Performance, and Premium tiers do not
support archival.
Bucket Versioning
• Bucket versioning cannot be enabled while Archival Storage is active on a
bucket. Disable Archival Storage first.
• Once versioning is enabled on a bucket — even after Archival Storage has
been disabled — that bucket is permanently ineligible for Archival Storage.
Restore Window
• Objects retrieved via a direct download are available for 7 days before
returning to archive-only state.
• Objects retrieved via an explicit restore request are available for the
number of days specified in the request.
• Restored objects are billed at the Standard storage rate ($0.018 per GB-month) during the restore window, in addition to the Archive storage rate.
Lifecycle Policy Execution
• Lifecycle policies run at 00:00 UTC each day. The actual transition time
depends on cluster load at the time the policy runs.

FAQ
Frequently asked questions and answers about Vultr services, features,
and common issues.

170
06 What is the difference between Vultr Object Storage
subscription and Vultr Block Storage volume? 170
07 Can I use Vultr Object Storage subscription as a file system?
171
08 Can I use a custom domain for Vultr Object Storage
subscription? 171
09 I closed my Vultr Object Storage subscription but I want to
reuse a bucket name. How long must I wait? 171
010 Is Vultr Object Storage subscription included in the
Cloudflare bandwidth alliance? 172
011 What are the available Vultr Object Storage locations? 172
012 What tools are compatible with Vultr Object Storage for
transferring objects (files) 173

Frequently Asked Questions (FAQs)
About Object Storage
Introduction
These are the frequently asked questions for Vultr Object Storage subscription.
Can I Upgrade a Vultr Object Storage
subscription to a new tier?
No, you cannot upgrade a Vultr Object Storage tier directly. Provision a new
Vultr Object Storage subscription with your target tier and move your existing
buckets to the new subscription.
Is Vultr Object Storage subscription S3-compatible?
Yes, Vultr Object Storage subscription is S3-compatible and supports many tools
such as S3cmd, a command-line tool for uploading, retrieving and managing
data in S3-compatible buckets.
Vultr Object Storage subscription also supports many modern programming
languages, libraries, and SDK tools. For more information, visit the following
resources:
• How to Use Vultr Object Storage subscription in Python
• How to Use Vultr Object Storage subscription with PHP

How do I use Vultr Object Storage
subscription on Vultr Cloud Compute
instances?
Files (objects) can be transferred to Vultr Object Storage subscriptions directly
from Vultr Cloud Compute instances using an S3-compatible tool or SDK. The
Vultr Object Storage subscription documentation includes examples of using
popular tools.
Since my files on Vultr Object Storage
subscription are internet accessible, does
that mean anyone can access them?
When you transfer files (objects) to Vultr Object Storage subscription, they are
"private" by default. You need your Vultr Object Storage subscription credentials
to access the files. However, some tools allow you to override this behavior - be
sure to check the documentation included with the tool or SDK you use to
interact with the Vultr Object Storage subscription.
What is the difference between Vultr Object
Storage subscription and Vultr Block Storage
volume?
Vultr Object Storage subscription offers an internet-accessible endpoint for
storing and retrieving files via HTTPS. Vultr Block Storage volume provides
mountable disk volumes that extend the storage for Vultr Cloud Compute
instances.

Can I use Vultr Object Storage subscription
as a file system?
Vultr Object Storage subscription offers an internet-accessible endpoint for
storing and retrieving files via HTTPS. The overhead of HTTPS calls may severely
affect your applications performance. If you're looking for a mountable storage
solution, please use a Vultr Block Storage volume.
Can I use a custom domain for Vultr Object
Storage subscription?
Vultr Object Storage does not support white-label domain configurations.
However, you can create domain-style URLs using your existing buckets and
use a domain CNAME record to point a custom domain to the Vultr Object
Storage bucket URL. For example, a storage.example.com CNAME record pointing
to example-bucket.ewr1.vultrobjects.com .
I closed my Vultr Object Storage
subscription but I want to reuse a bucket
name. How long must I wait?
If you close a subscription, you must wait at least 48 hours before you can
reuse the old bucket name. If you delete a bucket via API, it will be available for
immediate reuse.

Is Vultr Object Storage subscription included
in the Cloudflare bandwidth alliance?
No, the Cloudflare Bandwidth Alliance program does not include the Vultr Object
Storage subscription traffic.
What are the available Vultr Object Storage
locations?
Vultr offers Object Storage in multiple locations, which gives you options for
geographic redundancy and performance. Choose a location close to your
clients and application for high performance and low latency. For high
availability and redundancy, you can back up to object storage in a different
location from your main application or use multiple object storage locations and
sync between them.
The available Object Storage locations and their hostnames are:
• Amsterdam: ams1.vultrobjects.com , ams2.vultrobjects.com
• Atlanta: atl1.vultrobjects.com , atl2.vultrobjects.com
• Bangalore: blr1.vultrobjects.com , blr2.vultrobjects.com
• Chicago: chi3.vultrobjects.com
• London: lhr1.vultrobjects.com
• Los Angeles: lax1.vultrobjects.com
• New Delhi: del1.vultrobjects.com
• New Jersey: ewr1.vultrobjects.com , ewr2.vultrobjects.com
• Seattle: sea1.vultrobjects.com
• Silicon Valley: sjc1.vultrobjects.com
• Singapore: sgp1.vultrobjects.com , sgp2.vultrobjects.com
• Sydney: syd1.vultrobjects.com
• Tokyo: nrt1.vultrobjects.com

What tools are compatible with Vultr Object
Storage for transferring objects (files)
• Vultr Console: You can perform basic Object Storage management tasks
in the Vultr Console. Some operations are limited. For example, the Vultr
Console cannot delete a bucket with more than 50,000 objects. Power
users should use one of the other tools below to work with Object Storage,
such as s3cmd .
• Cyberduck: A graphical file manager for Windows and Mac. It supports S3,
FTP, and many popular file-sharing services. Download it from cyberduck.io
and see our article How to Use Cyberduck with Vultr Object Storage.
• S3 Browser: A freeware Windows client for S3-compatible object storage.
Download it from s3browser.com and see our article How to use S3
Browser with Vultr Object Storage.
• s3cmd: A command line S3 client for Linux and Mac. Download it from
s3tools.org and see our article How to Use s3cmd with Vultr Object
Storage.
• UpdraftPlus: A popular WordPress backup plugin. See our article How to
Back Up WordPress to Vultr Object Storage with UpdraftPlus.
• Rclone: A command-line program to manage files on cloud storage.
Download it from rclone.org and see our article How to use Rclone with
Vultr Object Storage.

Storage Performance for
Vultr Object Storage
Comprehensive benchmarking and performance analysis of Vultr Object
Storage tiers, rate limits, workloads, and Warp-based replication
methodology.

Introduction
We have conducted extensive benchmarking of Vultr Object Storage across all
performance tiers. For additional context on the performance metrics
referenced throughout this document and to better understand how storage
performance is measured, benchmarked, and compared, see What Are the
Fundamentals of Storage Performance?.
Vultr Object Storage is available in four performance tiers: Standard,
Premium, Performance, and Accelerated.
The Standard and Premium tiers are primarily implemented on HDD storage
with flash acceleration for metadata and write-ahead caching. This architecture
improves metadata responsiveness and write performance while maintaining
cost efficiency.
The Performance and Accelerated tiers are based on NVMe storage. These
tiers are optimized for workloads running on Vultr Cloud Compute and GPU
instances within the same data center and provide significantly higher
throughput and operations per second than typical Internet-facing object
storage.
Rate Limits
Tiers of Vultr Object Storage are limited at the object gateway to not allow a
given subscription to exceed certain operations per second and throughput
levels. These limits are imposed to avoid situations where one object storage
subscription consumes all the available network throughput or processing
power available on the object gateway for its storage workload, limiting what
would be available for competing workloads.
| Tier | Operations Limit | Throughput Limit |
| --- | --- | --- |
| Standard | 800 ops per second | 600 MiB/s or 5.0 Gbps |
| Premium | 1,000 ops per second | 800 MiB/s or 6.7 Gbps |
| Performance | 4,000 ops per second | 1,000 MiB/s or 8.3 Gbps |
| Accelerated | 10,000 ops per second | 5,000 MiB/s or 41.9 Gbps |
It is important to understand how these limits interact with object sizes. For
instance, object sizes smaller than 524,288 bytes will not reach the Accelerated
tier’s throughput limit before reaching its operations limit.
Note also that metadata operations count toward the total operations per
second. This means that they subtract from the available operations for reads
and writes and so either reduce throughput for the remaining operations or
require larger object sizes to make that throughput limit possible to reach.
Benchmark Results
As a rate limited service, both for operations per second and throughput, it is
possible to reach one limit before reaching the other. Small object sizes will
reach operations thresholds before throughput thresholds and large object sizes
will reach throughput thresholds before operations thresholds. Moreover,
metadata operations contribute toward the operations per second limits and so
can negatively impact attainable throughput.
Standard Tier
The Standard tier is what most people would think of as conventional object
storage. It is Internet-facing, usually with its clients accessing it from the
internet. Access from Vultr Cloud Compute is possible, of course, but the
general expectation is that it is low throughput and high latency. This makes it
good for infrequently accessed objects and the accretion of large amounts of
data retained over long periods.
| Operation Type | Object Size | Objects/s | Throughput (MiB/s) |
| --- | --- | --- | --- |
| PUT | 4 KB | 469.9 | 1.8 |
| PUT | 64 KB | 343.2 | 20.1 |
| PUT | 512 KB | 393.6 | 190.1 |
| PUT | 1024 KB | 595.1 | 567.4 |
| PUT | 10240 KB | 57.9 | 552.8 |
| GET | 4 KB | 361.3 | 1.3 |
| GET | 64 KB | 422.4 | 25.7 |
| GET | 512 KB | 390.4 | 190.6 |
| GET | 1024 KB | 613.7 | 585.3 |
| GET | 10240 KB | 59.7 | 570.1 |
Premium Tier
The Premium tier has a 25% increase in operations per second and a 33%
increase in throughput relative to the Standard tier. It also has slightly better
write performance than Standard. This makes it better suited to workloads that
depend on better performance generally, particularly with writes, but still are
geared towards clients accessing from the internet that expect relatively low
throughput and high latency.
| Operation Type | Object Size | Objects/s | Throughput (MiB/s) |
| --- | --- | --- | --- |
| PUT | 4 KB | 560.5 | 2.1 |
| PUT | 64 KB | 540.7 | 33.0 |
| PUT | 512 KB | 539.7 | 263.5 |
| PUT | 1024 KB | 696.2 | 650.4 |
| PUT | 10240 KB | 77.2 | 736.9 |
| GET | 4 KB | 613.7 | 2.1 |
| GET | 64 KB | 569.2 | 34.7 |
| GET | 512 KB | 569.2 | 277.9 |
| GET | 1024 KB | 793.7 | 756.9 |
| GET | 10240 KB | 79.4 | 757.9 |
Performance Tier
The Performance tier is backed by NVMe storage but aims at a cost efficiency
rather than maximum performance. It allows for significantly more operations
per second and higher throughput than the Premium tier. It is also intended for
access primarily by Vultr Cloud Compute in the same data center rather than
clients over the Internet. This is not to say that it can’t be accessed over the

Internet, but rather that in-data center clients will see benefits from local
connectivity as compared to slower tiers.
| Operation Type | Object Size | Objects/s | Throughput (MiB/s) |
| --- | --- | --- | --- |
| PUT | 4 KB | 2,462.2 | 9.3 |
| PUT | 64 KB | 2,817.8 | 171.9 |
| PUT | 512 KB | 1,973.8 | 963.7 |
| PUT | 1024 KB | 1,010.5 | 963.7 |
| PUT | 10240 KB | 101.7 | 970.2 |
| GET | 4 KB | 2,872.9 | 10.9 |
| GET | 64 KB | 2,376.4 | 145.0 |
| GET | 512 KB | 1,974.3 | 964.0 |
| GET | 1024 KB | 1,010.6 | 963.8 |
| GET | 10240 KB | 101.1 | 964.1 |
Accelerated Tier
The Accelerated tier is designed to allow shared data access from within the
data center at higher rates of both throughput and operations per second.
Being accessible from the internet at the same time makes it ideally suited for
data ingestion to cluster computing, such as AI training. Depositing data on the
Accelerated tier of Object Storage makes it accessible for import onto, for
example, Vultr File System, where it can then be used at very high throughputs
required for keeping GPU clusters flush with data.
| Operation Type | Object Size | Objects/s | Throughput (MiB/s) |
| --- | --- | --- | --- |
| PUT | 4 KB | 8,483.7 | 32.3 |
| PUT | 64 KB | 8,470.9 | 517.0 |
| PUT | 512 KB | 6,749.3 | 3,295.5 |
| PUT | 1024 KB | 3,837.1 | 3,659.3 |
| PUT | 10240 KB | 400.8 | 3,822.4 |
| GET | 4 KB | 6,611.3 | 25.2 |
| GET | 64 KB | 8,255.3 | 503.8 |
| GET | 512 KB | 6,625.8 | 3,235.2 |
| GET | 1024 KB | 3,987.0 | 3,802.3 |
| GET | 10240 KB | 438.7 | 4,184.1 |
Replicating These Results
You can replicate these benchmarks using the warp  utility.
1. Install the warp  utility and any dependencies. It can be found at its official
GitHub repository, but your distribution likely has it available as a package.
In most distributions the package is simply called warp .
2. Warp operates by having a Warp Server that coordinates one or more Warp
Clients, each of which generates load against one or more S3 servers. This
allows synchronized workload generation across multiple client machines.
In our testing, we used eight Vultr VPS in the same region as the object
storage. To set up clients, on each server you’re using as a client you must
run the command:
```bash
$ warp client [listenaddress:port]
Where listenaddress:port  is an optional specification of the port and address
the Warp Client should listen on for connections from the Warp Server. Be
sure that your firewall on the hosts is opened to allow communication to
the ports you’ve configured your clients to use.
```
3. Once Warp Clients are running you can use the following command to
execute the benchmark from the Warp Server. Note that the server is not
generating any client activity itself. Rather, it is merely instructing the
clients to generate the workload.
```bash
$ warp get \
--duration=2m \
--warp-client=$WORKERS \

--host=$S3HOST \
--bucket=bucket-name-warp \
--access-key=$S3ACCESS_KEY \
--secret-key=$S3SECRET_KEY \
--tls \
--obj.size=512k \
--rps-limit=$RATE
In the above command, get can be replaced by any of several benchmarks
you may wish to run from amongst the list of available benchmark
workloads. For a full list of available benchmark types, see the Warp
documentation included at its GitHub repository. The options and variables
above have the following meanings:
```
- $WORKERS This is the list of Warp Clients to coordinate. The presence of
the --warp-client option indicates that Warp is acting as a server.
- $S3HOST The name of the S3 host to test against.
- --bucket The name of the bucket that Warp should test against.
- $S3ACCESS_KEY Your access key.
- $S3SECRET_KEY Your secret key.
- --obj.size The size of objects to be used in testing.
- $RATE Sets the rate of requests per client to limit 429 status returns
due to exceeding the object storage rate limit. This should be equal to
or slightly above the published request rate of the storage tier divided
by the number of Warp Clients in use.
Refer to the official Warp documentation for complete details.
Tuning Tips for Best Performance with Vultr
Object Storage
• Enable high levels of parallelism by making more simultaneous requests.
Increase the number of clients making requests or the number of threads
or workers per client. For instance, we used eight Vultr VPS as clients for
our testing with warp rather than testing with a single s3cmd .
• Object Storage is inherently high latency, so also allow for more requests
to be in flight waiting for replies so as not to allow high latency to lower

your throughput artificially. For example, when writing code to connect to
your Vultr Object Storage buckets, leverage your language’s object storage
library’s support for queues to allow multiple requests across your
connections.
• Honor 429 status codes by slowing down your own request rate.
Remember that requests that go unfulfilled because you have exceeded
your operations rate limit cost resources as well. Most client applications
support some form of back-off after receiving 429 status, allowing them to
avoid blasting the Object Storage with requests that will only result in more
429 status responses.
• If you are merely using s3cmd , consider moving to s5cmd instead. It has
considerably improved performance, particularly with regard to highly
parallelizable workloads. Refer to the official GitHub repository for further
details (specifically the Configuring Concurrency section).
• If you’re using Loki with Vultr Object Storage, it benefits from 3 or more
ingesters and queriers, increasing parallelism. Rclone has the --transfers
flag to increase parallelism and the --retries-sleep to handle rate limiting.

File System
Learn how to provision, manage, and mount file systems on your Vultr
infrastructure.

Provisioning
A guide explaining how to set up and configure Vultr File System Volumes
for use with your instances

How to Provision Vultr File System
Volume
Introduction
Vultr File System (VFS) offers a fully managed Virtiofs-based file system,
enabling efficient and seamless file sharing for Vultr Cloud Compute instances.
Vultr File System volumes use a serverless architecture, allowing multiple Vultr
Cloud Compute instances to connect simultaneously to a single volume,
simplifying data sharing and scalability. Vultr File System is suitable for use
cases like file sharing, application synchronization, machine learning data
processing, and optimizing storage for Content Management Systems (CMS).
Follow this guide to provision a Vultr File System volume using the Vultr Console
or Terraform.
Vultr Console
1. Navigate to Products, select Cloud Storage, and click File System.
2. Click Add File System.
3. Choose a storage location to deploy the Vultr File System volume.
4. Move the slider to set the volume's storage size.
5. Enter a label, then click Add File System to provision the Vultr File
System volume.
Terraform
1. Ensure the Vultr Terraform provider is configured in your Terraform project.
2. Define the File System volume resource.

```hcl
terraform {
required_providers {
vultr = {
source = "vultr/vultr"
version = "~> 2.23"
}
}
}
provider "vultr" {}
resource "vultr_vfs" "file_system" {
label = "File-System"
region = "ewr"
size_gb = 100
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Management
Comprehensive tools and features for administering, monitoring, and
controlling your Vultr infrastructure.

Attach Instances
Learn how to connect and manage Vultr File System volumes with your
instances for shared storage access.

How to Manage Attachments for
Vultr File System Volume
Introduction
Attaching a Vultr File System volume to a Vultr Cloud Compute instance allows
the instance to discover the serverless volume as a new storage device. You can
then mount the Vultr File System volume to share files across different Vultr
Cloud Compute instances. You can remove a Vultr File System volume from a
Vultr Cloud Compute instance.
Follow this guide to manage attachments for Vultr File System volume using the
Vultr Console or Terraform.
Vultr Console
1. Navigate to Products and select Compute.
2. Click the Vultr Cloud Compute instance you want to attach to the Vultr File
System volume.
3. Navigate to Settings and click Change Memory Backing. Select Shared
and click Update.
4. Navigate to Products and select Cloud Storage. Then, click File
System.
5. Select the target Vultr File System volume you want to attach to the Vultr
Cloud Compute instance.
6. Navigate to the File System Information and click Attachments.
7. Click Attach to attach the Vultr File System volume to your target Vultr
Cloud Compute instance.
8. Confirm the new change.
9. Navigate to Attachments and click Detach to remove the Vultr File
System volume from the Vultr Cloud Compute instance.

Terraform
1. Open your existing Terraform configuration for the File System volume (and
instances).
2. Attach: set attached_instances on the vultr_vfs resource and apply.
```hcl
resource "vultr_vfs" "file_system" {
```
# ...existing fields (label, region, size_gb)
attached_instances = [
vultr_instance.app1.id,
# vultr_instance.app2.id
]
}
3. Detach: remove instance IDs from the list (or set it to an empty list), then
apply.
```hcl
resource "vultr_vfs" "file_system" {
```
# ...existing fields (label, region, size_gb)
attached_instances = []
}
4. Ensure each instance has Memory Backing set to "Shared" (Settings >
Change Memory Backing > Shared) before attaching.

Delete
Learn how to permanently delete a Vultr File System Volume from your
account.

How to Delete Vultr File System
Volume
Introduction
Deleting a Vultr File System volume removes the serverless storage from your
account and stops further charges. Backup any important files before
performing this operation because you can't undo the change. You can migrate
the files to a different Vultr File System volume or a Vultr Cloud Compute
instance. Detach all Vultr Cloud Compute instances from the volume before
deleting.
Follow this guide to delete Vultr File System volume using the Vultr Console or
Terraform.
Vultr Console
1. Navigate to Products and select Cloud Storage.
2. Click File System. Then, select the target Vultr File System volume.
3. Click the delete icon to remove the volume.
4. Click Delete when prompted to confirm.
Terraform
1. Open your Terraform configuration where the File System resource is
defined.
2. Remove the vultr_vfs resource block, or destroy it by target.
```hcl
resource "vultr_vfs" "file_system" {
```
# ...existing fields (label, region, size_gb)
}
# To delete, either remove this block from configuration
# or run: terraform destroy -target vultr_vfs.file_system
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 0 changed, 1 destroyed.

Resize
A guide explaining how to increase the storage capacity of your Vultr File
System Volume

How to Resize Vultr File System
Volume
Introduction
Resizing Vultr File System volume allows you to scale your storage needs
depending on your current data usage. For example, you can scale up the
storage size from 80GB to 160GB or down to 40GB. You can only shrink a Vultr
File System volume to the current storage size. That is, if the current files have
occupied 5GB you can't shrink the volume to a lesser storage like 4GB.
Follow this guide to resize a Vultr File System volume using the Vultr Console or
Terraform.
Vultr Console
1. Navigate to Products and select Cloud Storage.
2. Then, Click File System.
3. Select the target Vultr File System volume.
4. Click the disk size under Usage.
5. Enter a new disk size, such as 160 GB and click Update.
Terraform
1. Open your Terraform configuration and locate the File System resource.
2. Update the size_gb argument with the new volume size.
```hcl
resource "vultr_vfs" "file_system" {
label = "File-System"

region = "ewr"
size_gb = 160 # Updated size
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Mount
A command used to attach file systems to the directory tree, making
them accessible to the operating system.

Linux
A guide explaining how to attach and mount Vultr Block Storage volumes
on Linux operating systems.

How to Mount a Vultr File System
Volume on Linux
Introduction
Mounting a Vultr File System volume on Linux allows you to expand storage and
share files across multiple Vultr Cloud Compute instances. This process involves
creating a mount point, mounting the Vultr File System volume, and configuring
it for automatic mounting at boot.
Follow this guide to mount a Vultr File System volume on Linux.
1. Check your system's Linux Kernel version and ensure it's 5.4.x or later.
```bash
$ uname -srm
```
2. Ensure your system is compatible with virtiofs .
```bash
$ sudo modinfo virtiofs
```
3. Verify that the virtiofs Kernel module is loaded.
```bash
$ lsmod | grep virtiofs
If the virtiofs module is not loaded, run the following command to load it
manually:
```

```console
$ sudo modprobe virtiofs
```
4. Create a new directory such as /mnt/vfs  to mount the Vultr File System
volume.
```bash
$ sudo mkdir /mnt/vfs
```
5. Mount the Vultr File System volume to the directory using its Mount Tag.
For instance, 79287343 .
```bash
$ sudo mount -t virtiofs 79287343 /mnt/vfs
Open the Vultr File System volume's management page to find the Mount
Tag to use in the above command.
```
6. Query the /etc/mtab  file to get information about the newly mounted
volume.
```bash
$ sudo cat /etc/mtab grep virtiofs
Copy the command's output to your clipboard. For instance:
79287343 /mnt/vfs virtiofs rw,relatime 0 0
```
7. Open the /etc/fstab  file to automatically mount the new volume at boot.
```bash
$ sudo nano /etc/fstab
```
8. Append the volume information you copied earlier to the end of the file.
```ini
79287343 /mnt/vfs virtiofs rw,relatime 0 0
Save and close the file.
```
9. List all mounted file systems and verify that the virtiofs volume is
available.
```bash
$ df -hT
Output:
tmpfs tmpfs 96M 1.2M 94M 2% /run
/dev/vda2 ext4 23G 6.6G 16G 30% /
tmpfs tmpfs 476M 0 476M 0% /dev/shm
tmpfs tmpfs 5.0M 0 5.0M 0% /run/lock
/dev/vda1 vfat 511M 6.1M 505M 2% /boot/efi
tmpfs tmpfs 96M 4.0K 96M 1% /run/user/1002
79287343 virtiofs 80G 0 80G 0% /mnt/vfs
```
10. Create a new greetingsfromvultr.txt file in the /mnt/vfs directory to test
write permissions on the volume.
```bash
$ echo "Greetings from Vultr" > /mnt/vfs/
greetingsfromvultr.txt

Windows
A family of Microsoft operating systems that provides a graphical user
interface for managing applications, files, and system resources on Vultr
instances.
```

How to Mount a Vultr File System
Volume on Windows
Introduction
Mounting a Vultr File System volume on a Windows instance requires multiple
third-party software installations and is dependent on the software working well
together to create a dedicated virtiofs service to manage VFS volumes. As a
result, Vultr can only offer best-effort support for the use of VFS on Windows.
The virtiofs protocol is not natively supported on Windows, and installing the
virtio-win driver and the Windows File System Proxy (WinFsp) application
creates a virtiofs service that manages the Vultr File System volumes attached
to your Windows instance.
Follow this guide to mount a Vultr File System volume on a Windows instance.
Install
virtio-win
1. Visit the Fedora virtio-win releases page, open the latest virtio-win
archive and download the virtio-win-guest-tools.exe file.

2. Open the downloaded virtio-win-guest-tools.exe file to launch the
installation wizard.
3. Agree to the virtio-win license terms and click Install.
4. Click Next and accept the end-user license agreement.
5. Click Next and keep the default virtio-win features.
6. Click Install to start the installation.
7. Click Finish to complete the installation.
8. Close the virtio-win installation wizard.
Install WinFsp
1. Visit the WinFsp releases page and download the latest WinFsp Installer to
your server.

2. Open the downloaded winfsp-<version>.msi package to launch the WinFsp
installation wizard.
3. Click Next to start the installation wizard.
4. Keep the default WinFsp features and click Next to continue.
5. Click Install to start the WinFsp installation process.
6. Click Finish to close the WinFsp installation wizard.

Enable the VirtIO-FS Windows Service
1. Press Win+R to open the Windows run dialog.
2. Enter services.msc in the input field and press Enter to open the Services
window.
3. Find and right-click VirtIO-FS Service from the list of services.
4. Select Properties from the list of options.
5. Click the Startup type drop-down and select Automatic to enable the
VirtIO-FS Service to start automatically at boot.

6. Click Start to run the VirtIO-FS Service.
7. Verify that the service status changes to Running and click Apply to save
the changes.
8. Click OK to close the VirtIO-FS Service properties window.
Access a Mounted Vultr File System Volume
The virtio-fs service automatically mounts all Vultr File System volumes
attached to your Windows instance when it starts. Follow the steps below to
access a mounted VFS volume if the virtio-fs service is running correctly on
your Windows instance.
1. Open the Windows File Explorer.
2. Click This PC and verify that the Vultr File System volume is mounted as a
new disk drive.

3. Double-click to open the Vultr File System volume.
4. Create a new greetingsfromvultr.txt file to test the write permissions on
your VFS volume.
Note
Reboot your Windows instance if the virtiofs service is not available
immediately after installation, does not run correctly or the Vultr File System
volume is not detected. Verify that the VFS volume is attached to your
Windows instance and start the virtiofs service to access the volume using
the Windows File Explorer.

FAQ
A collection of common questions and answers about file systems to help
users troubleshoot issues and understand key concepts.

Frequently Asked Questions (FAQs)
About File System
Introduction
These are the frequently asked questions for Vultr File System volume.
How Can I Mount Vultr File System volumes
on Windows?
Install the virtio-win driver for Windows and the WinFsp package to create a
dedicated virtiofs service that manages VFS volumes attached to your
Windows instance. You may need to reboot your instance after installing the
required software packages to apply the system changes.
Can I attach Vultr File System Volumes to a
Windows Instance at the same time with a
Linux-based instance?
Yes, you can attach Vultr File System Volumes to a Windows instance at the
same time with a Linux-based instance. Ensure to install all required software
packages on Windows, then verify that you can read and write files on the VFS
volume when mounted.

Can I attach multiple Vultr Cloud Compute
instances to the same Vultr File System
volume?
Yes, you can attach multiple Vultr Cloud Compute instances to a single Vultr File
System volume provided the instance and the volume are in the same Vultr
location.
What file system protocols does Vultr File
System volume support?
Vultr File System volumes support virtiofs , a shared file system that allows
Vultr Cloud Compute instances to share directories with the underlying host
efficiently, typically for use cases like shared storage or collaboration between
the host and the VMs.
Can I resize a Vultr File System volume?
Yes, you can resize a Vultr File System volume. Open the Vultr File System
volume's management page, click Usage, enter a new capacity, and click
Update to resize the volume.

Can I attach Vultr Cloud Compute instances
in different locations to a Vultr File System
volume?
No, you cannot attach Vultr Cloud Compute instances in different Vultr locations
to a Vultr File System volume. The instance and the volume must be in the
same Vultr location.
How can I view the Vultr Cloud Compute
instances attached to a Vultr File System
volume?
Open your target Vultr File System volume's management page and click
Attachments to view all Vultr Cloud Compute instances attached to the
volume.

Storage Performance for
Vultr File System
Comprehensive performance analysis of Vultr File System, including fio
and smallfile benchmarks, metadata optimization, and tuning guidance.

Introduction
Vultr File System is intended for clusters of CPU or GPU systems to share stored
data between them, with an eye toward cache coherency so that writes made
by any one client of the file system are seen by subsequent reads of the file
system by other clients. Because Vultr File System tends to be used with large
numbers of clients accessing the same file system at the same time, metadata
operations have also been heavily optimized.
For additional context on the performance metrics referenced throughout this
document and to better understand how storage performance is measured,
benchmarked, and compared, see What Are the Fundamentals of Storage
Performance?.
Rate Limits
To make performance tuning simple for large clusters, there are presently no
rate limits imposed on Vultr File System by default. We reserve the option to
impose such limits in the future if the lack of such limits is abused. Until such a
time, this means that Vultr File System can provide very high throughput in use
cases where workloads require lots of throughput, such as keeping data loading
into GPU memory in AI Training clusters.
Benchmark Results
With VFS, we performed two different sets of benchmarks.
• To test generalized read/write performance we used the utility fio to
measure performance for 4 KB, 64 KB, 512 KB, 1024 KB, and 4096 KB
block sizes. We ran tests with 100% read (both random and sequential),
100% write (again both random and sequential), and a mixed workload of
both reads and writes.

• We also used the benchmarking utility smallfile  to measure file system
performance, at 64 KB, 512 KB, 1024 KB and 4096 KB total file sizes. This
tool exercises file system semantics and metadata operations, something a
tool like fio cannot be used to measure properly.
We performed these tests across a wide variety of VM instance plans so as to
see break points where insufficient CPU or memory in the plan could impact
storage performance. We did not find such a break point with block
performance even on plans with only 1 core and 1 GB of RAM.
Fio
There are three different classes of hypervisor hosts at Vultr and they each have
different performance characteristics:
• Vultr Cloud GPU plans
• VX1 Plans
• All other CPU plans
Because of how these different plan types consume host resources, they may or
may not be able to optimally support VFS. Both Vultr Cloud GPU and VX1 plans
will perform optimally, whereas older GPU plans have less performance at the
time of this writing.
VCG plans and VX1 plans have the following performance profile.
| IO Type | Block Size | Mean IOPS | Mean Throughput (MiB/s) | Mean Latency (ms) |
| --- | --- | --- | --- | --- |
| randwrite | 4 KB | 12,398.0 | 48.4 | 78.1 |
| randwrite | 64 KB | 7,882.7 | 492.7 | 125.7 |
| randwrite | 512 KB | 2,826.2 | 1,413.1 | 368.0 |
| randwrite | 1 MB | 1,788.6 | 1,788.6 | 568.3 |
| randwrite | 4 MB | 383.2 | 1,532.6 | 2,520.0 |
| randread | 4 KB | 33,706.7 | 131.7 | 32.0 |
| randread | 64 KB | 21,353.8 | 1,334.6 | 52.0 |
| randread | 512 KB | 7,468.4 | 3,734.2 | 130.0 |
| randread | 1 MB | 5,287.3 | 5,287.3 | 185.0 |
| randread | 4 MB | 1,094.0 | 4,375.9 | 893.7 |
| randrw | 4 KB | 16,981.3 | 66.3 | 56.8 |
| randrw | 64 KB | 10,634.7 | 664.7 | 86.1 |
| randrw | 512 KB | 3,900.8 | 1,950.4 | 254.3 |
| randrw | 1 MB | 2,505.4 | 2,505.3 | 394.5 |
| randrw | 4 MB | 507.2 | 2,029.0 | 1,885.0 |
The following table shows the performance characteristics of the “other” plan
types.
| IO Type | Block Size | Mean IOPS | Mean Throughput (MiB/s) | Mean Latency (ms) |
| --- | --- | --- | --- | --- |
| randwrite | 4 KB | 1,489.2 | 5.4 | 20.5 |
| randwrite | 64 KB | 974.4 | 60.9 | 36.1 |
| randwrite | 512 KB | 357.2 | 188.75 | 84.58 |
| randwrite | 1 MB | 236.2 | 236.25 | 136.25 |
| randwrite | 4 MB | 63.0 | 252 | 508.25 |
| randread | 4 KB | 4,371.2 | 17.08 | 6.32 |
| randread | 64 KB | 2,560.0 | 160 | 12.23 |
| randread | 512 KB | 782.0 | 391 | 41.25 |
| randread | 1 MB | 427.8 | 427.75 | 77.8 |
| randread | 4 MB | 101.0 | 404 | 327 |
| randrw | 4 KB | 4,416.0 | 17.25 | 11.8 |
| randrw | 64 KB | 2,752.8 | 172.05 | 21.83 |
| randrw | 512 KB | 868.0 | 434 | 62.46 |
| randrw | 1 MB | 517.0 | 517 | 103.3 |
| randrw | 4 MB | 146.9 | 587.5 | 409.38 |
Smallfile
The smallfile benchmark exercises file system metadata operations. Generally,
repeatedly opening and closing small file sizes result in significant metadata

operations overhead. Many metadata operations have a significant cost when
compared to simply reading and writing data. Using fio  alone to gauge the
performance of your file system storage would ignore this, essentially only
exercising read and write operations without accounting for metadata
operations overhead.
We did a significant amount of performance optimization work to dial in the
right balance between impact to CPU and memory resources on the client hosts
and the overall performance of VFS as a result of our testing. We paid particular
attention to the performance when small files are opened, read, and then
closed on after another. The result of these optimizations at the hypervisor level
should lead to the best possible performance even when faced with what is
colloquially known as “the small file problem”.
The following table can give you an idea of how VFS will perform when these
metadata operations become a significant portion of your overall workload. For
example, stat operations on files can be particularly taxing, so being able to
perform them on a large number of files per second has been a significant focus
for us.
File Files/s or Total Data Size Throughput (MiB/
IO Type
Size IOPS (GiB) s)
64 KB 4,808.8 56.2 300.6
create
create 512 KB 2,954.5 433.7 1,477.4
create 1024 KB 1,702.3 735.5 1,702.6
4096 KB 3,249.0 1,166.9 3,249.5
create
append 64 KB 4,021.8 56.6 251.4
512 KB 2,295.5 459.7 1,147.8
append
append 1024 KB 1,646.0 851.8 1,646.5
4096 KB 4,036.7 1,504.4 4,037.1
append
stat 64 KB 13,548.8 N/A N/A
512 KB 10,944.3 N/A N/A
stat
stat 1024 KB 10,365.8 N/A N/A
stat 4096 KB 13,714.3 N/A N/A
64 KB 10,815.8 N/A N/A
chmod
chmod 512 KB 9,773.8 N/A N/A

File Files/s or Total Data Size Throughput (MiB/
IO Type
Size IOPS (GiB) s)
1024 KB 7,313.5 N/A N/A
chmod
chmod 4096 KB 10,175.0 N/A N/A
64 KB 8,428.0 60.7 526.8
read
read 512 KB 4,279.3 485.3 2,139.9
1024 KB 2,482.8 835.8 2,483.1
read
read 4096 KB 5,966.0 1,448.6 5,966.4
overwrite 64 KB 3,458.3 57.6 216.2
512 KB 2,524.8 464.8 1,262.5
overwrite
overwrite 1024 KB 1,507.8 822.2 1,508.0
4096 KB 3,469.3 1,514.0 3,469.7
overwrite
delete 64 KB 6,715.8 N/A N/A
512 KB 5,717.8 N/A N/A
delete
delete 1024 KB 7,642.3 N/A N/A
4096 KB 6,686.7 N/A N/A
delete
Some interesting things to note about the table above:
• Some of the IO Types do not result in transfer of data, only metadata, as a
result they do not have a corresponding data size or throughput associated
with the test. In those cases, the results represent the number of files
processed per second rather than the number of IOPS.
• The 4096 KB file size aligns with the object size of the underlying storage,
so it tends to perform better than the trend with smaller file sizes might
predict because it leads to less back-end storage system communication
between storage cluster nodes.
Replicating These Results
Vultr File System is benchmarked using two different methods.

Using fio
You can replicate these results for yourself by using fio at any of the blocksizes
mentioned at any operations mix you would like.
1. Install the fio utility and any dependencies. It can be found on
git.kernel.org, but your distribution likely has it available as a package. In
most distributions the package is simply called fio . You should also install
libaio so that it is available to fio . The package is usually called either
libaio_dev or libaio_devel , depending on your distribution.
2. When running fio , you will need to create a job configuration file that you
can reference and then run a command line that points at the job file.
```ini
[FIOJOB]
filename=/mnt/vbs/fio.raw
size=500G
random_generator=lfsr
buffered=0
direct=1
invalidate=0
ioengine=libaio
rw=randwrite
bs=4k
iodepth=4
numjobs=16
runtime=900
loops=1
time_based=1
Key values to change to match the workload you are testing are:
```
- filename= This should be a file on the file system where you are
testing. If you are testing directly on the block device itself,
understand that the test is destructive to any data contained in the
file and will destroy any file system on the raw device.
- direct= 1 enables O_DIRECT , 0 disables it. Use direct=1 with
ioengine=libaio .

- ioengine= We recommend libaio for best results, but you may wish to
compare it with sync or psync .
- rw= randread , randwrite , and randrw are the most useful options.
- bs= Block size.
- iodepth= The queue depth per job.
- numjobs= The number of simultaneous jobs to run.
3. Then you can reference the job config from the command line:
```bash
$ fio \
--eta=never \
--status-interval=5000ms \
--output-format=json+ \
$FIOJOBFILE
Where $FIOJOBFILE is the path to the job file created above. See the fio
documentation for more details.
Using smallfile
```
1. To obtain smallfile you can download it from its GitHub repository. It
requires Python.
2. You need to create a YAML jobfile describing the job parameters. Refer to
the smallfile documentation on its GitHub repository for full details, but the
jobfile takes the following form.
```ini
top: /mnt/vfs/smallfile
operation: create
output-json: /tmp/smallfile/smallfileresults.json
files: 1000
threads: 100
auto-pause: true
file-size: 512
files-per-dir: 1000
dirs-per-dir: 1000
hash-into-dirs: true
```

xattr-size: 128
finish: true
Key values to change to match the workload you are testing are:
- top: This is the path to the filesystem you’re testing. Change it to
match your VFS mount point.
- operation: This is the operation benchmark type. See the smallfile
documentation for a full list of available benchmarks.
- output-json: This is the path to the output file for your results.
- threads: The number of threads to execute the benchmark. We used
100.
- file-size: The size of the file used for testing. We used 4k, 64k, 512k,
1M, and 4M in our testing.
3. Once the job file is created, you can execute the benchmark with the
command:
```bash
$ python3 smallfile_cli.py \
--yaml-input-file=$SMALLFILEJOBFILE
In the above command, $SMALLFILEJOBFILE is the path to the jobfile created
above.
Tuning Tips for Best Performance with Vultr
File System
• Run the latest kernel possible in your instance. Recent kernels have
significant optimizations for the virtio-fs filesystem type used by VFS.
• Be sure to mount the file system with the relatime or noatime mount
options if your application permits. Updating atime is expensive if your
application doesn’t require it. See the documentation for the mount
command and the /etc/fstab configuration file for your OS distribution for
more details.

• Metadata operations are expensive. Avoid opening and closing files
repeatedly whenever possible. Instead, open files and keep them open
until they are no longer needed. Consolidating data into larger files that
can be opened once and kept open (such as databases and big data file
formats) can make a huge difference in file system performance (for all file
systems, not just VFS).
• Avoid synchronous IO such as psync under most workloads. Instead, use
libaio for the benefit of greater queue depths. Test both to determine best
performance. Some applications may be able to leverage libaio via a
configurable option. If you’re writing your own application, see the
documentation for libaio as used in the language of your choice. For fio ,
enabling libaio is achieved with the option ioengine=libaio .
• Direct I/O allows you to bypass Linux caches. Consider using O_DIRECT for
increased performance. In fio this is enabled with the combination of two
options: direct=1 and buffered=0 .
• Enable high levels of parallelism by making more simultaneous requests.
Increase the number of processes, threads or workers making requests.
How to do this in your specific application will vary. Many applications will
have configuration options, and many libraries will have methods for doing
this. In the fio benchmarking utility you can increase parallelism by
increasing numjobs .
If you are trying to discover best possible performance limits on a system
where you do not already know the potential bottlenecks you can try
repeatedly increasing levels of parallelism until you discover the point
where increasing parallelism does not result in improved performance.
Typically this will be some multiple of the number of available threads on
your CPU. Start with 1 x vCPU and work up from there.
• Increasing queue depths will allow for more requests to be in flight waiting
for replies so as not to allow high latency to lower your throughput
artificially. How to do this in your specific application will vary. Many
applications will have configuration options, and many libraries will have
methods for doing this. In the fio benchmarking utility you can increase

the number of requests each job will allow to be in flight without a
response by increasing iodepth .
If you are trying to discover best possible performance limits on a system
where you do not know the potential bottlenecks you can try repeatedly
increasing the queue depth until you discover the point where a deeper
queue does not result in improved performance. Typically this is a function
of average latency and the number of requests you can queue while
waiting for a typical response. The goal is to have a queue that is always
full.

Storage Gateway
A scalable cloud storage solution that provides file sharing capabilities
with easy provisioning, management, and mounting options.
```

Provisioning
A guide explaining how to set up and configure Vultr Storage Gateway on
your infrastructure

How to Provision Vultr Storage
Gateway
Introduction
Vultr Storage Gateway (an NFS Gateway for Vultr File System) enables Vultr
Bare Metal and Cloud Compute instance to access scalable Vultr File System
(VFS) volumes over NFSv4, delivering high-speed, persistent cloud storage
without local disk limitations. Available in all regions that support VFS, the
gateway is designed for Bare Metal workloads that require dedicated storage
access. It also serves as a way to share VFS volumes between your Bare Metal
and other Vultr Cloud Compute instances in the same region, offering seamless
integration and high-performance data management across your infrastructure.
Follow this guide to provision a Vultr Storage Gateway using the Vultr API.
1. Send a GET request to the List VFS endpoint to retrieve available Vultr File
System volumes.
```bash
$ curl "https://api.vultr.com/v2/vfs" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Note the id of the VFS volume you want to attach to the Storage Gateway.
2. Provision a Vultr Storage Gateway by selecting either a Public Network or a
VPC Network.
- Provision Vultr Storage Gateway on a Public Network.
▪ Send a POST request to the Create Storage Gateway endpoint
to deploy a Storage Gateway instance with public IP enabled.

```bash
$ curl "https://api.vultr.com/v2/storage-gateways" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
      "region": "<vultr-location>",
      "label": "<storage-gateway-label>",
      "type": "nfs4",
      "export_config": [
        {
          "label": "<export-label>",
          "vfs_uuid": "<vfs-id>",
          "pseudo_root_path": "/vfs0",
          "allowed_ips": ["<bare-metal-ip>/32"]
        }
      ],
      "network_config": {
        "primary": {
          "ipv4_public_enabled": true,
          "ipv6_public_enabled": true
        }
      }
    }'
```
- Provision Vultr Storage Gateway Inside a Virtual Private Cloud (VPC).
1. Send a GET request to the List VPCs endpoint to retrieve
available VPCs in your account.
```bash
$ curl 'https://api.vultr.com/v2/vpcs' \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Note the vpc id  of the target VPC where the Storage Gateway
should reside.
2. Send a POST  request to the Create Storage Gateway endpoint
to deploy a Storage Gateway instance inside the VPC.

```bash
$ curl "https://api.vultr.com/v2/storage-gateways" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
"region": "<vultr-location>",
"label": "<storage-gateway-label>",
"type": "nfs4",
"export_config": [
{
"label": "<export-label>",
"vfs_uuid": "<vfs-id>",
"pseudo_root_path": "/vfs0",
"allowed_ips": ["<bare-metal-vpc-ip>/32"]
}
],
"network_config": {
"primary": {
"ipv4_public_enabled": true,
"ipv6_public_enabled": true,
"vpc": {
"vpc_uuid": "<vpc-id>"
}
}
}
}'
This deploys a Storage Gateway configured for private VPC
networking, without public IP addresses.
```
3. Send a GET request to the List Storage Gateways endpoint to retrieve
detailed metadata for this storage gateway using its ID.
```bash
$ curl "https://api.vultr.com/v2/storage-gateways/<storage-gateway-id>" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"

A successful response includes metadata such as status, type, network
settings, and export configuration ensure the health field shows Running to
confirm the gateway is operational.
```

Management
Tools and features for managing your Vultr infrastructure, including
monitoring, alerts, and account administration.

Create Export
Learn how to add an export to an existing Vultr Storage Gateway to share
data with clients

How to Add an Export for an
Existing Vultr Storage Gateway
Introduction
Vultr Storage Gateway (an NFS Gateway for Vultr File System) enables scalable
NFS-based access to VFS volumes from Vultr Bare Metal and Cloud Compute
instances. Adding an export to an existing gateway lets you
• Share a single VFS volume across multiple Bare Metal instances.
• Attach multiple VFS volumes to a single instance.
• Manage shared storage more efficiently across your infrastructure.
Follow this guide to create an export for an existing Vultr Storage Gateway
using the Vultr API.
1. Send a GET  request to the List Storage Gateways endpoint to retrieve
the available Vultr Storage Gateways.
```bash
$ curl "https://api.vultr.com/v2/storage-gateways" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List VFS endpoint to retrieve available Vultr File
System volumes.
```bash
$ curl "https://api.vultr.com/v2/vfs" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST request to the Add Storage Gateway Export endpoint to
add a new export for an existing Storage Gateway.
```bash
$ curl "https://api.vultr.com/v2/storage-gateways/<storage-gateway-id>/exports" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
"label": "<my-export-label>",
"pseudo_root_path": "<export-path>",
"vfs_uuid": "<vfs-volume-id>",
"allowed_ips": [
"<bare-metal-ip>/32"
]
}'
```
4. Send a GET request to the Storage Gateway endpoint using the Storage
Gateway ID to verify that the export was created.
```bash
$ curl "https://api.vultr.com/v2/storage-gateways/<storage-gateway-id>" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"

Delete Export
Learn how to permanently remove an export from your Vultr Storage
Gateway
```

How to Delete an Export for an
Existing Vultr Storage Gateway
Introduction
Vultr Storage Gateway (an NFS Gateway for Vultr File System) allows Vultr Bare
Metal and Cloud Compute instances to access VFS volumes over NFS. If you no
longer want a specific VFS volume exposed through a gateway, you can remove
its export configuration. Deleting an export revokes access to the specified
volume via NFS for any clients relying on that export, effectively detaching it
from the gateway without affecting the underlying VFS volume.
Follow this guide to delete an export for an existing Vultr Storage Gateway
using the Vultr API.
1. Send a GET  request to the List Storage Gateways endpoint to list all
configured Storage Gateways. Note the IDs of the Storage Gateway and
the export you want to delete.
```bash
$ curl "https://api.vultr.com/v2/storage-gateways" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete Storage Gateway Export endpoint
with the Storage Gateway ID and export ID to remove the specified export.
```bash
$ curl "https://api.vultr.com/v2/storage-gateways/<storage-gateway-id>/exports/<export-id>" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"

Delete Storage Gateway
Learn how to permanently remove a Vultr Storage Gateway from your
account
```

How to Delete Vultr Storage
Gateway
Introduction
Vultr Storage Gateway (an NFS Gateway for Vultr File System) provides NFS
access to VFS volumes from Vultr Bare Metal or Cloud Compute instances. When
you no longer need a gateway, you can delete it to stop further charges.
Deleting a storage gateway is permanent and cannot be undone. This action
does not delete your VFS volumes—your data remains safe and intact.
Follow this guide to delete a Vultr Storage Gateway using the Vultr API.
1. Send a GET  request to the List Storage Gateways endpoint and note the
Storage Gateway ID.
```bash
$ curl "https://api.vultr.com/v2/storage-gateways" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete Storage Gateway endpoint and
specify the Storage Gateway ID.
```bash
$ curl "https://api.vultr.com/v2/storage-gateways/{storage-gateway-id}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"

Update Storage Gateway
Learn how to update your Vultr Storage Gateway to access the latest
features and security improvements.
```

How to Update Vultr Storage
Gateway
Introduction
Vultr Storage Gateway (an NFS Gateway for Vultr File System) allows scalable
NFS access to VFS volumes. You can update a gateway’s label to better organize
your infrastructure, enforce naming conventions, or reflect project changes.
Follow this guide to update a Vultr Storage Gateway using the Vultr API.
1. Send a GET  request to the List Storage Gateways endpoint and copy the
ID of the gateway you want to update.
```bash
$ curl "https://api.vultr.com/v2/storage-gateways" \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Storage Gateway endpoint using the
copied ID. The only supported field for updates is the label.
```bash
$ curl "https://api.vultr.com/v2/storage-gateways/<storage-gateway-id>" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
      "label": "<your-new-storage-gateway-label>"
    }'
```
3. Send a GET  request to the Storage Gateway endpoint using the Storage
Gateway ID to confirm the updated label.

```bash
$ curl "https://api.vultr.com/v2/storage-gateways/<storage-gateway-id>" \
-H "Authorization: Bearer ${VULTR_API_KEY}"

Mount
A command that attaches a filesystem to a specific directory in the
systems directory tree, making it accessible to users.
```

Linux
A guide for mounting Vultr Storage Gateway on Linux systems to access
VFS volumes over NFSv4.

How to Mount Vultr Storage
Gateway in Linux
Introduction
Mounting a Vultr Storage Gateway — an NFS Gateway for Vultr File System
(VFS) — allows your Vultr Bare Metal and Cloud Compute instances to access
VFS volumes over NFSv4. This integration enables seamless, high-performance
cloud storage access with the flexibility and scalability of VFS, eliminating the
limitations of local disks. Follow this guide to mount a Vultr Storage Gateway on
a Linux instance using the NFS protocol.
1. Install the required dependencies based on your operating system. These
tools enable your instance to communicate with the Vultr Storage Gateway
using the NFS protocol.
- Ubuntu/Debian
▪ Update the server package index and install the nfs-common
package.
```bash
$ sudo apt update && sudo apt install nfs-common -y
```
- RHEL/RockyLinux/AlmaLinux
▪ Install the nfs-common package.
```console
$ sudo dnf install nfs-utils -y
```
2. Send a GET request to the List Storage Gateways endpoint to retrieve all
your available Storage Gateways, and note the IP address defined in the

public_ips  array under the network_config  section, you’ll use this IP address
to mount the Storage Gateway.
```bash
$ curl "https://api.vultr.com/v2/storage-gateways" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Use the below command to mount your Vultr Storage Gateway to a local
directory. Replace <storage-gateway-ip> , <export-path> , and <mount-point>  with
the actual values from your setup.
```bash
$ sudo mount -v -t nfs -o vers=4.2,soft,rw <storage-gateway-ip>:/<export-path> /mnt/vfs
```
- vers=4.2 : specifies the NFS version.
- soft : allows the system to timeout if the server is unresponsive.
- rw : mounts the export with read/write access.
- /mnt/vfs : is your local mount point. You can create it using mkdir -p /
mnt/vfs if it doesn’t exist.
4. Back up the existing /etc/fstab file before making any changes.
```bash
$ sudo cp /etc/fstab /etc/fstab.bak
```
5. Open the /etc/fstab file in a text editor.
```bash
$ sudo nano /etc/fstab
```
6. Add the following line at the end of the file to ensure the Vultr Storage
Gateway mounts automatically on boot.

```ini
<storage-gateway-ip>:/<export-path> /mnt/vfs nfs
defaults,_netdev,vers=4.2,soft,rw 0 0
Replace <storage-gateway-ip> and <export-path> with the actual values from
your setup.
```
7. Reload the system daemon.
```bash
$ sudo systemctl daemon-reexec
```
8. Apply the changes and test the configuration.
```bash
$ sudo mount -a
Your Vultr Storage Gateway is now permanently mounted to your instance.
```