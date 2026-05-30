Compute
Scalable cloud computing solutions offering various instance types
optimized for different workloads and performance requirements.

VX1™ Cloud Compute
Vultr VX1™ Cloud Compute delivers affordable, high-performance
enterprise-grade compute for web, app, and data workloads.

VX1™ Cloud Compute Product Documentation
Provisioning
Provision a high-performance Vultr VX1™ Cloud Compute instance using
the Customer Portal or API, with flexible boot options including local
NVMe and Block Storage.

How to Provision Vultr VX1™ Cloud
Compute Instances
Introduction
Vultr VX1™ Cloud Compute delivers industry-leading price-performance with
dedicated CPU resources. VX1™ supports booting from high-performance Vultr
Block Storage and can also leverage local NVMe for high-speed scratch storage.
Follow this guide to provision a Vultr VX1™ Cloud Compute instance using the
Vultr Console or Vultr API.
Note
VX1™ is available in select locations and expanding to more regions. To verify
availability, navigate to the Deploy Instance page in the Vultr Console,
select the required VX1™ plan, and verify that it is available in your preferred
location.
Vultr Console
1. Navigate to Products and click Compute.
2. Click Deploy.
3. Choose Dedicated CPU as the instance type.
4. Select your desired Vultr location to deploy the instance.
5. Select VX1 from the sidebar plan categories.
6. Select a plan from the available options:
- General Purpose ( vx1-g-* ): Provide a balanced combination of
vCPUs and memory, suitable for most workloads including web

servers, application servers, development environments, container
workloads, and moderate database deployments.
- Memory Optimized ( vx1-m-* ): Provide a higher memory-to-vCPU
ratio, ideal for workloads requiring large in-memory datasets such as
caching engines, analytics workloads, JVM applications, high-memory
web services, and large databases.
Note
Plans ending with -###s suffix (such as vx1-g-4c-16g-240s ) include local
NVMe storage.
7. Click Configure Software.
8. Select Boot Disk Settings:
- Local NVMe: Boot from high-speed local NVMe storage.
- Bootable Block Volume: Boot from Vultr Block Storage. Select an
existing bootable block volume or click Create Bootable Block
Volume to create a new one. When creating a bootable block volume,
select the operating system, storage size, and label.
9. Select a cloud image to install on your instance based on the following
options:
- Operating System: Installs a fresh operating system image on the
instance.
- Marketplace Apps: Installs a prebuilt software stack or application
and the recommended operating system image on the instance.
- ISO/iPXE: Boots a specific ISO available or iPXE-compatible image on
the instance.
- ISO Library: Installs a specific ISO image from the Vultr ISOs library.
- Backup: Recovers a specific backup available in your Vultr account to
the instance.
- Snapshot: Installs a specific snapshot available in your Vultr account
to the instance.

10. Select optional Server Settings to apply on the instance.
- SSH Keys: Installs a specific SSH key on the instance.
- Startup Script: Enables a startup script to execute at deployment or
a PXE script to automate the operating system installation.
- Firewall Group: Activates a Vultr Firewall group to filter incoming
network traffic on the instance.
11. Enter a new hostname in the Server Hostname field and a descriptive
label in the Server Label field to identify the instance.
12. Configure Additional Features for the instance.
- Instance Connectivity: Select how the instance connects to the
internet.
▪ Instance(s) with Public IP: Assigns public IP addresses directly
to the instance. Under Instance Address, Public IPv4 is
enabled by default. Select Public IPv6 to enable IPv6
addressing. After selecting IPv6, you can optionally deselect
Public IPv4 to create an IPv6-only instance.
▪ Private Instance(s) behind NAT Gateway: Routes internet
traffic through a NAT Gateway in a Virtual Private Cloud (VPC)
Network. Select an existing VPC Network with a NAT Gateway or
click Add VPC Network to create a new one.
- VPC Network: Connects the instance to a VPC Network in the current
location.
- Automatic Backups: Automatically creates backups for data
recovery in case of instance failures.
- DDoS Protection: Prevents potential Distributed Denial of Service
(DDoS) attacks on the instance.
- Limited User Login: Creates a linuxuser non-root user with sudo
privileges as the default user account instead of root .
- Cloud-Init User Data: Enables Cloud-Init user data to initialize and
customize the instance at boot.
13. Click Deploy to provision the instance.

Vultr API
Use the examples below as a reference for deploying VX1™ instances using API.
Boot from Local NVMe
In this section, you create a VX1™ instance that boots directly from the high-performance local NVMe device included with -###s plans. You can rely on the
default boot configuration or explicitly specify the local NVMe disk as the
bootable device, depending on your deployment requirements.
Option A — Basic Local Boot (Default Local NVMe)
Send a POST request to the Create Instance endpoint to create a VX1™ instance
using local NVMe as the default boot device.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X POST \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
--data '{
"region": "ewr",
"plan": "vx1-g-4c-16g-240s",
"label": "VX1 Local Disk Only",
"hostname": "vx1-localonly-1",
"os_id": 2284
}'
Option B — Explicit Local Boot Configuration
Send a POST request to the Create Instance endpoint to explicitly configure the
local NVMe device (block_id: "local" ) as the boot drive.
```
```console
```

$ curl "https://api.vultr.com/v2/instances" \
-X POST \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
--data '{
        "region": "ewr",
        "plan": "vx1-g-4c-16g-240s",
        "label": "VX1 Local Disk Only - Bootable",
        "hostname": "vx1-localonly-2",
        "os_id": 2284,
        "block_devices": [
        {
            "block_id": "local",
            "bootable": true
        }
        ]
    }'
Note
Select a plan with the -###s  suffix (for example, vx1-g-4c-16g-240s ) to include
local NVMe storage.
Boot from Block Storage
In this section, you create a VX1™ instance that boots from a high-performance
block storage volume. You can either provision a bootable block device first and
attach it to a new instance or create a VX1™ instance that includes a newly
provisioned bootable block volume during deployment.
Option A - Create a Bootable Block Volume and VX1™ Instance
1. Send a POST request to the Create Block Storage endpoint to create a
bootable block device.
```bash
$ curl "https://api.vultr.com/v2/blocks" \
-X POST \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${VULTR_API_KEY}" \

--data '{
"region": "ewr",
"size_gb": 50,
"label": "Bootable Block",
"block_type": "high_perf",
"os_id": 2284,
"bootable": true
}'
```
2. Send a POST request to the Create Instance endpoint to create the VX1™
instance using the previously created bootable block volume.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X POST \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
--data '{
"region": "ewr",
"plan": "vx1-g-4c-16g",
"label": "vx1-blockonly-existing-boot-block-1",
"hostname": "vx1-blockonly-existing-boot-block-1",
"os_id": 2284,
"block_devices": [
{
"block_id": "BLOCK_UUID",
"bootable": true
}
]
}'
Replace BLOCK_UUID with the UUID of your bootable block.
Option B — Create a VX1™ Instance with a New Bootable Block
Send a POST request to the Create Instance endpoint to create the VX1™
instance and provision a new bootable block device at the same time.
```
```console
$ curl "https://api.vultr.com/v2/instances" \
```
-X POST \

-H "Content-Type: application/json" \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
--data '{
        "region": "ewr",
        "plan": "vx1-g-4c-16g",
        "label": "vx1-blockonly-new-boot-block-1",
        "hostname": "vx1-blockonly-new-boot-block-1",
        "os_id": 2284,
        "block_devices": [
        {
            "disk_size": 50,
            "label": "New Bootable Block",
            "bootable": true
        }
        ]
    }'
Replace BLOCK_UUID  with the UUID of your bootable block device.
Boot from Local NVMe and Block Storage
In this section, you deploy a VX1™ instance that boots from a block storage
device while also attaching the high-performance local NVMe disk for additional
data storage. You can create a new bootable block volume during deployment
or boot from an existing bootable block device.
Option A — New Bootable Block + Local Storage
Send a POST  request to the Create Instance endpoint to create a VX1™ instance
that boots from a new bootable block device and includes local NVMe for
additional data storage.
```console
$ curl "https://api.vultr.com/v2/instances" \
```
-X POST \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
--data '{
        "region": "ewr",
        "plan": "vx1-g-4c-16g-240s",

"label": "vx1-new-boot-block-plus-local-1",
"hostname": "vx1-new-boot-block-plus-local-1",
"os_id": 2284,
"block_devices": [
{
"disk_size": 50,
"label": "New Bootable Block",
"bootable": true
},
{
"block_id": "local"
}
]
}'
Option B — Existing Bootable Block + Local Storage
Send a POST request to the Create Instance endpoint to create a VX1™ instance
that boots from an existing bootable block device and includes local NVMe.
```console
$ curl "https://api.vultr.com/v2/instances" \
```
-X POST \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
--data '{
"region": "ewr",
"plan": "vx1-g-4c-16g-240s",
"label": "vx1-existing-boot-block-plus-local-1",
"hostname": "vx1-existing-boot-block-plus-local-1",
"os_id": 2284,
"block_devices": [
{
"block_id": "local"
},
{
"block_id": "BLOCK_UUID",
"bootable": true
}
]
}'
Replace BLOCK_UUID with the UUID of your bootable block device.
Note
After deployment, format and mount the local NVMe disk inside your
operating system if you plan to use it for data storage.
Additional Notes
• Windows operating systems are not available for VX1™ instances.
• When creating bootable block devices, you must set block_type to
high_perf .

Connection
Establish connectivity to your Vultr resources through various network
protocols and access methods.

PuTTY
Connect to your Vultr VX1™ Cloud Compute instance on Windows using
PuTTY with either default user credentials or SSH keys.

How to Connect to a Vultr VX1™
Cloud Compute Instance Using
PuTTY
Introduction
PuTTY is an open-source terminal emulator and SSH client for Windows
workstations. It provides a user-friendly interface and terminal to connect to
instances using SSH. PuTTY supports both password-based authentication and
SSH keys for secure connections to an instance.
Follow this guide to connect to a Vultr VX1™ Cloud Compute instance using
PuTTY on Windows.
Connect to an Instance Using the Default
User Credentials
1. Open PuTTY from your applications menu.
2. Enter your instance's public IP address in the Host Name (or IP address)
field.
3. Keep 22 as the Port value and SSH as the connection type.
4. Click Open to connect to your instance using SSH.
5. Click Accept when prompted to add the instance's public key to your
workstation's known hosts.
6. Enter your username when prompted for the login as value.
7. Enter the user's password when prompted and press ENTER to log in.

8. View the active user information in your SSH session.
```bash
$ whoami
Connect to an Instance Using SSH Keys
```
1. Enter your instance's public IP address in the Host Name (or IP address)
field.
2. Keep 22 as the Port and SSH as the connection type.
3. Expand the SSH group on the main navigation menu to access additional
connection options.
4. Expand the Auth group and select Credentials from the list of options.
5. Click Browse within the Private key file for authentication field to load
your private key.
6. Click Data within the Connection group and enter the default instance
username in the Auto-login username field to use with your SSH key.
7. Navigate to Session on the main navigation menu and enter a new
session name in the Saved Sessions field.
8. Click Save to store your SSH key, user, and the instance IP configurations.
9. Click Open to connect to the instance using the SSH key session
information.
10. Click Accept when prompted to add the instance's public key to your
workstation's known hosts.
11. View the active user information in your SSH session.
```bash
$ whoami

OpenSSH
Connect to your Vultr VX1™ Cloud Compute instance using OpenSSH with
either default user credentials or SSH keys for secure access.
```

How To Connect to a Vultr VX1™
Cloud Compute Instance Using SSH
Introduction
OpenSSH is a secure protocol used to connect to remote servers through
encrypted SSH sessions. Vultr VX1™ Cloud Compute instances include OpenSSH
by default, allowing you to log in and manage your server securely.
Follow this guide to connect to a Vultr VX1™ Cloud Compute instance using SSH
on your workstation.
Connect to an Instance Using the Default
User Credentials
1. Open your instance's management page in the Vultr Console.
2. Note the default credentials within the Overview tab and copy the user
password to your clipboard.
3. Open a new terminal or command prompt application on your workstation.
4. Connect to your Vultr VX1™ Cloud Compute instance using SSH.
```bash
$ ssh username@SERVER-IP
```
5. Enter yes and press ENTER when prompted to add the instance's public
key to your known hosts.
The authenticity of host '192.0.2.18 (192.0.2.18)' can't be established.
ED25519 key fingerprint is SHA256:gTAOuCiCa3Us4tpVaVHVk9d3qOjKrsqXPOsAFQbB8xw.

This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])?
6. Enter your instance user's password when prompted and press ENTER to
log in.
username@SERVER-IP's password:
7. View the active user in your SSH session.
```bash
$ whoami
Connect to an Instance Using SSH Keys
```
Note
Generate an SSH key on your workstation and add it to your instance during
deployment. Adding an SSH key using the Vultr Console after deployment will
result in data loss and wipe your instance to install the new key.
1. Open a new terminal or command prompt application on your workstation.
2. Connect to your Vultr VX1™ Cloud Compute instance using a specific SSH
key on your workstation.
```bash
$ ssh -i /path/to/private/key username@SERVER-IP
```
3. Enter yes and press ENTER when prompted to add the instance's public
key to your known hosts.
The authenticity of host '192.0.2.18 (192.0.2.18)' can't be established.
ED25519 key fingerprint is SHA256:gTAOuCiCa3Us4tpVaVHVk9d3qOjKrsqXPOsAFQbB8xw.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes

4. View the active user in your SSH session.
```bash
$ whoami
```

Vultr Console
Access and manage your Vultr VX1™ Cloud Compute instance directly
through the web-based Vultr Console, even without SSH access.

How to Connect to a Vultr VX1™
Cloud Compute Instance Using the
Vultr Console
Introduction
Vultr Console is a web-based noVNC terminal that provides direct access to your
instance. You can run commands, manage services, and troubleshoot
configuration issues even if SSH is unavailable. The console also supports
features like clipboard sharing, a virtual keyboard, and special key combinations
such as CTRL +ALT +DEL .
Follow this guide to connect to a Vultr VX1™ Cloud Compute instance using the
Vultr Console.
Note
Enable pop-ups in your web browser settings to access the Vultr Console.
1. Open your instance's management page.
2. Find the default credentials in the Overview tab and copy the user
password to your clipboard.
3. Find and click View Console on the top-right navigation menu to open the
Vultr Console.
4. Enter your default username and press ENTER when prompted.
5. Find and click Send Clipboard on the list of control bar options to paste
the user password in your Vultr Console session.
6. Press ENTER to log in to the instance.

Features
Provides an overview of the key capabilities and distinguishing attributes
of Vultr's cloud infrastructure services.

DDoS Protection
Enable DDoS protection on your Vultr VX1™ Cloud Compute instance
using the Customer Portal or API for improved security and uptime.

How to Enable DDoS Protection on
a Vultr VX1™ Cloud Compute
Instance
Introduction
Distributed Denial of Service (DDoS) protection enables traffic monitoring and
prevents potential DDoS attacks to an instance. It activates a set of tools that
detect and block network flooding attempts, ensuring the instance remains
active and operational.
Follow this guide to enable DDoS protection on a Vultr VX1™ Cloud Compute
instance using the Vultr Console, or API.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr VX1™ Cloud Compute instance to open its
management page.
3. Navigate to the DDoS tab.
4. Click Enable DDoS Protection.
5. Click Enable DDoS Protection in the confirmation prompt to enable
DDoS protection on your instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.

```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Instance endpoint to enable DDoS
protection on the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "ddos_protection": true
  }'
If successful, you receive a 200  HTTP status code response.

Cloud-Init
Update Cloud-Init user data on your Vultr VX1™ Cloud Compute instance
using the Customer Portal or API to automate configuration.

Cloud-Init Product Documentation
```
Cloud-Init Product Documentation
How to Update Cloud-Init User Data
on a Vultr VX1™ Cloud Compute
Instance
Introduction
Cloud-Init enables the automatic initialization and configuration of instances
during the initial boot phase. It runs user data scripts to customize an instance,
install applications, and configure specific packages or services.
Follow this guide to update Cloud-Init user data on a Vultr VX1™ Cloud Compute
instance using the Vultr Console, or API.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr VX1™ Cloud Compute instance to open its
management page.
3. Navigate to the User-Data tab.
4. Enter your script or cloud config in the Cloud-Init User-Data field.
5. Click Update to apply the changes.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
Cloud-Init Product Documentation
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Instance endpoint to update the
instance's Cloud-Init user data.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "user_data" : "<cloud-init-data>"
  }'
If successful, you receive a 200  status code response.
```

Management
Tools and features for managing your Vultr infrastructure, including
billing, access controls, and account settings.

Tags
Add and manage tags on your Vultr VX1™ Cloud Compute instance using
the Customer Portal or API for better organization.

How to Add Tags on a Vultr VX1™
Cloud Compute Instance
Introduction
Tagging allows you to assign specific labels, known as tags, to an instance for
improved identification in your Vultr account. Tags consist of multiple characters
that help identify, organize, and manage instances in your Vultr account.
Follow this guide to add tags on a Vultr VX1™ Cloud Compute instance using
the Vultr Console, or API.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr VX1™ Cloud Compute instance to open its
management page.
3. Navigate to the Tags tab.
4. Enter a new tag in the Add Tag field and click Add to apply the new tag.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Instance endpoint to add tags to the
instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "tags" : ["tag1", "tag2"]
  }'
If successful, you receive a 200  status code response.

Custom ISO
Attach and boot custom ISO images on your Vultr VX1™ Cloud Compute
instance using the Customer Portal or API for flexible OS installation.
```

How to Attach a Custom ISO to a
Vultr VX1™ Cloud Compute
Instance
Introduction
ISO images allow you to install a specific operating system on a Vultr VX1™
Cloud Compute instance. Custom ISOs enable you to deploy operating systems
not available in the default Vultr installer list. They are useful for creating
tailored environments or booting into specialized modes, such as rescue and
recovery environments.
Follow this guide to attach a custom ISO to a Vultr VX1™ Cloud Compute
instance using the Vultr Console, or API.
Warning
Installing a custom ISO on a Vultr VX1™ Cloud Compute instance disables the
default user credentials listed in your instance's management page.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr VX1™ Cloud Compute instance to open its
management page.
3. Navigate to the Settings tab.
4. Find and click Custom ISO on the left navigation menu.
5. Select a custom ISO available in your Vultr account or click the ISO
Library drop-down to select from a list of public ISOs.
6. Click Attach ISO and Reboot to attach the ISO to your instance.

Vultr API
1. Send a GET  request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List ISOs endpoint and note your target ISO ID.
```bash
$ curl "https://api.vultr.com/v2/iso" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Attach ISO to Instance endpoint to attach
the ISO to your target instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/iso/
attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "iso_id" : "<iso-id>"
  }'
If successful, you receive a 200  status code response.
```

Delete
Delete a Vultr VX1™ Cloud Compute instance using the Customer Portal
or API while preserving any attached bootable Block Storage volumes.

How to Delete a Vultr VX1™ Cloud
Compute Instance
Introduction
Deleting a VX1™ Cloud Compute instance removes the server and returns its IP
address to the Vultr IP pool. However, if the instance is booted from a Vultr
Block Storage (VBS) bootable volume, the data stored on that volume remains
intact.
Follow this guide to delete a Vultr VX1™ Cloud Compute instance using the Vultr
Console, or API.
Note
Deleting an Vultr VX1™ instance that is booted from a Vultr Block Storage
(VBS) bootable volume does not delete the underlying VBS volume. You must
manually remove the bootable VBS volume from the Block Storage section if
you wish to delete it.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr VX1™ Cloud Compute instance to open its
management page.
3. Click Destroy Server on the top-right navigation menu.
4. Check the confirmation prompt and click Destroy Server to apply
changes.

Vultr API
1. Send a GET  request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete Instance endpoint to delete the
instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```

Monitor
Monitor your Vultr VX1™ Cloud Compute instance using the Customer
Portal or API to track performance, bandwidth, and real-time resource
utilization.

How to Monitor a Vultr VX1 Cloud
Compute Instance
Introduction
Monitoring a VX1™ Cloud Compute instance helps you track its performance,
health, and resource utilization. It provides detailed insights into metrics such
as vCPU usage, disk operations, and bandwidth consumption, allowing you to
analyze trends and optimize your instance’s performance.
Follow this guide to monitor a Vultr VX1™ Cloud Compute instance using the
Vultr Console or API.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr VX1™ Cloud Compute instance to open its
management page.
3. Navigate to the Usage Graphs tab to monitor the instance's usage
statistics.
4. Monitor the instance's bandwidth usage statistics within the Monthly
Bandwidth section.
5. Monitor the instance's performance statistics within the Server
Monitors section.
6. Click the Range drop-down to select a specific timeframe and view the
monitoring information in the following categories:
- vCPU Usage: Displays the vCPU usage statistics.
- Disk Operations: Displays the read and write operations per second
on the primary storage disk.
- Network: Displays the instance's networking statistics in bytes.

Vultr API
1. Send a GET  request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Instance Bandwidth endpoint to fetch the
instance's bandwidth usage statistics.
```bash
$ curl "https://api.vultr.com/v2/instances/
6616e66d-38a0-4a55-8283-1f9d85ea5467/bandwidth" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"

Restart
Restart your Vultr VX1™ Cloud Compute instance through the Customer
Portal or API to reinitialize the system without affecting stored data.
```

How to Restart a Vultr VX1™ Cloud
Compute Instance
Introduction
Restarting an instance performs a hard reboot that stops all running processes
and reinitializes the operating system. This action does not affect the instance’s
data or file system. Restarting is useful for applying system updates,
configuration changes, or recovering from temporary service issues.
Follow this guide to restart a Vultr VX1™ Cloud Compute instance using the
Vultr Console, or API.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr VX1™ Cloud Compute instance to open its
management page.
3. Click Server Restart on the top-right navigation menu to restart your
server.
4. Click Restart Server in the confirmation prompt to apply changes.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Reboot Instances endpoint to restart the
instance.
```bash
$ curl "https://api.vultr.com/v2/instances/reboot" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "instance_ids" : [
      "instance_id"
    ]
  }'
If successful, you receive a 200 HTTP response.

Stop
Stop your Vultr VX1™ Cloud Compute instance using the Customer Portal
or API to perform a clean shutdown while preserving all data.
```

How to Stop a Vultr VX1™ Cloud
Compute Instance
Introduction
Stopping an instance performs a graceful shutdown, halting all running
processes and disabling network connectivity until it is restarted. The instance’s
data and configuration remain intact. However, billing continues while the
instance is stopped unless it is deleted.
Follow this guide to stop a Vultr VX1™ Cloud Compute instance using the Vultr
Console, or API.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr VX1™ Cloud Compute instance to open its
management page.
3. Click Stop Server on the top-right navigation menu to stop the instance.
4. In the confirmation dialog, click Stop Server again to confirm.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Halt Instances endpoint to stop the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/halt" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
     "instance_ids" : [
       "instance_id"
     ]
   }'
If successful, you receive a 200 HTTP response.

Networking
Manage your Vultr infrastructures connectivity with advanced networking
features, configurations, and security controls.
```

Compute instance using the Customer Portal or API.

How to Add IPv4 Addresses on a
Vultr VX1™ Cloud Compute
Instance
Introduction
A public IPv4 address is automatically assigned to an instance upon
deployment, unless disabled by default. You can attach multiple IPv4 addresses
to the instance to enable external network connections. Additional addresses
can also be used for tasks such as IP forwarding, static and dynamic routing.
Follow this guide to add the IPv4 information on a Vultr VX1™ Cloud Compute
instance using the Vultr Console, or API.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr VX1™ Cloud Compute instance to open its
management page.
3. Navigate to the Settings tab.
4. Click IPv4 on the left navigation menu to view the instance's public IPv4
network information.
5. Click Add Another IPv4 Address to attach an additional public IP
address to the instance.
6. Check the confirmation prompt and click Add IPv4 Address to attach the
new public IP address and restart your instance.
7. Click the default IPv4 reverse DNS value and replace it with a custom value
to enable reverse DNS on the instance.

Vultr API
1. Send a GET  request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Instance IPv4 Information endpoint to
view the instance's IPv4 information.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv4" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Create IPv4 endpoint to attach a new IPv4
address to the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv4" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "reboot" : true
  }'
```
4. Send a POST  request to the Create Instance Reverse IPv4 endpoint to
enable reverse DNS on the instance.

```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv4/reverse" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
"ip" : "<ipv4-address>",
"reverse" : "<domain>"
}'

IPv6
Add and manage IPv6 addresses on a Vultr VX1™ Cloud Compute
instance using the Customer Portal or API.
```

How to Add IPv6 Addresses on a
Vultr VX1™ Cloud Compute
Instance
Introduction
Vultr VX1™ Cloud Compute instances support IPv6, but the platform does not
assign a public IPv6 address unless you enable it during instance deployment.
After enabling IPv6, you can create additional IPv6 addresses, attach them to
your instance, and configure reverse DNS records.
Follow this guide to add IPv6 addresses to a Vultr VX1™ Cloud Compute
instance using the Vultr Console or API.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr VX1™ Cloud Compute instance to open the
management page.
3. Navigate to the Settings tab.
4. Click IPv6 on the left navigation menu.
5. Click Assign IPv6 Network to allocate an IPv6 subnet if your instance
does not have one.
6. Return to the main navigation menu and click Network.
7. Click Reserved IPs.
8. Click Add Reserved IP.
9. Select the location, choose IPv6 as the type, enter a label, and click Add
to create the reserved IPv6 address.
10. Select the newly created reserved IPv6 address from the list.
11. Under Attach to Server, select your VX1™ instance and click Attach to
bind the IPv6 address to the server.

12. To configure reverse DNS, return to your instance information page, open
Settings, click IPv6, and edit the Reverse DNS entry for the attached IPv6
address.
Vultr API
1. Send a GET  request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Get Instance IPv6 Information endpoint to verify
that IPv6 is enabled.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv6" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
If IPv6 is disabled, send a PATCH  request to the Update Instance endpoint to
enable it.
```
```console
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
```
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "enable_ipv6": true
  }'
After it is enabled, it assigns an IPv6 address to the instance
3. Send a POST  request to the Create Reserved IP endpoint to create a new
IPv6 address.
```bash
$ curl "https://api.vultr.com/v2/reserved-ips" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "region": "ewr",
    "ip_type": "v6",
    "label": "Example Reserved IPv6"
  }'
If successful, you receive a 200 HTTP response with the reserved IP
information.
```
4. Send a POST  request to the Attach Reserved IP endpoint to attach the new
IPv6 address to your instance.
```bash
$ curl "https://api.vultr.com/v2/reserved-ips/{reserved-ip-id}/attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "instance_id": "{instance-id}"
  }'
```
5. Send a GET  request to the Get Instance endpoint to verify that your
instance now lists the new IPv6 address.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
6. Send a POST request to the Create Instance Reverse IPv6 endpoint to
create a reverse DNS record.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv6/reverse" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
"ip": "<ipv6-address>",
"reverse": "<domain>"
}'

VPC
Attach a secure VPC network to a Vultr VX1™ Cloud Compute instance via
Portal or API.
```

How to Attach a VPC Network to a
Vultr VX1™ Cloud Compute
Instance
Introduction
A Virtual Private Cloud (VPC) network creates a secure and isolated private
networking interface to enable connections to other instances attached to the
same network. You can attach multiple instances to the VPC network to enable
secure connections between a Vultr VX1 Cloud Compute instance and other
instances attached to the same VPC network.
Follow this guide to attach a VPC network to a Vultr VX1™ Cloud Compute
instance using the Vultr Console, or API.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr VX1™ Cloud Compute instance to open its
management page.
3. Navigate to the Settings tab.
4. Click IPv4 on the left navigation menu.
5. Click Enable VPC.
6. Click Enable VPC again in the confirmation prompt. This action attaches
your instance to the default VPC in the same region. If no VPC exists in that
region, the platform creates a new VPC automatically and attaches your
instance to it..
7. To attach multiple VPC networks to the same instance, use the drop-down
menu on the same page to select additional VPCs. Ensure that the VPC
subnets do not overlap, or the attachment will cause routing conflicts.

Vultr API
1. Send a GET  request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List VPCs endpoint to list all available VPCs and
note the target VPC network ID.
```bash
$ curl "https://api.vultr.com/v2/vpcs" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Attach VPC to Instance endpoint to attach
the VPC network to the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
vpcs/attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "vpc_id": "<vpc-id>"
  }'
If successful, you receive a 200 HTTP response.

Reserved IPs
Attach reserved public IPs to a Vultr VX1™ Cloud Compute instance via
Portal or API.
```

How to Attach Reserved IPs to a
Vultr VX1™ Cloud Compute
Instance
Introduction
Reserved IPs let you reserve specific public IP addresses that you can attach to
a Vultr VX1™ Cloud Compute instance. You can attach multiple reserved IPs to
the same instance to support advanced networking tasks such as routing, load
balancing, and IP forwarding.
Follow this guide to attach reserved IPs to a Vultr VX1™ Cloud Compute
instance using the Vultr Console, or API.
Vultr Console
1. Navigate to Products, expand the Network section, and click Reserved
IPs.
2. Click your target reserved IP to open its management page.
3. Select your target Vultr VX1™ Cloud Compute instance from the Attach to
Server drop-down menu.
4. Click Attach to apply the reserved IP to the instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Reserved IPs endpoint and note the target
reserved IP's ID.
```bash
$ curl "https://api.vultr.com/v2/reserved-ips" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Attach Reserved IP endpoint to attach the
reserved IP to the instance.
```bash
$ curl "https://api.vultr.com/v2/reserved-ips/{reserved-ip}/
attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "instance_id" : "<instance-id>"
  }'

Enable Firewall
```
Apply a Vultr Firewall group to secure a VX1™ Cloud Compute instance
via Portal or API.

How to Enable a Vultr Firewall
Group on a Vultr VX1™ Cloud
Compute Instance
Introduction
Vultr Firewall groups let you create rules that control and filter incoming
network traffic to your instance. These rules define which ports, protocols, and
services you allow or block, improving the security of your Vultr VX1™ Cloud
Compute instance.
Follow this guide to enable a Vultr Firewall group on a Vultr VX1™ Cloud
Compute instance using the Vultr Console, or API.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr VX1™ Cloud Compute instance to open its
management page.
3. Navigate to the Settings tab.
4. Click Firewall on the left navigation menu.
5. Open the Firewall drop-down menu and select the firewall group you want
to apply.
6. Click Update Firewall Group to enable the firewall group on the instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.

```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Firewall Groups endpoint and note the ID
of the firewall group you want to apply.
```bash
$ curl "https://api.vultr.com/v2/firewalls" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PATCH  request to the Update Instance endpoint to attach a firewall
group to the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "firewall_group_id" : "<firewall-id>"
  }'
If successful, you receive a 200 HTTP response.

Optimized Cloud Compute
High-performance cloud compute instances optimized for specific
workloads with enhanced resources and specialized configurations.
```

Provisioning
A guide explaining how to deploy and set up Vultr Optimized Cloud
Compute instances for your workloads.

How to Provision Vultr Optimized
Cloud Compute Instances
Introduction
Vultr Optimized Cloud Compute instances are dedicated virtual machines
designed for demanding business applications such as production websites, CI/
CD, video transcoding, and large databases. Vultr Optimized Cloud Compute
instances are capable of running resource-intensive applications that require
specific CPU, memory or storage resources.
Follow this guide to provision Vultr Optimized Cloud Compute instances using
the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click Deploy.
3. Choose Dedicated CPU as the instance type.
4. Select your desired Vultr location to deploy the instance to.
5. Select a plan category from the sidebar:
- VX1: Provide the best price-to-performance for efficient compute
workloads.
- General Purpose: Support resource-demanding business
applications such as production websites, CI/CD, video transcoding,
and large databases.
- CPU Optimized: Support compute-bound applications that require
proportionally more CPU than RAM (memory) and storage.

- Memory Optimized: Support memory-bound applications that
require more RAM than CPU and storage.
- Storage Optimized: Provide more NVMe SSD storage to balance the
available CPU and RAM.
6. Select a plan from the available options based on your vCPU, memory,
storage, and bandwidth requirements.
7. Click Configure Software.
8. Select a cloud image to install on the instance based on the following
options:
- Operating System: Installs a fresh operating system image on the
instance.
- Marketplace Apps: Installs a prebuilt software stack or application
and the recommended operating system image on the instance.
- ISO/iPXE: Boots a specific ISO available or iPXE-compatible image on
the instance.
- ISO Library: Installs a specific ISO image from the Vultr ISOs library.
- Backup: Recovers a specific backup available in your Vultr account to
the instance.
- Snapshot: Installs a specific snapshot available in your Vultr account
to the instance.
9. Select optional Server Settings to apply on the instance.
- SSH Keys: Installs a specific SSH key on the instance.
- Startup Script: Enables a startup script to execute at deployment or
a PXE script to automate the operating system installation.
- Firewall Group: Activates a Vultr Firewall group to filter incoming
network traffic on the instance.
10. Enter a new hostname in the Server Hostname field and a descriptive
label in the Server Label field to identify the instance.

11. Configure Additional Features for the instance.
- Instance Connectivity: Select how the instance connects to the
internet.
▪ Instance(s) with Public IP: Assigns public IP addresses directly
to the instance. Under Instance Address, Public IPv4 is
enabled by default. Select Public IPv6 to enable IPv6
addressing. After selecting IPv6, you can optionally deselect
Public IPv4 to create an IPv6-only instance.
▪ Private Instance(s) behind NAT Gateway: Routes internet
traffic through a NAT Gateway in a Virtual Private Cloud (VPC)
Network. Select an existing VPC Network with a NAT Gateway or
click Add VPC Network to create a new one.
- VPC Network: Connects the instance to a VPC Network in the current
location.
- Automatic Backups: Automatically creates backups for data
recovery in case of instance failures.
- DDoS Protection: Prevents potential Distributed Denial of Service
(DDoS) attacks on the instance.
- Limited User Login: Creates a linuxuser non-root user with sudo
privileges as the default user account instead of root .
- Cloud-Init User Data: Enables Cloud-Init user data to initialize and
customize the instance at boot.
12. Click Deploy to provision the instance.
Vultr API
1. Send a POST request to the Create Instance endpoint to create a new
Vultr Optimized Cloud Compute instance. Replace VULTR_LOCATION ,
INSTANCE_PLAN , OS_ID , INSTANCE_LABEL , and HOSTNAME with your target values.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \

-H "Content-Type: application/json" \
--data '{
    "region" : "VULTR_LOCATION",
    "plan" : "INSTANCE_PLAN",
    "os_id" : OS_ID,
    "label" : "INSTANCE_LABEL",
    "hostname": "HOSTNAME"
  }'
```
Visit the Create Instance API page to view additional attributes you can
apply on the Vultr Optimized Cloud Compute instance.
2. Send a GET  request to the List Instances endpoint to list all available
instances.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. Create a new Vultr Optimized Cloud Compute instance. Replace
VULTR_LOCATION , INSTANCE_PLAN , OS_ID , INSTANCE_LABEL , and HOSTNAME  with your
target values.
```bash
$ vultr-cli instance create --region VULTR_LOCATION --plan
INSTANCE_PLAN --os OS_ID --label INSTANCE_LABEL --host
HOSTNAME
```
Run vultr-cli instance create --help  to view additional options you can apply
on the Vultr Optimized Cloud Compute instance.
2. List all available instances.
```bash
$ vultr-cli instance list
```
Terraform
1. Ensure the Vultr Terraform provider is configured in your Terraform project.
2. Define the Optimized Cloud Compute instance in your Terraform
configuration file.
```hcl
terraform {
required_providers {
vultr = {
source = "vultr/vultr"
version = "~> 2.26"
}
}
}
provider "vultr" {}
resource "vultr_instance" "occ" {
label = "occ-instance-1"
hostname = "occ-instance-1"
region = "del"              # change to your target
region (such as ewr, ams, sgp)
plan = "vhp-2c-4gb"       # OCC plan code
os_id = 2284               # Ubuntu 24.04 LTS x64
enable_ipv6 = true
}
output "public_ip" {
value = vultr_instance.occ.main_ip
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Connection
Establish connectivity to your Vultr resources through various network
protocols and access methods.

OpenSSH
A secure protocol for remote server access that comes pre-installed on
Vultr instances, allowing encrypted connections from your local machine.

How To Connect to a Vultr
Optimized Cloud Compute Instance
Using SSH
Introduction
OpenSSH is a connection protocol that enables SSH access to an instance. It is
pre-installed and active on Vultr Optimized Cloud Compute instances by default
to enable secure connections.
Follow this guide to connect to a Vultr Optimized Cloud Compute instance using
SSH on your workstation.
Connect to an Instance Using the Default
User Credentials
1. Open your instance's management page.
2. Note the default credentials within the Overview tab and copy the user
password to your clipboard.
3. Open a new terminal or command prompt application on your workstation.
4. Connect to your Vultr Optimized Cloud Compute instance using SSH.
```bash
$ ssh username@SERVER-IP
```
5. Enter yes and press ENTER when prompted to add the instance's public key
to your known hosts.

The authenticity of host '192.0.2.123 (192.0.2.123)' can't be established.
ED25519 key fingerprint is SHA256:gTAOuCiCa3Us4tpVaVHVk9d3qOjKrsqXPOsAFQbB8xw.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])?
6. Enter your instance user's password when prompted and press ENTER to log
in.
username@SERVER-IP's password:
7. View the active user in your SSH session.
```bash
$ whoami
Connect to an Instance Using SSH Keys
```
Note
Generate an SSH key on your workstation and add it to your instance during
deployment. Adding an SSH key using the Vultr Console after deployment will
result in data loss and wipe your instance to install the new key.
1. Open a new terminal or command prompt application on your workstation.
2. Connect to your Vultr Optimized Cloud Compute instance using a specific
SSH key on your workstation.
```bash
$ ssh -i /path/to/private/key username@SERVER-IP
```
3. Enter yes and press ENTER when prompted to add the instance's public key
to your known hosts.

The authenticity of host '192.0.2.123 (192.0.2.123)' can't be established.
ED25519 key fingerprint is SHA256:gTAOuCiCa3Us4tpVaVHVk9d3qOjKrsqXPOsAFQbB8xw.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
4. View the active user in your SSH session.
```bash
$ whoami

PuTTY
A free SSH client for Windows that allows secure remote connections to
Vultr instances using terminal access.
```

How to Connect to a Vultr
Optimized Cloud Compute Instance
Using PuTTY
Introduction
PuTTY is an open-source terminal emulator and SSH client for Windows
workstations. It provides a user-friendly interface and terminal to connect to
instances using SSH. PuTTY supports both password-based authentication and
SSH keys for secure connections to an instance.
Follow this guide to connect to a Vultr Optimized Cloud Compute instance using
PuTTY on Windows.
Connect to an Instance Using the Default
User Credentials
1. Open PuTTY from your applications menu.
2. Enter your instance's public IP address in the Host Name (or IP address)
field.
3. Keep 22 as the Port value and SSH as the connection type.
4. Click Open to connect to your instance using SSH.
5. Click Accept when prompted to add the instance's public key to your
workstation's known hosts.
6. Enter your username when prompted for the login as value.
7. Enter the user's password when prompted and press Enter to log in.

8. View the active user information in your SSH session.
```bash
$ whoami
Connect to an Instance Using SSH Keys
```
1. Enter your instance's public IP address in the Host Name (or IP address)
field.
2. Keep 22 as the Port and SSH as the connection type.
3. Expand the SSH group on the main navigation menu to access additional
connection options.
4. Expand the Auth group and select Credentials from the list of options.
5. Click Browse within the Private key file for authentication field to load
your private key.
6. Click Data within the Connection group and enter the default instance
username in the Auto-login username field to use with your SSH key.
7. Navigate to Session on the main navigation menu and enter a new
session name in the Saved Sessions field.
8. Click Save to store your SSH key, user, and the instance IP configurations.
9. Click Open to connect to the instance using the SSH key session
information.
10. Click Accept when prompted to add the instance's public key to your
workstation's known hosts.
11. View the active user information in your SSH session.
```bash
$ whoami
```

Vultr Console
Access your Vultr instance directly through the web browser without SSH
clients using the built-in console interface.

How to Connect to a Vultr
Optimized Cloud Compute Instance
Using the Vultr Console
Introduction
Vultr Console is a noVNC terminal that provides direct access to an instance's
console. You can run commands, install applications and manage processes
through the Vultr Console. Additionally, it offers multiple features like clipboard
sharing, a virtual keyboard, and special commands such as CTRL ALT DEL to
manage an instance.
Follow this guide to connect to a Vultr Optimized Cloud Compute instance using
the Vultr Console.
Note
Enable pop-ups in your web browser settings to access the Vultr Console.
1. Open your instance's management page.
2. Find the default credentials in the Overview tab and copy the user
password to your clipboard.
3. Find and click View Console on the top-right navigation menu to open the
Vultr Console.
4. Enter your default username and press ENTER when prompted.
5. Find and click Send Clipboard on the list of control bar options to paste
the user password in your Vultr Console session.
6. Press ENTER to log in to the instance.

Features
Provides an overview of the key capabilities and distinguishing attributes
of Vultr's cloud infrastructure services.

Auto Backups
A service that automatically creates and stores regular backups of your
Vultr instance for data protection and recovery.

How to Enable Automatic Backups
on a Vultr Optimized Cloud
Compute Instance
Introduction
Automatic Backups allow you to create full backups of your instance's data and
file system on a scheduled basis, ensuring recovery in case of unexpected
failures. These backups follow specific schedules and retention policies to
ensure your instance is securely backed up in your Vultr account
Follow this guide to enable automatic backups on a Vultr Optimized Cloud
Compute instance using the Vultr Console, API, or Terraform.
Vultr Console
1. Navigate to Products and click Compute
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Navigate to the Backups tab.
4. Click Enable Backups to turn on automatic backups.
5. Click Enable Backups in the confirmation prompt to enable automatic
backups.
6. Click the Schedule Backups drop-down to choose a backup schedule.
7. Click Update to create automatic backups based on your selection.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.

```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Instance endpoint to update the
instance and enable automatic backups.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "backups" : "enabled"
  }'
```
3. Send a POST  request to the Set Instance Backup Schedule endpoint to
create a new automatic backups schedule.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
backup-schedule" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "type": "daily",
    "hour": 10,
    "dow": 1,
    "dom": 1
  }'
```
Visit the Set Instance Backup Schedule API page to view additional
backup schedule attributes.

Terraform
1. Open your Terraform configuration for the existing Optimized Cloud
Compute instance.
2. Enable backups and define a schedule in the configuration.
```hcl
resource "vultr_instance" "occ" {
label = "occ-instance-1"
hostname = "occ-instance-1"
region = "del"
plan = "vhp-2c-4gb"
os_id = 2284
backups = "enabled"
backups_schedule {
type = "daily" # daily | weekly | monthly
hour = 10 # UTC hour (0-23)
dow = 1 # used for weekly
dom = 1 # used for monthly
}
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Cloud-Init
A guide explaining how to modify the Cloud-Init user data on your Vultr
Optimized Cloud Compute instance after deployment.

Cloud-Init Product Documentation
Cloud-Init Product Documentation
How to Update Cloud-Init User Data
on a Vultr Optimized Cloud
Compute Instance
Introduction
Cloud-Init enables the automatic initialization and configuration of instances
during the initial boot phase. It runs user data scripts to customize an instance,
install applications, and configure specific packages or services.
Follow this guide to update Cloud-Init user data on a Vultr Optimized Cloud
Compute instance using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Navigate to the User-Data tab.
4. Enter your script or cloud config in the Cloud-Init User-Data field.
5. Click Update to apply the changes.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
Cloud-Init Product Documentation
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Instance endpoint to update the
instance's Cloud-Init user data.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "user_data" : "<cloud-init-data>",
  }'
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. Upload new Cloud-Init user data to the instance from a file on your
workstation.
```bash
$ vultr-cli instance user-data set <instance-id> --userdata
"<script-path>"

Cloud-Init Product Documentation
```
Terraform
Cloud-Init user data can only be set during instance creation in Terraform and
cannot be updated on an existing instance without recreating it.
1. Open your Terraform configuration for the new Optimized Cloud Compute
instance.
2. Add the user_data argument to the instance resource to run a script at first
boot.
```hcl
resource "vultr_instance" "occ" {
```
# ...existing fields (region, plan, os_id, label, etc.)
user_data = <<-EOT
#!/bin/bash
apt-get update -y
apt-get install -y nginx
systemctl enable --now nginx
EOT
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

DDoS Protection
Learn how to enable DDoS protection on your Vultr Optimized Cloud
Compute instance to safeguard against distributed denial-of-service
attacks.

How to Enable DDoS Protection on
a Vultr Optimized Cloud Compute
Instance
Introduction
Distributed Denial of Service (DDoS) protection enables traffic monitoring and
prevents potential DDoS attacks to an instance. It activates a set of tools that
detect and block network flooding attempts, ensuring the instance remains
active and operational.
Follow this guide to enable DDoS protection on a Vultr Optimized Cloud
Compute instance using the Vultr Console, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Navigate to the DDoS tab.
4. Click Enable DDoS Protection.
5. Click Enable DDoS Protection in the confirmation prompt to enable
DDoS protection on your instance.
Terraform
1. Open your Terraform configuration for the existing Optimized Cloud
Compute instance.
2. Enable DDoS protection in the instance resource.

```hcl
resource "vultr_instance" "occ" {
```
    # ...existing fields (region, plan, os_id, label, etc.)
ddos_protection = true
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Snapshots
A feature that allows you to create point-in-time copies of your Vultr
instances for backup, cloning, or recovery purposes.

How to Create Snapshots on a Vultr
Optimized Cloud Compute Instance
Introduction
A snapshot is a point-in-time copy of an instance's state, including its entire file
system and disk contents. Snapshots offer a quick backup solution for
instances, making it easier to restore data in case of unexpected failures or
data loss.
Follow this guide to create snapshots on a Vultr Optimized Cloud Compute
instance using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click the target Vultr Optimized Cloud Compute instance to open its
management page.
3. Navigate to the Snapshots tab.
4. Enter a new descriptive label in the Label field and click Create
Snapshot to take a new snapshot of your instance. Snapshot creation can
take 20 to 30 minutes depending on the instance size.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Create Snapshot endpoint to create a new
snapshot of the instance.
```bash
$ curl "https://api.vultr.com/v2/snapshots" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "instance_id" : "<instance-id>",
    "description" : "<label>"
  }'
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. Create a new snapshot of the instance.
```bash
$ vultr-cli snapshot create --id <instance-id>
```

Management
Tools and features for managing your Vultr infrastructure, including
billing, access controls, and account settings.

Change Hostname
Learn how to modify the hostname on your Vultr Optimized Cloud
Compute instance.

How to Change the Hostname on a
Vultr Optimized Cloud Compute
Instance
Introduction
Changing the hostname on an instance modifies the default server
configuration and reinstalls the operating system. This operation may result into
data loss when the instance is reinstalled to apply the new hostname.
Follow this guide to change the hostname on a Vultr Optimized Cloud Compute
instance using the Vultr Console, or Terraform.
Warning
Changing the hostname reinstalls the operating system and wipes all the data
on your server.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Navigate to the Settings tab.
4. Find and click Change Hostname on the left navigation menu.
5. Replace the existing value with your new hostname.
6. Click Reinstall to change your instance hostname.
7. Check the confirmation prompt and click Change Hostname to apply the
new hostname.

Terraform
1. Open your Terraform configuration for the existing Optimized Cloud
Compute instance.
2. Update the hostname value in the instance resource.
```hcl
resource "vultr_instance" "occ" {
```
# ...existing fields (region, plan, os_id, label, etc.)
hostname = "new-hostname"
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 1 destroyed.

Change OS
A guide explaining how to replace the operating system on your Vultr
Optimized Cloud Compute instance.

How to Change the Operating
System on a Vultr Optimized Cloud
Compute Instance
Introduction
Changing the instance operating system wipes all data on your server and
installs a new file system. This is important when changing the default
operating system while preserving the instance's IP and networking information.
Follow this guide to change the operating system on a Vultr Optimized Cloud
Compute instance using the Vultr Console, API, CLI, or Terraform.
Warning
Changing to a different operating system wipes all the data on your server.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Navigate to the Settings tab.
4. Find and click Change OS on the left navigation menu.
5. Click the Choose new OS drop-down and select a new operating system
to install on your instance.
6. Click Change OS to change the instance operating system.
7. Check the Change OS confirmation prompt and click Change OS to apply
the new instance changes.

Vultr API
1. Send a GET  request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List OS endpoint to view all available operating
systems and note the target OS ID.
```bash
$ curl "https://api.vultr.com/v2/os" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PATCH  request to the Update Instance endpoint with a new os_id
value to change the instance's operating system.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
  "os_id" : "new-instance-os_id"
}'
```
Vultr CLI
1. List all available instances and note your target instance's ID.

```bash
$ vultr-cli instance list
```
2. List all available operating systems and note the target OS ID.
```bash
$ vultr-cli instance os list <instance-id>
```
3. Change the target instance's operating system.
```bash
$ vultr-cli instance os change <instance-id> --os <os_id>
```
Terraform
1. Open your Terraform configuration for the existing Optimized Cloud
Compute instance.
2. Update the os_id  value in the instance resource to the new operating
system ID.
```hcl
resource "vultr_instance" "occ" {
```
    # ...existing fields (region, plan, label, etc.)
os_id = 1743  # Example: Ubuntu 22.04 LTS x64
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Change Startup Script
Learn how to modify the startup script that runs when your Vultr instance
boots up

How to Change the Startup Script
on a Vultr Optimized Cloud
Compute Instance
Introduction
Startup scripts allow you to automate specific configurations during the
operating system installation. Changing the startup script on an instance wipes
the file system and reinstalls the default operating system.
Follow this guide to change the startup script on a Vultr Optimized Cloud
Compute instance using the Vultr Console, or Terraform.
Warning
Changing the startup script on an instance will wipe all data and reinstall the
operating system.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Navigate to the Settings tab.
4. Find and click Change StartUp Script on the left navigation menu.
5. Click Add Startup Script.
6. Enter a new script name and click the Type drop down to select the script
type.
7. Add your startup script data and click Add Script to apply the script to
your instance.
8. Navigate to Change StartUp Script in your instance settings to verify
that the new script is added.

9. Select the startup script and click Change Startup Script.
10. Check the confirmation prompt and click Change Startup Script to apply
the new script.
Terraform
1. Open your Terraform configuration for the existing Optimized Cloud
Compute instance.
2. Create or reference a vultr_startup_script  resource and attach it to the
instance.
# Create a new startup script
resource "vultr_startup_script" "init" {
name = "init-nginx"
type = "boot"  # boot pxeboot
script = <<-EOT
    #!/bin/bash
    apt-get update -y
    apt-get install -y nginx
    systemctl enable --now nginx
    EOT
}
# Attach the startup script to the instance
resource "vultr_instance" "occ" {
    # ...existing fields (region, plan, os_id, label, etc.)
script_id = vultr_startup_script.init.id
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Custom ISO
A feature that allows you to upload and attach your own ISO image to
Vultr instances for custom operating system installations.

How to Attach a Custom ISO to a
Vultr Optimized Cloud Compute
Instance
Introduction
ISO images allow you to install a specific operating system on an Vultr
Optimized Cloud Compute instance. Custom ISOs enable you to deploy
operating systems not available in the default Vultr installer list. They are useful
for creating tailored environments or booting into specialized modes, such as
rescue and recovery environments.
Follow this guide to attach a custom ISO to a Vultr Optimized Cloud Compute
instance using the Vultr Console, API, CLI, or Terraform.
Warning
Installing a custom ISO on a Vultr Optimized Cloud Compute instance disables
the default user credentials listed in your instance's management page.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Navigate to the Settings tab.
4. Find and click Custom ISO on the left navigation menu.
5. Select a custom ISO available in your Vultr account or click the ISO
Library drop-down to select from a list of public ISOs.
6. Click Attach ISO and Reboot to attach the ISO to your instance.

Vultr API
1. Send a GET  request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List ISOs endpoint and note your target ISO ID.
```bash
$ curl "https://api.vultr.com/v2/iso" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Attach ISO to Instance endpoint to attach
the ISO to your target instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/iso/
attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "iso_id" : "<iso-id>"
  }'
```
Vultr CLI
1. List all available instances and note your target instance's ID.

```bash
$ vultr-cli instance list
```
2. List all available ISO images and note your target ISO's ID.
```bash
$ vultr-cli iso list
```
3. Attach the ISO to your target instance.
$ vultr-cli instance iso attach <instance-id> \
            --iso-id="<iso-id>"
Terraform
1. Open your Terraform configuration for the existing Optimized Cloud
Compute instance.
2. Specify the ISO by its os_id  when defining or rebuilding the instance.
# Example: attach a custom ISO by its ID (replace 159 with
your ISO ID)
resource "vultr_instance" "occ" {
label = "occ-custom-iso"
region = "del"
plan = "vhp-2c-4gb"
os_id = 159                 # 'Custom' ISO type
iso_id = "your-iso-id-here"  # ID of uploaded or
library ISO
hostname = "occ-custom-iso"
}
3. Apply the configuration and observe the following output:

Apply complete! Resources: 0 added, 1 changed, 0 destroyed.
Note
Terraform does not currently support attaching an ISO in-place to a running
instance.
The ISO must be set at create time or during a rebuild, which replaces the
instance and wipes all existing data.

Delete
Learn how to permanently remove a Vultr Optimized Cloud Compute
instance from your account.

How to Delete a Vultr Optimized
Cloud Compute Instance
Introduction
Deleting an instance permanently erases the server's file system and removes
all IP information. This action is irreversible and any data on the instance data is
lost unless a backup or snapshot is available in your Vultr account.
Follow this guide to delete a Vultr Optimized Cloud Compute instance using the
Vultr Console, API, or CLI.
Warning
Deleting an instance is permanent and irreversible. Take a snapshot of the
instance if want to recover the instance at a later time.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Click Destroy Server on the top-right navigation menu.
4. Check the confirmation prompt and click Destroy Server to apply
changes.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.

```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete Instance endpoint to delete the
instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. Delete the target instance.
```bash
$ vultr-cli instance delete <instance_id>
```
Terraform
1. Open your Terraform configuration and locate the Optimized Cloud
Compute instance resource.
2. Remove the resource block or set its lifecycle to destroy.

```hcl
resource "vultr_instance" "occ" {
label = "occ-instance-1"
region = "del"
plan = "vhp-2c-4gb"
os_id = 2284
hostname = "occ-instance-1"
}
```
# To delete, either remove this block from configuration
# or run: terraform destroy -target vultr_instance.occ
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 0 changed, 1 destroyed.

Monitor
Learn how to monitor your Vultr Optimized Cloud Compute instances
performance metrics including CPU usage, disk operations, and
bandwidth statistics.

How to Monitor a Vultr Optimized
Cloud Compute Instance
Introduction
Monitoring an instance provides information about its performance and usage
statistics. This enables you to track the instance's activity, health, and resource
usage. You can monitor the vCPU usage, disk operations and bandwidth
statistics on a Vultr Cloud Compute instance.
Follow this guide to monitor a Vultr Optimized Cloud Compute instance using
the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. View the instance usage summary within the Overview section.
4. Navigate to the Usage Graphs tab to monitor the instance's usage
statistics.
5. Monitor the instance's bandwidth usage statistics within the Monthly
Bandwidth section.
6. Monitor the instance's performance statistics within the Server
Monitors section.
7. Click the Range drop-down to select a specific timeframe and view the
monitoring information in the following categories:
- vCPU Usage: Displays the vCPU usage statistics.
- Disk Operations: Displays the read and write operations per second
on the primary storage disk.
- Network: Displays the instance's networking statistics in bytes.

Vultr API
1. Send a GET  request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Instance Bandwidth endpoint to monitor the
instance's bandwidth usage statistics.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
bandwidth" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. Monitor the instance's bandwidth usage statistics.
```bash
$ vultr-cli instance bandwidth <instance-id>

Reinstall
Learn how to reinstall your Vultr Optimized Cloud Compute instance to
reset it to a fresh state.
```

How to Reinstall a Vultr Optimized
Cloud Compute Instance
Introduction
Reinstalling an instance wipes the file system, resets all configurations, and
reinstalls the operating system. Any data on the instance's file system is
permanently deleted and cannot be recovered unless a backup or snapshot is
available in your Vultr account.
Follow this guide to reinstall a Vultr Optimized Cloud Compute instance using
the Vultr Console, API, CLI, or Terraform.
Warning
Reinstalling an instance will wipe all data and reinstall the operating system.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Click Server Reinstall on the top-right navigation menu.
4. Check the confirmation prompt and click Reinstall Server to apply the
changes.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.

```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Reinstall Instance endpoint to reinstall the
target instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
reinstall" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. Reinstall the target instance.
```bash
$ vultr-cli instance reinstall <instance_id>
```
Terraform
1. Open your Terraform configuration for the existing Optimized Cloud
Compute instance.
2. Trigger a reinstall by replacing the instance during apply.

```bash
$ terraform apply -replace=vultr_instance.occ
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 1 destroyed.

Reinstall SSH Keys
A guide for reinstalling SSH keys on your Vultr Optimized Cloud Compute
instance to restore secure access.

How to Reinstall SSH Keys on a
Vultr Optimized Cloud Compute
Instance
Introduction
SSH keys enable secure, password-free authentication for users accessing your
instance over SSH. Reinstalling SSH keys resets the instance, wiping all data
and reinstalls the operating system to apply the new SSH key details.
Follow this guide to reinstall SSH keys on a Vultr Optimized Cloud Compute
instance using the Vultr Console, or Terraform.
Warning
Reinstalling SSH keys will wipe all data on the instance and reapply the
selected SSH keys.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Navigate to the Settings tab.
4. Find and click Reinstall SSH Keys on the left navigation menu.
5. Select the target SSH key and click Reinstall.
6. Check the confirmation prompt and click Reinstall SSH Keys to apply the
changes, reinstall the instance and enable the SSH key.

Terraform
1. Open your Terraform configuration for the existing Optimized Cloud
Compute instance.
2. Update the ssh_key_ids in the instance resource to reference the new SSH
key(s).
```hcl
resource "vultr_ssh_key" "new_key" {
name = "mbp-ed25519"
public_key = file("~/.ssh/id_ed25519.pub")
}
resource "vultr_instance" "occ" {
```
# ...existing fields (region, plan, os_id, label, etc.)
ssh_key_ids = [vultr_ssh_key.new_key.id]
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Resize
Learn how to increase or decrease the resources of your Vultr Optimized
Cloud Compute instance.

How to Resize a Vultr Optimized
Cloud Compute Instance
Introduction
Resizing an instance activates a new plan with more vCPUs, RAM, and storage
to match your needs. Downgrading is not supported while upgrading the
instance enables a higher plan without changes to the instance's data or file
system.
Follow this guide to resize a Vultr Optimized Cloud Compute instance using the
Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Navigate to the Settings tab.
4. Find and click Change Plan on the left navigation menu.
5. Click the Change Plan drop-down and select a new instance plan.
6. Click Upgrade to resize your instance.
7. Check the confirmation prompt and click Change Plan to apply changes.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Instance endpoint to resize the
instance with a new plan and note the Job ID.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
  "plan" : "instance_plan_id"
}'
```
3. Send a GET  request to the Get Instance Job endpoint to monitor and get
availble information for the upgrade plan instance job.
```bash
$ curl "https://api.vultr.com/v2/instances/jobs/{job-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. List all available plans the instance can resize to.
```bash
$ vultr-cli instance plan list <instance-id>
```
3. Resize the instance to a new plan.
```bash
$ vultr-cli instance plan upgrade <instance-id> --plan
<instance_plan_id>
```
Terraform
1. Open your Terraform configuration for the existing Optimized Cloud
Compute instance.
2. Update the plan  value in the instance resource to the new Optimized Cloud
Compute plan code.
```hcl
resource "vultr_instance" "occ" {
```
    # ...existing fields (region, os_id, label, etc.)
plan = "vhp-4c-8gb"  # Example: upgrade from vhp-2c-4gb
to vhp-4c-8gb
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Restart
Learn how to restart your Vultr Optimized Cloud Compute instance
through the Vultr Console or API.

How to Restart a Vultr Optimized
Cloud Compute Instance
Introduction
Restarting an instance performs a hard reboot, stopping all running processes
before starting them again. It does not affect the instance's data or file system
and allows application updates or configuration changes that require a reboot to
take effect.
Follow this guide to restart a Vultr Optimized Cloud Compute instance using the
Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Click Server Restart on the top-right navigation menu to restart your
server.
4. Click Restart Server in the confirmation prompt to apply changes.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Reboot Instances endpoint to restart the
instance.
```bash
$ curl "https://api.vultr.com/v2/instances/reboot" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "instance_ids" : [
      "instance_id"
    ]
  }'
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. Restart the instance.
```bash
$ vultr-cli instance restart <instance_id>

Stop
Learn how to safely stop a running Vultr Optimized Cloud Compute
instance from the control panel.
```

How to Stop a Vultr Optimized
Cloud Compute Instance
Introduction
Stopping an instance shuts it down and disables network connectivity until it is
restarted. The operating system and all running processes are halted, but billing
continues unless the instance is deleted.
Follow this guide to stop a Vultr Optimized Cloud Compute instance using the
Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Click Stop Server on the top-right navigation menu to stop the instance.
4. Click Stop Server in the confirmation prompt to stop the instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Halt Instances endpoint to stop the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/halt" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
     "instance_ids" : [
       "your-instance-id"
     ]
   }'
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. Stop the instance.
```bash
$ vultr-cli instance stop <your-instance-id>

Tags
Learn how to organize and categorize your Vultr resources by adding tags
to your Optimized Cloud Compute instances.
```

How to Add Tags on a Vultr
Optimized Cloud Compute Instance
Introduction
Tagging allows you to assign specific labels, known as tags, to an instance for
improved identification in your Vultr account. Tags consist of multiple characters
that help identify, organize, and manage instances in your Vultr account.
Follow this guide to add tags on a Vultr Optimized Cloud Compute instance
using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Navigate to the Tags tab.
4. Enter a new tag in the Add Tag field and click Add to apply the new tag.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Instance endpoint to add tags to the
instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "tags" : ["tag1", "tag2"]
  }'
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. Add new tags to the instance.
```bash
$ vultr-cli instance tags <instance_id> --tags <tag1,tag2>
```
Terraform
1. Open your Terraform configuration for the existing Optimized Cloud
Compute instance.
2. Add or update the tags  argument in the instance resource.
```hcl
resource "vultr_instance" "occ" {
```
    # ...existing fields (region, plan, os_id, label, etc.)
tags = ["production", "web-server"]
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Networking
Manage your Vultr infrastructures connectivity with advanced networking
features, configurations, and security controls.

Enable Firewall
Learn how to activate a Vultr Firewall Group to protect your Optimized
Cloud Compute instance.

How to Enable a Vultr Firewall
Group on a Vultr Optimized Cloud
Compute Instance
Introduction
Vultr Firewall groups allow you to create rules that filter incoming network traffic
to an instance. Firewall rules define the network ports and services to control,
filter, and secure network connections to the instance.
Follow this guide to enable a Vultr Firewall group on a Vultr Optimized Cloud
Compute instance using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Navigate to the Settings tab.
4. Click Firewall on the left navigation menu.
5. Click the Firewall drop-down to select a new firewall group.
6. Click Update Firewall Group to enable the firewall group on the instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Firewall Groups endpoint to list all
available firewall groups.
```bash
$ curl "https://api.vultr.com/v2/firewalls" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PATCH  request to the Update Instance endpoint to attach a firewall
group to the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "firewall_group_id" : "<firewall-id>",
  }'
```
Vultr CLI
1. List all available firewall groups and note the target firewall group's ID.
```bash
$ vultr-cli firewall group list
```
2. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
3. Attach the firewall group to the instance.
```bash
$ vultr-cli instance update-firewall-group --instance-id
<instance-id> --firewall-group-id <firewall-id>
```
Terraform
1. Open your Terraform configuration for the existing Optimized Cloud
Compute instance.
2. Create or reference a vultr_firewall_group  resource and attach it to the
instance.
# Create a firewall group
resource "vultr_firewall_group" "web" {
description = "Web server firewall group"
}
# Add example rules to the group
resource "vultr_firewall_rule" "allow_http" {
firewall_group_id = vultr_firewall_group.web.id
protocol = "tcp"
ip_type = "v4"
subnet = "0.0.0.0"
subnet_size = 0
port = "80"
}
resource "vultr_firewall_rule" "allow_https" {
firewall_group_id = vultr_firewall_group.web.id
protocol = "tcp"
ip_type = "v4"
subnet = "0.0.0.0"
subnet_size = 0
port = "443"
}

# Attach the firewall group to the instance
resource "vultr_instance" "occ" {
    # ...existing fields (region, plan, os_id, label, etc.)
firewall_group_id = vultr_firewall_group.web.id
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

IPv4
Learn how to add additional IPv4 addresses to your Vultr Optimized Cloud
Compute instance.

How to Add IPv4 Addresses on a
Vultr Optimized Cloud Compute
Instance
Introduction
A public IPv4 address is automatically assigned to an instance upon
deployment, unless disabled by default. You can attach multiple IPv4 addresses
to the instance to enable external network connections. Additional addresses
can also be used for tasks such as IP forwarding, static and dynamic routing.
Follow this guide to add the IPv4 information on a Vultr Optimized Cloud
Compute instance using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Navigate to the Settings tab.
4. Click IPv4 on the left navigation menu to view the instance's public IPv4
network information.
5. Click Add Another IPv4 Address to attach an additional public IP
address to the instance.
6. Check the confirmation prompt and click Add IPv4 Address to attach the
new public IP address and restart your instance.
7. Click the default IPv4 reverse DNS value and replace it a custom value to
enable reverse DNS on the instance.

Vultr API
1. Send a GET  request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Instance IPV4 Information endpoint to
view the instance's IPv4 information.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv4" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Create IPv4 endpoint to attach a new IPv4
address to the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv4" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "reboot" : true
  }'
```
4. Send a POST  request to the Create Instance Reverse IPv4 endpoint to
enable reverse DNS on the instance.

```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv4/reverse" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "ip" : "<ipv4-address>",
    "reverse" : "<domain>"
  }'
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. List the instance's IPv4 address information.
```bash
$ vultr-cli instance ipv4 list <instance-id>
```
3. Create a new public IPv4 address and attach it to the instance.
```bash
$ vultr-cli instance ipv4 create <instance-id> --reboot
```
4. Create a new IPv4 reverse DNS entry on the instance.
```bash
$ vultr-cli instance reverse-dns set-ipv4 <instance-id> --
entry <domain> --ip <ipv4-address>

IPv6
A guide explaining how to configure IPv6 addressing on your Vultr
Optimized Cloud Compute instance.
```

How to Add IPv6 Addresses on a
Vultr Optimized Cloud Compute
Instance
Introduction
IPv6 is available but a public address is not automatically assigned to a Vultr
Optimized Cloud Compute instance unless enabled during instance
configuration. Once enabled, you can manage the instance's IPv6 network
settings and configure reverse DNS for specific networking tasks.
Follow this guide to add the IPv6 network information on a Vultr Optimized
Cloud Compute instance using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Navigate to the Settings tab.
4. Click IPv6 on the left navigation menu.
5. Click Assign IPv6 Network to assign a new subnet to the instance.
6. Click Assign IPv6 Network Address to attach an IPv6 address to the
instance.
7. Find the Reverse DNS section, enter your IPv6 address in the IP field,
and a domain in the Reverse DNS field to enable reverse DNS.

Vultr API
1. Send a GET  request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Get Instance IPv6 Information endpoint to
view the instance's IPv6 information.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv6" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Create Instance Reverse IPv6 endpoint to
create a new reverse DNS entry on the IPv6 address.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv6/reverse" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "ip" : "<ipv6-address>",
    "reverse" : "<domain>"
  }'
```

Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. List the instance's IPv6 network information.
```bash
$ vultr-cli instance ipv6 list <instance-id>
```
3. Create a new IPv6 reverse DNS entry on the instance.
```bash
$ vultr-cli instance reverse-dns set-ipv6 <instance-id> --
entry <domain> --ip <ipv6-address>
```
Terraform
1. Open your Terraform configuration for the existing Optimized Cloud
Compute instance.
2. Enable IPv6 on the instance and (optionally) set reverse DNS.
# Enable IPv6 on the instance
resource "vultr_instance" "occ" {
    # ...existing fields (region, plan, os_id, label, etc.)
enable_ipv6 = true
}
# Optional: set reverse DNS for the instance's primary IPv6

# (v6 address is known after the instance exists)
resource "vultr_reverse_ipv6" "occ_ptr" {
ip = vultr_instance.occ.v6_main_ip
reverse = "host.example.com."
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Reserved IPs
A guide explaining how to assign and use dedicated IP addresses with
your Vultr Optimized Cloud Compute instance.

How to Attach Reserved IPs to a
Vultr Optimized Cloud Compute
Instance
Introduction
Reserved IPs allow you to reserve a specific public IP address you can assign to
a Vultr Optimized Cloud Compute instance. You can attach multiple reserved IPs
to a single instance to enable advanced networking capabilities like routing and
IP forwarding with distinct public IP addresses.
Follow this guide to attach reserved IPs on a Vultr Optimized Cloud Compute
instance using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products, expand the Network group and click Reserved
IPs.
2. Click your target reserved IP to open its management page.
3. Click the Attach to Server drop-down and select your target Vultr
Optimized Cloud Compute instance.
4. Click Attach to apply the reserved IP to the Vultr Optimized Cloud
Compute instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.

```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Reserved IPs endpoint and note the target
reserved IP's ID.
```bash
$ curl "https://api.vultr.com/v2/reserved-ips" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Attach Reserved IP endpoint to attach the
reserved IP to the instance.
```bash
$ curl "https://api.vultr.com/v2/reserved-ips/{reserved-ip}/
attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "instance_id" : "<instance-id>"
  }'
```
Vultr CLI
1. List all reserved IPs in your Vultr account and note the target reserved IP's
ID.
```bash
$ vultr-cli reserved-ip list
```
2. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
3. Attach the reserved IP to the instance.
```bash
$ vultr-cli reserved-ip attach <reserved-ip-id> --instance-id <instance-id>
```
Terraform
1. Open your Terraform configuration for the existing Optimized Cloud
Compute instance.
2. Create (or import) a Reserved IP and reference it from the instance using
reserved_ip_id .
```hcl
resource "vultr_reserved_ip" "public_ip" {
region = "del"
ip_type = "v4"          # or "v6"
label = "occ-reserved-ip"
}
resource "vultr_instance" "occ" {
```
    # ...existing fields (region, plan, os_id, label, etc.)
reserved_ip_id = vultr_reserved_ip.public_ip.id
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

VPC 2.0
A private network solution that allows secure communication between
Vultr resources in isolated environments.

VPC 2.0 Product Documentation
VPC 2.0 Product Documentation
How to Attach a VPC 2.0 Network
to a Vultr Optimized Cloud
Compute Instance
Introduction
A Virtual Private Cloud (VPC) 2.0 network creates a secure and isolated private
networking interface to enable connections to other instances attached to the
same network. You can attach multiple VPC 2.0 networks to enable secure
connections between a Vultr Optimized Cloud Compute instance and other
instances attached to the same VPC 2.0 network.
Follow this guide to attach a VPC 2.0 network to a Vultr Optimized Cloud
Compute instance using the Vultr Console, API, CLI or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Navigate to the Settings tab.
4. Click VPC 2.0 on the left navigation menu.
5. Click Enable VPC 2.0 to activate a new VPC 2.0 network interface.
6. Click Enable VPC 2.0 in the confirmation prompt to apply the changes.
7. Click the VPC 2.0 drop-down to select a specific network and click Attach
to apply the changes on your instance.

VPC 2.0 Product Documentation
Vultr API
1. Send a GET  request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Instance VPC 2.0 Networks endpoint to
list all VPC 2.0 networks in your Vultr account and note the target VPC 2.0
network's ID.
```bash
$ curl "https://api.vultr.com/v2/vpc2" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Attach VPC 2.0 to Instance endpoint to
attach a VPC 2.0 network to the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
vpc2/attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "vpc_id": "<vpc2-id>"
  }'

VPC 2.0 Product Documentation
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. List all available VPC 2.0 networks and note the target VPC 2.0 network ID.
```bash
$ vultr-cli vpc2 list
```
3. Attach the VPC 2.0 network to the instance.
```bash
$ vultr-cli vpc2 nodes attach <vpc2-id> \
--nodes="<instance-id>"
```
Terraform
1. Open your Terraform configuration for the existing Optimized Cloud
Compute instance.
2. Create (or reference) a VPC 2.0 network and attach it to the instance.
# Create a VPC 2.0 network
resource "vultr_vpc2" "app_net" {
region = "del"
description = "Private network for OCC workloads"
}
# Attach the VPC 2.0 network to the Optimized Cloud Compute

VPC 2.0 Product Documentation
instance
resource "vultr_instance" "occ" {
label = "occ-01"
region = "del"
plan = "vhp-2c-4gb"
os_id = 2284
hostname = "occ-01"
vpc2_ids = [vultr_vpc2.app_net.id]
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

VPC
A private network solution that allows secure communication between
Vultr instances without using public internet connections.

How to Attach a VPC Network to a
Vultr Optimized Cloud Compute
Instance
Introduction
A Virtual Private Cloud (VPC) network creates a secure and isolated private
networking interface to enable connections to other instances attached to the
same network. You can attach multiple VPC 2.0 networks to enable secure
connections between a Vultr Optimized Cloud Compute instance and other
instances attached to the same VPC network.
Follow this guide to attach a VPC network to a Vultr Optimized Cloud Compute
instance using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Optimized Cloud Compute instance to open its
management page.
3. Navigate to the Settings tab.
4. Click IPv4 on the left navigation menu.
5. Click Enable VPC.
6. Click Enable VPC in the confirmation prompt to apply the changes.
7. Click Attach VPC in the confirmation prompt to apply changes to your
instance.

Vultr API
1. Send a GET  request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List VPCs endpoint to list all available VPCs and
note the target VPC network ID.
```bash
$ curl "https://api.vultr.com/v2/vpcs" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Attach VPC to Instance endpoint to attach
the VPC network to the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
vpcs/attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "vpc_id": "<vpc-id>"
  }'
```
Vultr CLI
1. List all available instances and note your target instance's ID.

```bash
$ vultr-cli instance list
```
2. List all available VPC networks and note the target VPC network ID.
```bash
$ vultr-cli vpc list
```
3. Attach the VPC network to the instance.
```bash
$ vultr-cli instance vpc attach <instance-id> <vpc-id>
```
Terraform
1. Open your Terraform configuration for the existing Optimized Cloud
Compute instance.
2. Create (or reference) a VPC network and attach it to the instance.
# Create a VPC network
resource "vultr_vpc" "app_net" {
region = "del"
description = "Private network for OCC workloads"
}
# Attach the VPC network to the Optimized Cloud Compute
instance
resource "vultr_instance" "occ" {
label = "occ-01"
region = "del"
plan = "vhp-2c-4gb"
os_id = 2284
hostname = "occ-01"

vpc_ids = [vultr_vpc.app_net.id]
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

FAQ
A collection of frequently asked questions and answers about Vultr
services and features.

Frequently Asked Questions (FAQs)
About Optimized Cloud Compute
Introduction
These are the frequently asked questions for Vultr Optimized Cloud Compute
instances.
How can I access a Vultr Optimized Cloud
Compute instance?
You can access a Vultr Optimized Cloud Compute instance depending on its
operating system. Use SSH or the Vultr Console for Linux instances and the
Remote Desktop Protocol for Windows instances.
Can I run resource-intensive applications on
a Vultr Optimized Cloud Compute instance?
Yes, Vultr Optimized Cloud Compute supports resource-intensive applications
depending on your server size. For example, if your applications require more
RAM, deploy a memory-optimized instance.
Can I downgrade a Vultr Optimized Cloud
Compute instance?
No, you cannot downgrade a Vultr Optimized Cloud Compute instance, but can
upgrade the instance to higher plans as your needs grow.

Does a Vultr Optimized Cloud Compute
instance incur any charges when stopped?
Yes, a stopped instance incurs normal charges as it would while running.
However, the instance does not incur any charges when destroyed which may
lead to data loss.
Can I change my Vultr Optimized Cloud
Compute instance type?
Yes, you can change your Vultr Optimized Cloud Compute instance type.
Navigate to Settings -> Change Plan to modify the instance type. For
example, you can change a CPU-optimized instance to a memory-optimized
instance.

Cloud Compute
Cloud Compute offers high-performance virtual machines with flexible
configurations for running applications and workloads in the cloud.

Provisioning
A guide explaining how to set up and deploy new cloud compute
instances on the Vultr platform.

How to Provision Vultr Cloud
Compute Instances
Introduction
Vultr Cloud Compute instances are shared CPU virtual machines designed for
demanding applications with bursty performance, such as low-traffic websites,
blogs, CMS, development/test environments, and small databases. Vultr Cloud
Compute instances are capable of running general purpose applications without
specific CPU, memory or storage performance restrictions.
Follow this guide to provision Vultr Cloud Compute instances using the Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click Deploy.
3. Choose Shared CPU as the instance type.
4. Select your desired Vultr location to deploy the instance to.
5. Select a plan category from the sidebar:
- Cloud Compute: Virtual Machines powered by previous generation
Intel CPUs and regular SSD, and offer a good balance of price and
performance.
- High Frequency: Virtual Machines with a higher clock speed (>3Ghz)
for CPU intensive applications and ultra fast NVMe storage.
- High Performance: Virtual Machines powered by the latest
generation Intel Xeon CPUs or AMD EPYC CPUs and ultra fast NVMe
storage.

6. Select a plan from the available options based on your vCPU, memory,
storage, and bandwidth requirements.
7. Click Configure Software.
8. Select a cloud image to install on the instance based on the following
options:
- Operating System: Installs a fresh operating system image on the
instance.
- Marketplace Apps: Installs a prebuilt software stack or application
and the recommended operating system image on the instance.
- ISO/iPXE: Boots a specific ISO available or iPXE-compatible image on
the instance.
- ISO Library: Installs a specific ISO image from the Vultr ISOs library.
- Backup: Recovers a specific backup available in your Vultr account to
the instance.
- Snapshot: Installs a specific snapshot available in your Vultr account
to the instance.
9. Select optional Server Settings to apply on the instance.
- SSH Keys: Installs a specific SSH key on the instance.
- Startup Script: Enables a startup script to execute at deployment or
a PXE script to automate the operating system installation.
- Firewall Group: Activates a Vultr Firewall group to filter incoming
network traffic on the instance.
10. Enter a new hostname in the Server Hostname field and a descriptive
label in the Server Label field to identify the instance.
11. Configure Additional Features for the instance.
- Instance Connectivity: Select how the instance connects to the
internet.
▪ Instance(s) with Public IP: Assigns public IP addresses directly
to the instance. Under Instance Address, Public IPv4 is
enabled by default. Select Public IPv6 to enable IPv6

addressing. After selecting IPv6, you can optionally deselect
Public IPv4 to create an IPv6-only instance.
▪ Private Instance(s) behind NAT Gateway: Routes internet
traffic through a NAT Gateway in a Virtual Private Cloud (VPC)
Network. Select an existing VPC Network with a NAT Gateway or
click Add VPC Network to create a new one.
- VPC Network: Connects the instance to a VPC Network in the current
location.
- Automatic Backups: Automatically creates backups for data
recovery in case of instance failures.
- DDoS Protection: Prevents potential Distributed Denial of Service
(DDoS) attacks on the instance.
- Limited User Login: Creates a linuxuser non-root user with sudo
privileges as the default user account instead of root .
- Cloud-Init User Data: Enables Cloud-Init user data to initialize and
customize the instance at boot.
12. Click Deploy to provision the instance.
Vultr API
1. Send a POST request to the Create Instance endpoint to create a new
Vultr Cloud Compute instance. Replace VULTR_LOCATION , INSTANCE_PLAN , OS_ID ,
INSTANCE_LABEL , and HOSTNAME with your target values.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
"region" : "VULTR_LOCATION",
"plan" : "INSTANCE_PLAN",
"os_id" : OS_ID,
"label" : "INSTANCE_LABEL",
"hostname": "HOSTNAME"
}'
```
Visit the Create Instance API page to view additional attributes you can
apply on the Vultr Cloud Compute instance.
2. Send a GET request to the List Instances endpoint to list all available
instances.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. Create a new Vultr Cloud Compute instance. Replace VULTR_LOCATION ,
INSTANCE_PLAN , OS_ID , INSTANCE_LABEL , and HOSTNAME with your target values.
```bash
$ vultr-cli instance create --region VULTR_LOCATION --plan
INSTANCE_PLAN --os OS_ID --label INSTANCE_LABEL --host
HOSTNAME
```
Run vultr-cli instance create --help to view additional options you can apply
on the Vultr Cloud Compute instance.
2. List all available instances.
```bash
$ vultr-cli instance list
```
Terraform
1. Ensure the Vultr Terraform provider is configured in your Terraform project.
2. Define the Cloud Compute instance in your Terraform configuration file.

```hcl
terraform {
required_providers {
vultr = {
source = "vultr/vultr"
version = "~> 2.26"
}
}
}
provider "vultr" {}
resource "vultr_instance" "cc" {
label = "cc-instance-1"
hostname = "cc-instance-1"
region = "del"            # such as ewr, ams, sgp
plan = "vc2-2c-4gb"     # Cloud Compute (shared
CPU) plan code; use vhf-* for High Frequency
os_id = 2284             # Ubuntu 24.04 LTS x64
enable_ipv6 = true
}
output "public_ip" {
value = vultr_instance.cc.main_ip
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Connection
Establish and manage connectivity to your Vultr resources through
various methods and protocols.

OpenSSH
A secure protocol for remotely accessing and managing Vultr Cloud
Compute instances via encrypted connections.

How to Connect to a Vultr Cloud
Compute Instance Using SSH
Introduction
OpenSSH is a connection protocol that enables SSH access to an instance. It is
pre-installed and active on Vultr Cloud Compute instances by default to enable
secure connections.
Follow this guide to connect to a Vultr Cloud Compute instance using SSH on
your workstation.
Connect to an Instance Using the Default
User Credentials
1. Open your instance's management page.
2. Note the default credentials within the Overview tab and copy the user
password to your clipboard.
3. Open a new terminal or command prompt application on your workstation.
4. Connect to your Vultr Cloud Compute instance using SSH.
```bash
$ ssh username@SERVER-IP
```
5. Enter yes and press ENTER when prompted to add the instance's public key
to your known hosts.
The authenticity of host '192.0.2.123 (192.0.2.123)' can't be established.
ED25519 key fingerprint is SHA256:gTAOuCiCa3Us4tpVaVHVk9d3qOjKrsqXPOsAFQbB8xw.

This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])?
6. Enter your instance user's password when prompted and press ENTER to log
in.
username@SERVER-IP's password:
7. View the active user in your SSH session.
```bash
$ whoami
Connect to an Instance Using SSH Keys
```
Note
Generate an SSH key on your workstation and add it to your instance during
deployment. Adding an SSH key using the Vultr Console after deployment will
result in data loss and wipe your instance to install the new key.
1. Open a new terminal or command prompt application on your workstation.
2. Connect to your Vultr Cloud Compute instance using a specific SSH key on
your workstation.
```bash
$ ssh -i /path/to/private/key username@SERVER-IP
```
3. Enter yes and press ENTER when prompted to add the instance's public key
to your known hosts.
The authenticity of host '192.0.2.123 (192.0.2.123)' can't be established.
ED25519 key fingerprint is SHA256:gTAOuCiCa3Us4tpVaVHVk9d3qOjKrsqXPOsAFQbB8xw.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes

4. View the active user in your SSH session.
```bash
$ whoami

PuTTY
A guide for connecting to Vultr Cloud Compute instances using the PuTTY
SSH client for Windows users.
```

How to Connect to a Vultr Cloud
Compute Instance Using PuTTY
Introduction
PuTTY is an open-source terminal emulator and SSH client for Windows
workstations. It provides a user-friendly interface and terminal to connect to
instances using SSH. PuTTY supports both password-based authentication and
SSH keys for secure connections to an instance.
Follow this guide to connect to a Vultr Cloud Compute instance using PuTTY on
Windows.
Connect to an Instance Using the Default
User Credentials
1. Open PuTTY from your applications menu.
2. Enter your instance's public IP address in the Host Name (or IP address)
field.
3. Keep 22 as the Port value and SSH as the connection type.
4. Click Open to connect to your instance using SSH.
5. Click Accept when prompted to add the instance's public key to your
workstation's known hosts.
6. Enter your username when prompted for the login as value.
7. Enter the user's password when prompted and press ENTER to log in.
8. View the active user information in your SSH session.

```bash
$ whoami
Connect to an Instance Using SSH Keys
```
1. Enter your instance's public IP address in the Host Name (or IP address)
field.
2. Keep 22 as the Port and SSH as the connection type.
3. Expand the SSH group on the main navigation menu to access additional
connection options.
4. Expand the Auth group and select Credentials from the list of options.
5. Click Browse within the Private key file for authentication field to load
your private key.
6. Click Data within the Connection group and enter the default instance
username in the Auto-login username field to use with your SSH key.
7. Navigate to Session on the main navigation menu and enter a new
session name in the Saved Sessions field.
8. Click Save to store your SSH key, user, and the instance IP configurations.
9. Click Open to connect to the instance using the SSH key session
information.
10. Click Accept when prompted to add the instance's public key to your
workstation's known hosts.
11. View the active user information in your SSH session.
```bash
$ whoami
```

Vultr Console
Access your Vultr Cloud Compute instance directly through the web-based console interface without SSH.

How to Connect to a Vultr Cloud
Compute Instance Using the Vultr
Console
Introduction
Vultr Console is a noVNC terminal that provides direct access to an instance's
console. You can run commands, install applications and manage processes
through the Vultr Console. Additionally, it offers multiple features like clipboard
sharing, a virtual keyboard, and special commands such as CTRL ALT DEL to
manage an instance.
Follow this guide to connect to a Vultr Cloud Compute instance using the Vultr
Console.
Note
Enable pop-ups in your web browser settings to access the Vultr Console.
1. Open your instance's management page.
2. Find the default credentials in the Overview tab and copy the user
password to your clipboard.
3. Find and click View Console on the top-right navigation menu to open the
Vultr Console.
4. Enter your default username and press ENTER when prompted.
5. Find and click Send Clipboard on the list of control bar options to paste
the user password in your Vultr Console session.
6. Press ENTER to log in to the instance.

Features
Explore the complete set of capabilities and functionalities available with
Vultr's cloud infrastructure services.

Auto Backups
A service that automatically creates and stores backups of your Vultr
instances on a regular schedule.

How to Enable Automatic Backups
on a Vultr Cloud Compute Instance
Introduction
Automatic Backups allow you to create full backups of your instance's data and
file system on a scheduled basis, ensuring recovery in case of unexpected
failures. These backups follow specific schedules and retention policies to
ensure your instance is securely backed up in your Vultr account
Follow this guide to enable automatic backups on a Vultr Cloud Compute
instance using the Vultr Console, API, or Terraform.
Vultr Console
1. Navigate to Products and click Compute
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Navigate to the Backups tab.
4. Click Enable Backups to turn on automatic backups.
5. Click Enable Backups in the confirmation prompt to enable automatic
backups.
6. Click the Schedule Backups drop-down to choose a backup schedule.
7. click Update to create automatic backups based on your selection.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.

```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Instance endpoint to update the
instance and enable automatic backups.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "backups" : "enabled"
  }'
```
3. Send a POST  request to the Set Instance Backup Schedule endpoint to
create a new automatic backups schedule.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
backup-schedule" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "type": "daily",
    "hour": 10,
    "dow": 1,
    "dom": 1
  }'
```
Visit the Set Instance Backup Schedule API page to view additional
backup schedule attributes.

Terraform
1. Open your Terraform configuration for the existing Cloud Compute
instance.
2. Enable backups and define a schedule in the configuration.
```hcl
resource "vultr_instance" "cc" {
label = "cc-instance-1"
hostname = "cc-instance-1"
region = "del"
plan = "vc2-2c-4gb" # or vhf-*, vhp-* etc. per
need
os_id = 2284
backups = "enabled"
backups_schedule {
type = "daily" # daily | weekly | monthly
hour = 10 # UTC hour (0-23)
```
# dow/dom only when type = "weekly" or "monthly"
# dow = 1
# dom = 1
}
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Cloud-Init
A guide for modifying the initialization scripts and configuration data on
your Vultr instance after deployment.

Cloud-Init Product Documentation
Cloud-Init Product Documentation
How to Update Cloud-Init User Data
on a Vultr Cloud Compute Instance
Introduction
Cloud-Init enables the automatic initialization and configuration of instances
during the initial boot phase. It runs user data scripts to customize an instance,
install applications, and configure specific packages or services.
Follow this guide to update Cloud-Init user data on a Vultr Cloud Compute
instance using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Navigate to the User-Data tab.
4. Enter your script or cloud config in the Cloud-Init User-Data field.
5. Click Update to apply the changes.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"

Cloud-Init Product Documentation
```
2. Send a PATCH  request to the Update Instance endpoint to update the
instance's Cloud-Init user data.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "user_data" : "<cloud-init-data>",
  }'
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. Upload new Cloud-Init user data to the instance from a file on your
workstation.
```bash
$ vultr-cli instance user-data set <instance-id> --userdata
"<script-path>"
```
Terraform
Cloud-Init user data can only be set during instance creation in Terraform and
cannot be updated on an existing instance without recreating it.
1. Open your Terraform configuration for the new Cloud Compute instance.

Cloud-Init Product Documentation
2. Add the user_data argument to the instance resource to run a script at first
boot.
```hcl
resource "vultr_instance" "cc" {
```
# ...existing fields (region, plan, os_id, label, etc.)
user_data = <<-EOT
#!/bin/bash
apt-get update -y
apt-get install -y nginx
systemctl enable --now nginx
EOT
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

DDoS Protection
Shields your Vultr Cloud Compute instance from distributed denial-of-service attacks with advanced traffic filtering.

How to Enable DDoS Protection on
a Vultr Cloud Compute Instance
Introduction
Distributed Denial of Service (DDoS) protection enables traffic monitoring and
prevents potential DDoS attacks to an instance. It activates a set of tools that
detect and block network flooding attempts, ensuring the instance remains
active and operational.
Follow this guide to enable DDoS protection on a Vultr Cloud Compute instance
using the Vultr Console, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Navigate to the DDoS tab.
4. Click Enable DDoS Protection.
5. Click Enable DDoS Protection in the confirmation prompt to enable
DDoS protection on your instance.
Terraform
1. Open your Terraform configuration for the existing Cloud Compute
instance.
2. Enable DDoS protection in the instance resource.
```hcl
resource "vultr_instance" "cc" {
```
    # ...existing fields (region, plan, os_id, label, etc.)
ddos_protection = true
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Snapshots
Learn how to create and manage point-in-time backups of your Vultr
Cloud Compute instance for data protection and recovery.

How to Create Snapshots on a Vultr
Cloud Compute Instance
Introduction
A snapshot is a point-in-time copy of an instance's state, including its entire file
system and disk contents. Snapshots offer a quick backup solution for
instances, making it easier to restore data in case of unexpected failures or
data loss.
Follow this guide to create snapshots on a Vultr Cloud Compute instance using
the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click the target Vultr Cloud Compute instance to open its management
page.
3. Navigate to the Snapshots tab.
4. Enter a new descriptive label in the Label field and click Create
Snapshot to take a new snapshot of your instance. Snapshot creation can
take upto 30 minutes depending on the instance size.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Create Snapshot endpoint to create a new
snapshot of the instance.
```bash
$ curl "https://api.vultr.com/v2/snapshots" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "instance_id" : "<instance-id>",
    "description" : "<label>"
  }'
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. Create a new snapshot of the instance.
```bash
$ vultr-cli snapshot create --id <instance-id>
```

Management
Centralized tools and features for administering and controlling your Vultr
infrastructure and account settings.

Change Hostname
Learn how to change the hostname on your Vultr Cloud Compute instance
for proper system identification.

How to Change the Hostname on a
Vultr Cloud Compute Instance
Introduction
Changing the hostname on an instance modifies the default server
configuration and reinstalls the operating system. This operation may results in
data loss when the instance is reinstalled to apply the new hostname.
Follow this guide to change the hostname on a Vultr Cloud Compute instance
using the Vultr Console, or Terraform.
Warning
Changing the hostname reinstalls the operating system and wipes all data on
your server.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Navigate to the Settings tab.
4. Find and click Change Hostname on the left navigation menu.
5. Replace the existing value with your new hostname.
6. Click Reinstall to change your instance hostname.
7. Check the confirmation prompt and click Change Hostname to apply the
new hostname.

Terraform
1. Open your Terraform configuration for the existing Cloud Compute
instance.
2. Update the hostname value in the instance resource.
```hcl
resource "vultr_instance" "cc" {
```
# ...existing fields (region, plan, os_id, label, etc.)
hostname = "new-hostname"
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Change OS
Learn how to change the operating system on your existing Vultr Cloud
Compute instance.

How to Change the Operating
System on a Vultr Cloud Compute
Instance
Introduction
Changing the instance operating system wipes all data on your server and
installs a new file system. This is important when changing the default
operating system while preserving the instance's IP and networking information.
Follow this guide to change the operating system on a Vultr Cloud Compute
instance using the Vultr Console, API, CLI, or Terraform.
Warning
Changing to a different operating system wipes all the data on your server.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Navigate to the Settings tab.
4. Find and click Change OS on the left navigation menu.
5. Click the Choose new OS drop-down and select a new operating system
to install on the instance.
6. Click Change OS to change the instance operating system.
7. Check the Change OS confirmation prompt and click Change OS to apply
the new instance changes.

Vultr API
1. Send a GET  request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List OS endpoint to view all available operating
systems and note the target OS ID.
```bash
$ curl "https://api.vultr.com/v2/os" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PATCH  request to the Update Instance endpoint with a new os_id
value to change the instance's operating system.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
  "os_id" : "new-instance-os_id"
}'
```
Vultr CLI
1. List all available instances and note your target instance's ID.

```bash
$ vultr-cli instance list
```
2. List all available operating systems and note the target OS ID.
```bash
$ vultr-cli instance os list <instance-id>
```
3. Change the target instance's operating system.
```bash
$ vultr-cli instance os change <instance-id> --os <os_id>
```
Terraform
1. Open your Terraform configuration for the existing Cloud Compute
instance.
2. Update the os_id  value in the instance resource to the new operating
system ID.
```hcl
resource "vultr_instance" "cc" {
```
    # ...existing fields (region, plan, label, etc.)
os_id = 1743  # Example: Ubuntu 22.04 LTS x64
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Change Startup Script
Learn how to modify the startup script that runs when your Vultr Cloud
Compute instance boots up.

How to Change the Startup Script
on a Vultr Cloud Compute Instance
Introduction
Startup scripts allow you to automate specific configurations during the
operating system installation. Changing the startup script on an instance wipes
the file system and reinstalls the default operating system.
Follow this guide to change the startup script on a Vultr Cloud Compute
instance using the Vultr Console, or Terraform.
Warning
Changing the startup script on an instance will wipe all data and reinstall the
operating system.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Navigate to the Settings tab.
4. Find and click Change StartUp Script on the left navigation menu.
5. Click Add Startup Script.
6. Enter a new script name and click the Type drop down to select the script
type.
7. Add your startup script data and click Add Script to apply the script to
your instance.
8. Navigate to Change StartUp Script in your instance settings to verify
that the new script is added.
9. Select the startup script and click Change Startup Script.

10. Check the confirmation prompt and click Change Startup Script to apply
the new script.
Terraform
1. Open your Terraform configuration for the existing Cloud Compute
instance.
2. Create or reference a vultr_startup_script  resource and attach it to the
instance.
# Create a new startup script
resource "vultr_startup_script" "init" {
name = "init-nginx"
type = "boot"  # boot pxeboot
script = <<-EOT
    #!/bin/bash
    apt-get update -y
    apt-get install -y nginx
    systemctl enable --now nginx
    EOT
}
# Attach the startup script to the instance
resource "vultr_instance" "cc" {
    # ...existing fields (region, plan, os_id, label, etc.)
script_id = vultr_startup_script.init.id
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Custom ISO
A feature that allows you to upload and attach your own ISO image to
Vultr instances for custom operating system installations.

How to Attach a Custom ISO to a
Vultr Cloud Compute Instance
Introduction
ISO images allow you to install a specific operating system on an Vultr Cloud
Compute instance. Custom ISOs enable you to deploy operating systems not
available in the default Vultr installer list. They are useful for creating tailored
environments or booting into specialized modes, such as rescue and recovery
environments.
Follow this guide to attach a custom ISO to a Vultr Cloud Compute instance
using the Vultr Console, API, CLI, or Terraform.
Warning
Installing a custom ISO on a Vultr Cloud Compute instance disables the
default user credentials listed in your instance's management page.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Navigate to the Settings tab.
4. Find and click Custom ISO on the left navigation menu.
5. Select a custom ISO available in your Vultr account or click the ISO
Library drop-down to select from a list of public ISOs.
6. Click Attach ISO and Reboot to attach the ISO to your instance.

Vultr API
1. Send a GET  request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List ISOs endpoint and note your target ISO ID.
```bash
$ curl "https://api.vultr.com/v2/iso" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Attach ISO to Instance endpoint to attach
the ISO to your target instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/iso/
attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "iso_id" : "<iso-id>"
  }'
```
Vultr CLI
1. List all available instances and note your target instance's ID.

```bash
$ vultr-cli instance list
```
2. List all available ISO images and note your target ISO's ID.
```bash
$ vultr-cli iso list
```
3. Attach the ISO to your target instance.
$ vultr-cli instance iso attach <instance-id> \
            --iso-id="<iso-id>"
Terraform
1. Open your Terraform configuration for the existing Cloud Compute
instance.
2. Add the iso_id field to attach the desired ISO.
```hcl
resource "vultr_instance" "cc" {
```
    # ...existing fields (region, plan, os_id, label, etc.)
iso_id = "<iso-id>"
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.
Note
Terraform does not currently support attaching an ISO in-place to a running
instance.

The ISO must be set at create time or during a rebuild, which replaces the
instance and wipes all existing data.

Delete
Learn how to permanently remove a Vultr Cloud Compute instance from
your account.

How to Delete a Vultr Cloud
Compute Instance
Introduction
Deleting an instance permanently erases the server's file system and removes
all IP information. This action is irreversible and any data on the instance data is
lost unless a backup or snapshot is available in your Vultr account.
Follow this guide to delete a Vultr Cloud Compute instance using the Vultr
Console, API, CLI, or Terraform.
Warning
Deleting an instance is permanent and irreversible. Take a snapshot of the
instance if want to recover the instance at a later time.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Click Destroy Server on the top-right navigation menu to delete the
server instance.
4. Check the confirmation prompt and click Destroy Server to apply
changes.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.

```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete Instance endpoint to delete the
instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. Delete the target instance.
```bash
$ vultr-cli instance delete <instance_id>
```
Terraform
1. Open your Terraform configuration and locate the Cloud Compute instance
resource.
2. Remove the resource block or set its lifecycle to destroy.

```hcl
resource "vultr_instance" "cc" {
label = "cc-instance-1"
region = "del"
plan = "vc2-2c-4gb"
os_id = 2284
hostname = "cc-instance-1"
}
```
# To delete, either remove this block from configuration
# or run: terraform destroy -target vultr_instance.cc
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 0 changed, 1 destroyed.

Monitor
Learn how to monitor your Vultr Cloud Compute instances performance
metrics including CPU usage, disk operations, and bandwidth statistics.

How to Monitor a Vultr Cloud
Compute Instance
Introduction
Monitoring an instance provides information about its performance and usage
statistics. This enables you to track the instance's activity, health, and resource
usage. You can monitor the vCPU usage, disk operations and bandwidth
statistics on a Vultr Cloud Compute instance.
Follow this guide to monitor a Vultr Cloud Compute instance using the Vultr
Console, API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. View the instance usage summary within the Overview section.
4. Navigate to the Usage Graphs tab to monitor the instance's usage
statistics.
5. Monitor the instance's bandwidth usage statistics within the Monthly
Bandwidth section.
6. Monitor the instance's performance statistics within the Server Monitors
section.

7. Click the Range drop-down to select a specific timeframe and view the
monitoring information in the following categories:
- vCPU Usage: Displays the vCPU usage statistics.
- Disk Operations: Displays the read and write operations per second
on the primary storage disk.
- Network: Displays the instance's networking statistics in bytes.
Vultr API
1. Send a GET  request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Instance Bandwidth endpoint to monitor the
instance's bandwidth usage statistics.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
bandwidth" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. Monitor the instance's bandwidth usage statistics.
```bash
$ vultr-cli instance bandwidth <instance-id>

Reinstall
Learn how to reinstall the operating system on your Vultr Cloud Compute
instance while preserving your IP address and hostname.
```

How to Reinstall a Vultr Cloud
Compute Instance
Introduction
Reinstalling an instance wipes the file system, resets all configurations, and
reinstalls the operating system. Any data on the instance's file system is
permanently deleted and cannot be recovered unless a backup or snapshot is
available in your Vultr account.
Follow this guide to reinstall a Vultr Cloud Compute instance using the Vultr
Console, API, CLI, or Terraform.
Warning
Reinstalling an instance will wipe all data and reinstall the operating system.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Click Server Reinstall on the top-right navigation menu.
4. Check the confirmation prompt and click Reinstall Server to apply the
changes.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.

```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Reinstall Instance endpoint to reinstall the
target instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
reinstall" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. Reinstall the target instance.
```bash
$ vultr-cli instance reinstall <instance_id>
```
Terraform
1. Open your Terraform configuration for the existing Cloud Compute
instance.
2. Trigger a reinstall by replacing the instance during apply.

```bash
$ terraform apply -replace=vultr_instance.cc
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 1 destroyed.

Reinstall SSH Keys
Learn how to add or replace SSH keys on an existing Vultr Cloud Compute
instance.

How to Reinstall SSH Keys on a
Vultr Cloud Compute Instance
Introduction
SSH keys enable secure, password-free authentication for users accessing your
instance over SSH. Reinstalling SSH keys resets the instance, wiping all data
and reinstalls the operating system to apply the new SSH key details.
Follow this guide to reinstall SSH keys on a Vultr Cloud Compute instance using
the Vultr Console, or Terraform.
Warning
Reinstalling SSH keys will wipe all data on the instance and reapply the
selected SSH keys.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Navigate to the Settings tab.
4. Find and click Reinstall SSH Keys on the left navigation menu.
5. Select the target SSH key and click Reinstall.
6. Check the confirmation prompt and click Reinstall SSH Keys to apply the
changes, reinstall the instance and enable the SSH key.
Terraform
1. Open your Terraform configuration for the existing Cloud Compute
instance.

2. Update the ssh_key_ids in the instance resource to reference the new SSH
key(s).
```hcl
resource "vultr_ssh_key" "new_key" {
name = "mbp-ed25519"
public_key = file("~/.ssh/id_ed25519.pub")
}
resource "vultr_instance" "cc" {
```
# ...existing fields (region, plan, os_id, label, etc.)
ssh_key_ids = [vultr_ssh_key.new_key.id]
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Resize
Learn how to increase or decrease the resources of your Vultr Cloud
Compute instance to match your workload requirements.

How to Resize a Vultr Cloud
Compute Instance
Introduction
Resizing an instance activates a new plan with more vCPUs, RAM, and storage
to match your needs. Downgrading is not supported while upgrading the
instance enables a higher plan without changes to the instance's data or file
system.
Follow this guide to resize a Vultr Cloud Compute instance using the Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Navigate to the Settings tab.
4. Find and click Change Plan on the left navigation menu.
5. Click the Change Plan drop-down and select a new instance plan.
6. Click Upgrade to resize your instance.
7. Check the confirmation prompt and click Change Plan to apply changes.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Instance endpoint to resize the
instance with a new plan and note the Job ID.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
  "plan" : "instance_plan_id"
}'
```
3. Send a GET  request to the Get Instance Job endpoint to monitor and get
availble information for the upgrade plan instance job.
```bash
$ curl "https://api.vultr.com/v2/instances/jobs/{job-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. List all available plans the instance can resize to.
```bash
$ vultr-cli instance plan list <instance-id>
```
3. Resize the instance to a new plan.
```bash
$ vultr-cli instance plan upgrade <instance-id> --plan
<instance_plan_id>
```
Terraform
1. Open your Terraform configuration and locate the Cloud Compute instance
resource.
2. Update the plan attribute with the new instance plan ID.
```hcl
resource "vultr_instance" "cc" {
label = "cc-instance-1"
region = "del"
plan = "vc2-4c-8gb" # Updated plan ID for more vCPUs/
RAM/Storage
os_id = 2284
hostname = "cc-instance-1"
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Restart
Learn how to restart your Vultr Cloud Compute instance through the Vultr
Console or API.

How to Restart a Vultr Cloud
Compute Instance
Introduction
Restarting an instance performs a hard reboot, stopping all running processes
before starting them again. It does not affect the instance's data or file system
and allows application updates or configuration changes that require a reboot to
take effect.
Follow this guide to restart a Vultr Cloud Compute instance using the Vultr
Console, API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Click Server Restart on the top-right navigation menu to restart your
server.
4. Click Restart Server in the confirmation prompt to apply changes.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Reboot Instances endpoint to restart the
instance.
```bash
$ curl "https://api.vultr.com/v2/instances/reboot" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "instance_ids" : [
      "instance_id"
    ]
  }'
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. Restart the instance.
```bash
$ vultr-cli instance restart <instance_id>

Stop
Learn how to temporarily halt your Vultr Cloud Compute instance while
preserving its configuration and data.
```

How to Stop a Vultr Cloud Compute
Instance
Introduction
Stopping an instance shuts it down and disables network connectivity until it is
restarted. The operating system and all running processes are halted, but billing
continues unless the instance is deleted.
Follow this guide to stop a Vultr Cloud Compute instance using the Vultr
Console, API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Click Stop Server on the top-right navigation menu to stop the instance.s
4. Click Stop Server in the confirmation prompt to stop the instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Halt Instances endpoint to stop the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/halt" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
     "instance_ids" : [
       "your-instance-id"
     ]
   }'
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. Stop the instance.
```bash
$ vultr-cli instance stop <your-instance-id>

Tags
A labeling system that helps organize and filter Vultr resources for easier
management and identification.
```

How to Add Tags on a Vultr Cloud
Compute Instance
Introduction
Tagging allows you to assign specific labels, known as tags, to an instance for
improved identification in your Vultr account. Tags consist of multiple characters
that help identify, organize, and manage instances in your Vultr account.
Follow this guide to add tags on a Vultr Cloud Compute instance using the Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Navigate to the Tags tab.
4. Enter a new tag in the Add Tag field and click Add to apply the new tag.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Instance endpoint to add new tags to
the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "tags" : ["tag1", "tag2"]
  }'
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. Add new tags to the instance.
```bash
$ vultr-cli instance tags <instance_id> --tags <tag1,tag2>
```
Terraform
1. Open your Terraform configuration for the existing Cloud Compute
instance.
2. Add or update the tags  argument in the instance resource.
```hcl
resource "vultr_instance" "cc" {
```
    # ...existing fields (region, plan, os_id, label, etc.)
tags = ["production", "web-server"]
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Networking
Manage and configure network settings for your Vultr infrastructure
including IP addresses, firewalls, and connectivity options.

Enable Firewall
Learn how to activate a Vultr Firewall Group on your Cloud Compute
instance to control network traffic.

How to Enable a Vultr Firewall
Group on a Vultr Cloud Compute
Instance
Introduction
Vultr Firewall groups allow you to create rules that filter incoming network traffic
to an instance. Firewall rules define the network ports and services to control,
filter, and secure network connections to the instance.
Follow this guide to enable a Vultr Firewall group on a Vultr Cloud Compute
instance using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Navigate to the Settings tab.
4. Click Firewall on the left navigation menu.
5. Click the Firewall drop-down to select a new firewall group.
6. Click Update Firewall Group to enable the firewall group on the instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Firewall Groups endpoint to list all
available firewall groups.
```bash
$ curl "https://api.vultr.com/v2/firewalls" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PATCH  request to the Update Instance endpoint to attach a firewall
group to the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "firewall_group_id" : "<firewall-id>",
  }'
```
Vultr CLI
1. List all available firewall groups and note the target firewall group's ID.
```bash
$ vultr-cli firewall group list
```
2. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
3. Attach the firewall group to the instance.
```bash
$ vultr-cli instance update-firewall-group --instance-id
<instance-id> --firewall-group-id <firewall-id>
```
Terraform
1. Open your Terraform configuration for the existing Cloud Compute
instance.
2. Create or reference a vultr_firewall_group  resource and attach it to the
instance.
# Create a firewall group
resource "vultr_firewall_group" "web" {
description = "Web server firewall group"
}
# Add example rules to the group
resource "vultr_firewall_rule" "allow_http" {
firewall_group_id = vultr_firewall_group.web.id
protocol = "tcp"
ip_type = "v4"
subnet = "0.0.0.0"
subnet_size = 0
port = "80"
}
resource "vultr_firewall_rule" "allow_https" {
firewall_group_id = vultr_firewall_group.web.id
protocol = "tcp"
ip_type = "v4"
subnet = "0.0.0.0"
subnet_size = 0
port = "443"
}

# Attach the firewall group to the instance
resource "vultr_instance" "cc" {
    # ...existing fields (region, plan, os_id, label, etc.)
firewall_group_id = vultr_firewall_group.web.id
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

IPv4
A guide explaining how to add additional IPv4 addresses to your existing
Vultr Cloud Compute instance

How to Add IPv4 Addresses on a
Vultr Cloud Compute Instance
Introduction
A public IPv4 address is automatically assigned to an instance upon
deployment, unless disabled by default. You can attach multiple IPv4 addresses
to the instance to enable external network connections. Additional addresses
can also be used for tasks such as IP forwarding, static and dynamic routing.
Follow this guide to add the IPv4 information on a Vultr Cloud Compute instance
using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Navigate to the Settings tab.
4. Click IPv4 on the left navigation menu to view the instance's public IPv4
network information.
5. Click Add Another IPv4 Address to attach an additional public IP
address to the instance.
6. Check the confirmation prompt and click Add IPv4 Address to attach the
new public IP address and restart your instance.
7. Click the default IPv4 reverse DNS value and replace it a custom value to
enable reverse DNS on the instance.

Vultr API
1. Send a GET  request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Instance IPV4 Information endpoint to
view the instance's IPv4 information.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv4" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Create IPv4 endpoint to attach a new IPv4
address to the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv4" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "reboot" : true
  }'
```
4. Send a POST  request to the Create Instance Reverse IPv4 endpoint to
enable reverse DNS on the instance.

```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv4/reverse" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "ip" : "<ipv4-address>",
    "reverse" : "<domain>"
  }'
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. List the instance's IPv4 address information.
```bash
$ vultr-cli instance ipv4 list <instance-id>
```
3. Create a new public IPv4 address and attach it to the instance.
```bash
$ vultr-cli instance ipv4 create <instance-id> --reboot
```
4. Create a new IPv4 reverse DNS entry on the instance.
```bash
$ vultr-cli instance reverse-dns set-ipv4 <instance-id> --
entry <domain> --ip <ipv4-address>

IPv6
A guide explaining how to configure IPv6 addressing on your Vultr Cloud
Compute instance for enhanced network connectivity.
```

How to Add IPv6 Addresses on a
Vultr Cloud Compute Instance
Introduction
IPv6 is available but a public address is not automatically assigned to a Vultr
Cloud Compute instance unless enabled during instance configuration. Once
enabled, you can manage the instance's IPv6 network settings and configure
reverse DNS for specific networking tasks.
Follow this guide to add the IPv6 information on a Vultr Cloud Compute instance
using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Navigate to the Settings tab.
4. Click IPv6 on the left navigation menu.
5. Click Assign IPv6 Network to assign a new subnet to the instance.
6. Click Assign IPv6 Network Address to attach an IPv6 address to the
instance.
7. Find the Reverse DNS section, enter your IPv6 address in the IP field,
and a domain in the Reverse DNS field to enable reverse DNS.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.

```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Get Instance IPv6 Information endpoint to
view the instance's IPv6 information.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv6" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Create Instance Reverse IPv6 endpoint to
create a new reverse DNS entry on the IPv6 address.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv6/reverse" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "ip" : "<ipv6-address>",
    "reverse" : "<domain>"
  }'
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. List the instance's IPv6 network information.
```bash
$ vultr-cli instance ipv6 list <instance-id>
```
3. Create a new IPv6 reverse DNS entry on the instance.
```bash
$ vultr-cli instance reverse-dns set-ipv6 <instance-id> --
entry <domain> --ip <ipv6-address>
```
Terraform
1. Open your Terraform configuration for the existing Cloud Compute
instance.
2. Enable IPv6 on the instance and (optionally) set reverse DNS.
# Enable IPv6 on the instance
resource "vultr_instance" "cc" {
    # ...existing fields (region, plan, os_id, label, etc.)
enable_ipv6 = true
}
# Optional: set reverse DNS for the instance's primary IPv6
# (v6 address is known after the instance exists)
resource "vultr_reverse_ipv6" "cc_ptr" {
ip = vultr_instance.cc.v6_main_ip
reverse = "host.example.com."
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Reserved IPs
A feature that allows you to assign permanent IP addresses to your Vultr
instances that remain available even when the instance is destroyed.

How to Attach Reserved IPs to a
Vultr Cloud Compute Instance
Introduction
Reserved IPs allow you to reserve a specific public IP address you can assign to
a Vultr Cloud Compute instance. You can attach multiple reserved IPs to a single
instance to enable advanced networking capabilities like routing and IP
forwarding with distinct public IP addresses.
Follow this guide to attach reserved IPs on a Vultr Cloud Compute instance using
the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products, expand the Network group and click Reserved
IPs.
2. Click your target reserved IP to open its management page.
3. Click the Attach to Server drop-down and select your target Vultr Cloud
Compute instance.
4. Click Attach to apply the reserved IP to the Vultr Cloud Compute instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Reserved IPs endpoint and note the target
reserved IP's ID.
```bash
$ curl "https://api.vultr.com/v2/reserved-ips" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Attach Reserved IP endpoint to attach the
reserved IP to the instance.
```bash
$ curl "https://api.vultr.com/v2/reserved-ips/{reserved-ip}/
attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "instance_id" : "<instance-id>"
  }'
```
Vultr CLI
1. List all reserved IPs in your Vultr account and note the target reserved IP's
ID.
```bash
$ vultr-cli reserved-ip list
```
2. List all available instances and note your target instance's ID.

```bash
$ vultr-cli instance list
```
3. Attach the reserved IP to the instance.
```bash
$ vultr-cli reserved-ip attach <reserved-ip-id> --instance-id <instance-id>
```
Terraform
1. Open your Terraform configuration for the existing Cloud Compute
instance.
2. Add the vultr_reserved_ip  resource and reference its id  in the instance’s
reserved_ip_id field.
```hcl
resource "vultr_reserved_ip" "public_ip" {
region = "del"
ip_type = "v4"
label = "cc-reserved-ip"
}
resource "vultr_instance" "cc" {
label = "cc-instance-1"
region = "del"
plan = "vc2-2c-4gb"
os_id = 1743
reserved_ip_id = vultr_reserved_ip.public_ip.id
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

VPC 2.0
A private network solution that allows you to securely connect multiple
Vultr resources within an isolated environment.

VPC 2.0 Product Documentation
VPC 2.0 Product Documentation
How to Attach a VPC 2.0 Network
to a Vultr Cloud Compute Instance
Introduction
A Virtual Private Cloud (VPC) 2.0 network creates a secure and isolated private
networking interface to enable connections to other instances attached to the
same network. You can attach multiple VPC 2.0 networks to enable secure
connections between a Vultr Cloud Compute instance and other instances
attached to the same VPC 2.0 network.
Follow this guide to attach a VPC 2.0 network to a Vultr Cloud Compute instance
using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Navigate to the Settings tab.
4. Click VPC 2.0 on the left navigation menu.
5. Click Enable VPC 2.0 to activate a new VPC 2.0 network interface.
6. Click Enable VPC 2.0 in the confirmation prompt to apply the changes.
7. Click the VPC 2.0 drop-down to select a specific network and click Attach
to apply the changes on your instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.

VPC 2.0 Product Documentation
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Instance VPC 2.0 Networks endpoint to
list all VPC 2.0 networks in your Vultr account and note the target VPC 2.0
network's ID.
```bash
$ curl "https://api.vultr.com/v2/vpc2" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Attach VPC 2.0 to Instance endpoint to
attach a VPC 2.0 network to the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
vpc2/attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "vpc_id": "<vpc2-id>"
  }'
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list

VPC 2.0 Product Documentation
```
2. List all available VPC 2.0 networks and note the target VPC 2.0 network ID.
```bash
$ vultr-cli vpc2 list
```
3. Attach the VPC 2.0 network to the instance.
```bash
$ vultr-cli vpc2 nodes attach <vpc2-id> \
--nodes="<instance-id>"
```
Terraform
1. Open your Terraform configuration for the existing Cloud Compute
instance.
2. Create (or reference) a VPC 2.0 network and attach it to the instance.
# Create a new VPC 2.0 network
resource "vultr_vpc2" "private_net" {
region = "del"
description = "Private network for CC workloads"
}
# Attach the VPC 2.0 network to the Cloud Compute instance
resource "vultr_instance" "cc" {
    # ...existing fields (region, plan, os_id, label, etc.)
label = "cc-instance-1"
region = "del"
plan = "vc2-2c-4gb"
os_id = 2284
vpc2_ids = [vultr_vpc2.private_net.id]
}
3. Apply the configuration and observe the following output:

VPC 2.0 Product Documentation
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

VPC
A private network solution that allows secure communication between
Vultr resources without using public internet connections.

How to Attach a VPC Network to a
Vultr Cloud Compute Instance
Introduction
A Virtual Private Cloud (VPC) network creates a secure and isolated private
networking interface to enable connections to other instances attached to the
same network. You can attach multiple VPC 2.0 networks to enable secure
connections between a Vultr Cloud Compute instance and other instances
attached to the same VPC network.
Follow this guide to attach a VPC network to a Vultr Cloud Compute instance
using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Navigate to the Settings tab.
4. Click IPv4 on the left navigation menu.
5. Click Enable VPC.
6. Click Enable VPC in the confirmation prompt to apply the changes.
7. Click Attach VPC in the confirmation prompt to apply changes to your
instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note your target
instance's ID.

```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List VPCs endpoint to list all available VPCs and
note the target VPC network ID.
```bash
$ curl "https://api.vultr.com/v2/vpcs" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Attach VPC to Instance endpoint to attach
the VPC network to the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
vpcs/attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "vpc_id": "<vpc-id>"
  }'
```
Vultr CLI
1. List all available instances and note your target instance's ID.
```bash
$ vultr-cli instance list
```
2. List all available VPC networks and note the target VPC network ID.

```bash
$ vultr-cli vpc list
```
3. Attach the VPC network to the instance.
```bash
$ vultr-cli instance vpc attach <instance-id> <vpc-id>
```
Terraform
1. Open your Terraform configuration for the existing Cloud Compute
instance.
2. Create (or reference) a VPC network and attach it to the instance.
# Create a new VPC network
resource "vultr_vpc" "private_net" {
region = "del"
description = "Private network for CC workloads"
}
# Attach the VPC network to the Cloud Compute instance
resource "vultr_instance" "cc" {
    # ...existing fields (region, plan, os_id, label, etc.)
label = "cc-instance-1"
region = "del"
plan = "vc2-2c-4gb"
os_id = 2284
vpc_ids = [vultr_vpc.private_net.id]
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

FAQ
Frequently asked questions and answers about Vultr's products, services,
and platform features.

Frequently Asked Questions (FAQs)
About Cloud Compute
Introduction
These are the frequently asked questions for Vultr Cloud Compute instances.
How can I access a Vultr Cloud Compute
instance?
You can access a Vultr Cloud Compute instance depending on its operating
system. Use SSH or the Vultr Console for Linux instances and the Remote
Desktop Protocol for Windows instances.
Can I run web applications and services on a
Vultr Cloud Compute instance?
Yes, Vultr Cloud Compute instances can run web applications and low-resource
services efficiently. Upgrade the instance each time your needs grow to enable
the smooth run time of your applications.
Can I downgrade a Vultr Cloud Compute
instance?
No, you cannot downgrade a Vultr Cloud Compute instance, but you can
upgrade the instance to higher plans as your resource needs grow.

Does a Vultr Cloud Compute instance incur
any charges when stopped?
Yes, a stopped instance incurs normal charges as it would while running.
However, the instance does not incur any charges when destroyed.
Can I change my Vultr Cloud Compute
instance CPU type?
No, you cannot change your Vultr Cloud Compute instance's CPU type after
deployment.

Cloud GPU
Powerful GPU-accelerated cloud computing solutions for AI, machine
learning, and graphics-intensive workloads with flexible provisioning
options.

Provisioning
A guide explaining how to set up and deploy GPU-powered virtual
machines on Vultr's cloud platform.

How to Provision Vultr Cloud GPU
Instances
Introduction
Vultr Cloud GPU instances are virtual machines that run with dedicated NVIDIA
GPUs designed for AI applications, machine learning, HPC, visual computing,
and VDI. Cloud GPU instances include a dedicated GPU device capable of
running multiple applications depending on your resource requirements.
Follow this guide to provision Vultr Cloud GPU instances using the Vultr Console,
API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Compute on the list of product options.
2. Click Deploy to access the Deploy New Instance page.
3. Select Cloud GPU.
4. Choose your desired Vultr location to deploy the instance.
5. Select a GPU type from the sidebar based on your workload requirements.
6. Select a plan from the available options based on your GPU, vCPU,
memory, storage, and bandwidth requirements.
7. Click Configure Software.
8. Select a cloud image to install on your instance based on the following
options:
- Marketplace Apps: Install a prebuilt software stack or application
and the recommended operating system image on the instance.

- Operating System: Install a fresh operating system image on the
instance. GPU enabled versions include pre-installed drivers.
- Upload ISO: Install a specific ISO available in your Vultr account or
upload a new ISO image from your workstation to install on the
instance.
- ISO Library: Install a specific ISO image from the Vultr ISOs library.
- Backup: Recover a specific backup available in your Vultr account to
the instance.
- Snapshot: Install a specific snapshot available in your Vultr account
to the instance.
9. Select optional Server Settings to apply on the instance.
- SSH Keys: Installs a specific SSH key on the instance.
- Startup Script: Enables a startup script to execute at deployment or
a PXE script to automate the operating system installation.
- Firewall Group: Activates a Vultr Firewall group to filter incoming
network traffic on the instance.
10. Enter a new hostname in the Server Hostname field and a descriptive
label in the Server Label field to identify the instance.
11. Configure Additional Features for the instance.
- Instance Connectivity: Select how the instance connects to the
internet.
▪ Instance(s) with Public IP: Assigns public IP addresses directly
to the instance. Under Instance Address, Public IPv4 is
enabled by default. Select Public IPv6 to enable IPv6
addressing. After selecting IPv6, you can optionally deselect
Public IPv4 to create an IPv6-only instance.
▪ Private Instance(s) behind NAT Gateway: Routes internet
traffic through a NAT Gateway in a Virtual Private Cloud (VPC)
Network. Select an existing VPC Network with a NAT Gateway or
click Add VPC Network to create a new one.
- VPC Network: Connects the instance to a VPC Network in the current
location.
- Automatic Backups: Automatically creates backups for data
recovery in case of instance failures.

- DDoS Protection: Prevents potential Distributed Denial of Service
(DDoS) attacks on the instance.
- Limited User Login: Creates a linuxuser non-root user with sudo
privileges as the default user account instead of root .
- Cloud-Init User Data: Enables Cloud-Init user data to initialize and
customize the instance at boot.
12. Click Deploy to provision the instance.
Vultr API
1. Send a POST request to the Create Instance endpoint to create a new
Vultr Cloud GPU instance. Replace VULTR_LOCATION , INSTANCE_PLAN , OS_ID ,
INSTANCE_LABEL , and HOSTNAME with your target values.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
"region" : "VULTR_LOCATION",
"plan" : "INSTANCE_PLAN",
"os_id" : OS_ID,
"label" : "INSTANCE_LABEL",
"hostname": "HOSTNAME"
}'
```
Visit the Create Instance API page to view additional attributes you can
apply on the Vultr Cloud GPU instance.
Vultr CLI
1. Create a new Vultr Cloud GPU instance. Replace VULTR_LOCATION ,
INSTANCE_PLAN , OS_ID , INSTANCE_LABEL , and HOSTNAME with your target values.

```bash
$ vultr-cli instance create --region VULTR_LOCATION --plan
INSTANCE_PLAN --os OS_ID --label INSTANCE_LABEL --host
HOSTNAME
```
Run vultr-cli instance create --help  to view additional options you can apply
on the Vultr Cloud GPU instance.
Terraform
1. Ensure the Vultr Terraform provider is configured in your Terraform project.
2. Add the Cloud GPU instance resource to your Terraform configuration.
```hcl
terraform {
required_providers {
vultr = {
source = "vultr/vultr"
version = "~> 2.26"
}
}
}
provider "vultr" {}
resource "vultr_instance" "gpu" {
region = "del"              # Target deployment
region
plan = "vcg-a100-12c-120g-80vram" # Cloud GPU plan ID (A100/A40/A16)
os_id = 2284               # Ubuntu 24.04 LTS x64
label = "gpu-instance-1"
hostname = "gpu-instance-1"
enable_ipv6 = true
}
output "public_ip" {

value = vultr_instance.gpu.main_ip
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Connection
Establish a secure connection to your Vultr infrastructure for remote
management and data transfer.

OpenSSH
A secure protocol for remotely accessing and managing Vultr Cloud GPU
instances through encrypted connections.

How to Connect to a Vultr Cloud
GPU Instance Using SSH
Introduction
OpenSSH is a connection protocol that enables SSH access on a server. It's
available and active on Vultr Cloud GPU instances by default to enable secure
connections.
Follow this guide to connect to a Vultr Cloud GPU instance using SSH on your
workstation.
Connect to an Instance Using the Default
User Credentials
1. Access your Cloud GPU instance's management page.
2. Note the default credentials within the Overview tab and copy the user
password to your clipboard.
3. Open a new terminal window on your workstation.
4. Connect to your Vultr Cloud GPU instance using SSH.
```bash
$ ssh username@SERVER-IP
```
5. Enter yes and press Enter when prompted to add the instance public key
to your workstation's known hosts.
The authenticity of host '192.0.2.123 (192.0.2.123)' can't be established.
ED25519 key fingerprint is SHA256:gTAOuCiCa3Us4tpVaVHVk9d3qOjKrsqXPOsAFQbB8xw.

This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
6. Paste your instance password when prompted and press Enter to log in.
username@SERVER-IP's password:
7. View the active user information in your SSH session.
```bash
$ whoami
Connect to an Instance Using SSH Keys
```
Note
Generate an SSH key on your workstation and add it to your instance during
deployment. Adding an SSH key after deployment will result in data loss and
wipe your instance to install the new key.
1. Open a new terminal window on your workstation.
2. Connect to your Vultr Cloud GPU instance using a specific SSH key on your
workstation.
```bash
$ ssh -i /path/to/private/key username@SERVER-IP
```
3. Enter yes and press Enter when prompted to add the instance public key
to your workstation's known hosts.
The authenticity of host '192.0.2.123 (192.0.2.123)' can't be established.
ED25519 key fingerprint is SHA256:gTAOuCiCa3Us4tpVaVHVk9d3qOjKrsqXPOsAFQbB8xw.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes

4. View the active user information in your SSH session.
```bash
$ whoami

Putty
A guide for connecting to Vultr Cloud GPU instances using the PuTTY SSH
client for Windows users.
```

How to Connect to a Vultr Cloud
GPU Instance Using Putty
Introduction
Putty is an open source terminal emulator for Windows workstations. It provides
a unique management panel and terminal to connect to instances using SSH.
Putty supports password-based authentication and SSH keys to connect to an
instance.
Follow this guide to connect to a Vultr Cloud GPU instance using Putty on
Windows.
Connect to an Instance Using the Default
User Credentials
1. Open Putty from your applications menu.
2. Enter your instance's public IP address in the Host Name (or IP address)
field.
3. Keep 22 as the Port value and SSH as the connection type.
4. Click Open to connect to your instance using SSH.
5. Click Accept when prompted to add the instance's public key to your
workstation's known hosts.
6. Enter your instance username as the login as value.
7. Enter your user password when prompted and press Enter to log in.
8. View the active user information in your SSH session.

```bash
$ whoami
Connect to an Instance Using SSH Keys
```
1. Enter your instance's public IP address in the Host Name (or IP address)
field.
2. Keep 22 as the Port and SSH as the connection type.
3. Expand the SSH group on the main navigation menu to access more
connection options.
4. Expand the Auth group and select Credentials from the list of options.
5. Click Browse within the Private key file for authentication field to load
your private key.
6. Click Data within the Connection group and enter the default instance
username in the Auto-login username field to use with your SSH key.
7. Navigate to Session on the main navigation menu and enter a new
session name in the Saved Sessions field.
8. Click Save to store your SSH key, user, and the instance IP configurations.
9. Click Open to connect to the instance using the SSH key session
information.
10. Click Accept when prompted to add the instance's public key to your
workstation's known hosts.
11. View the active user information in your SSH session.
```bash
$ whoami
```

Vultr Console
A web-based interface that provides direct access to your Vultr GPU
instance without requiring SSH or RDP clients.

How to Connect to a Vultr Cloud
GPU Instance Using the Vultr
Console
Introduction
Vultr Console is a noVNC terminal that provides direct console access to
instances. You can access the instance terminal, run commands, install
applications and manage processes using the Vultr Console. In addition, Vultr
Console supports multiple tools to enable clipboard sharing, virtual keyboard,
and special commands such as Ctrl Alt Del.
Follow this guide to connect to a Vultr Cloud GPU instance using the Vultr
Console.
Note
Allow pop-ups in your web browser settings to enable access to the Vultr
Console.
1. Open the Vultr Console.
2. Navigate to Products and click Compute.
3. Click your target Cloud GPU instance to open its management page.
4. Note the default credentials within the Overview tab and copy the user
password to your clipboard.
5. Find and click View Console on the top-right navigation menu to open the
Vultr console.
6. Enter your default username and press Enter.
7. Reveal the console's control bar on the floating noVNC menu.
8. Find and click Clipboard on the list of control bar options.
9. Paste your user password in the Clipboard field and click Paste to apply
the clipboard contents in your console session.
10. Click Clipboard again to hide the pop-up dialog.

11. Click the instance console and press Enter to log in to your instance.

Features
Explore the comprehensive suite of capabilities and functionalities
available on the Vultr platform.

Auto Backups
A service that automatically creates and stores backups of your Vultr GPU
instance on a regular schedule.

How to Enable Automatic Backups
on a Vultr Cloud GPU Instance
Introduction
Automatic Backups enable the creation of a full backup of your instance data
and file system using a specific schedule for recovery in case of unexpected
failures. Automatic backups use specific backup schedule intervals and
retention policies to ensure your instance is backed up in your Vultr account.
Follow this guide to enable automatic backups on a Vultr Cloud GPU instance
using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target instance to open its management page.
3. Navigate to the Backups tab.
4. Click Enable Backups to turn on automatic backups.
5. Click Enable Backups in the confirmation prompt to enable automatic
backups.
6. Click the Schedule Backups drop down to select a back up schedule.
7. Click Update to create automatic backups based on set the schedule.
Vultr API
1. Send a GET request to the List Instances endpoint and note the target
instance's ID in your output.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Instance endpoint to update the
instance and enable automatic backups.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "backups" : "enabled"
  }'
```
3. Send a POST  request to the Set Instance Backup Schedule endpoint to
create a new automatic backups schedule to enable on your instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
backup-schedule" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "type": "daily",
    "hour": 10,
    "dow": 1,
    "dom": 1
  }'
```
Visit the Set Instance Backup Schedule API page to view additional
schedule attributes to create automatic backups.
Vultr CLI
1. List all instances in your Vultr account and note the target instance's ID.

```bash
$ vultr-cli instance list
```
2. Create a new automatic backups schedule using the target instance's ID.
```bash
$ vultr-cli instance backup create
e56d93ea-41c4-4dbe-93e2-537c552cf2fb --type daily --hour 10
--dow 1 --dom 1
```
Run vultr-cli instance backup create --help  to view more additional schedule
options to create automatic backups.
Terraform
1. Open your Terraform configuration for the existing Cloud GPU instance.
2. Update the backups  value in the instance resource to "enabled" .
```hcl
resource "vultr_instance" "gpu" {
```
    # ...existing fields (region, plan, label, etc.)
backups = "enabled"  # Enable automatic backups
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Cloud-Init
A guide for updating the Cloud-Init user data on your Vultr Cloud GPU
instance after deployment.

Cloud-Init Product Documentation
Cloud-Init Product Documentation
How to Update Cloud-Init User Data
on a Vultr Cloud GPU Instance
Introduction
Cloud-Init enables the automatic initialization and configuration of instances
during the initial boot phase. Cloud-Init user data runs a specific script's
contents to automate the instance customization, software installation and
configuration of specific packages or services.
Follow this guide to update Cloud-Init user data on a Vultr Cloud GPU instance
using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target instance to open its management page.
3. Navigate to the User-Data tab.
4. Enter your script or cloud config in the Cloud-Init User-Data field.
5. Click Update to apply changes.
Vultr API
1. Send a GET request to the List Instances endpoint and note the target
instance's ID in your output.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"

Cloud-Init Product Documentation
```
2. Send a PATCH  request to the Update Instance endpoint to update the
Cloud-Init user data on the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "user_data" : "<cloud-init-data>",
  }'
```
Vultr CLI
1. List all instances available in your Vultr account and note the target
instance's ID.
```bash
$ vultr-cli instance list
```
2. Upload new Cloud-Init user data to the instance using a file on your
workstation.
```bash
$ vultr-cli instance user-data set <instance-id> --userdata
"<script-path>"
```
Terraform
Cloud-Init user data can only be set during instance creation in Terraform and
cannot be updated on an existing instance without recreating it.
1. Open your Terraform configuration for the new Cloud GPU instance.

Cloud-Init Product Documentation
2. Add the user_data argument to the instance resource to run a script at first
boot.
```hcl
resource "vultr_instance" "gpu" {
```
# ...existing fields (region, plan, os_id, label, etc.)
user_data = <<-EOT
#!/bin/bash
apt-get update -y
apt-get install -y nginx
systemctl enable --now nginx
EOT
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

DDoS Protection
A guide explaining how to activate DDoS protection features for your
Vultr Cloud GPU instance to safeguard against distributed denial-of-service attacks.

How to Enable DDoS Protection on
a Vultr Cloud GPU Instance
Introduction
Distributed Denial of Service (DDoS) protection enables traffic monitoring and
prevents potential DDoS attacks from overwhelming an instance. DDoS
protection actives a set of tools that block network flooding attempts targeting
an instance.
Follow this guide to enable DDoS protection on a Vultr Cloud GPU instance using
the Vultr Console, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target instance to open its management page.
3. Navigate to the DDoS tab.
4. Click Enable DDoS Protection.
5. Click Enable DDoS Protection in the confirmation prompt to enable
DDoS protection on the instance.
Terraform
1. Open your Terraform configuration for the existing Cloud GPU instance.
2. Update the ddos_protection value in the instance resource to true .
```hcl
resource "vultr_instance" "gpu" {
```
# ...existing fields (region, plan, label, etc.)

ddos_protection = true
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Snapshots
Learn how to create and manage snapshots of your Vultr Cloud GPU
instance for backup and recovery purposes.

How to Create Snapshots on a Vultr
Cloud GPU Instance
Introduction
A snapshot is a point-in-time copy of the instance state that includes the file
system and disk contents. Snapshots enable instant backups of an instance to
enable data recovery in case of unexpected failures.
Follow this guide to create snapshots on a Vultr Cloud GPU instance using the
Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target instance to open its management page.
3. Navigate to the Snapshots tab.
4. Enter a new descriptive label in the Label field.
5. Click Create Snapshot to take a new snapshot of your instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note the target
instance's ID in your output.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Create Snapshot endpoint to create a new
snapshot of the instance.
```bash
$ curl "https://api.vultr.com/v2/snapshots" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "instance_id" : "<instance-id>",
    "description" : "<label>"
  }'
```
Vultr CLI
1. List all instances available in your Vultr account and note the target
instance's ID.
```bash
$ vultr-cli instance list
```
2. Create a new snapshot of the instance.
```bash
$ vultr-cli snapshot create --id <instance-id>

Explore GPU Variants
A comprehensive guide to Vultr's diverse GPU options designed for high-performance computing tasks like AI, machine learning, and 3D
rendering.
```

Explore GPU Variants for Vultr
Cloud GPU
Introduction
Vultr offers a wide range of Vultr Cloud GPU options to meet different user
needs. These powerful GPUs help users handle demanding tasks such as
machine learning, artificial intelligence, 3D rendering, and complex simulations.
With Vultr's resources, developers can create and launch new applications more
effectively.
This article explains the four different Vultr Cloud GPU offerings which are A16,
A40, A100 Tensor Core and L40S, you will get an understanding of the core
differences between the GPU variants to help users make the best choice for a
specific workload.
GPU Specifications and Performance
Overview
This section provides the necessary technical and performance data to compare
the 4 different GPUs based on their CUDA Cores, Tflops performance, parallel
processing.
Below are the stats of the different Cloud GPUs Vultr offers to compare
performances:
TF32
CUDA Tensor tflops GPU Architecture
Variant Implementation
cores cores with memory type
sparsity
vGPU 5120 160 72 64 GB

TF32
CUDA Tensor tflops GPU Architecture
Variant Implementation
cores cores with memory type
sparsity
NVIDIA NVIDIA
A16 GPU Ampere
NVIDIA NVIDIA
vGPU 10752 336 149.6 48 GB
A40 GPU Ampere
NVIDIA
A100 NVIDIA
vGPU 6912 432 312 80 GB
Tensor Ampere
Core GPU
NVIDIA NVIDIA ADA
Passthrough 18716 568 366 48 GB
L40S GPU Lovelace
Key Terms
1. vGPU: Allows a physical GPU to be shared among multiple virtual
machines (VMs), enabling high-performance graphics and compute
workloads in a virtualized environment. This is particularly useful for tasks
like virtual desktop infrastructure (VDI), graphics-intensive applications,
and AI workloads in shared setups.
2. Passthrough: Virtualization technique that allows a physical GPU to be
directly assigned to a single virtual machine (VM), providing the VM with
exclusive access to the GPU's resources. Unlike vGPU, where a GPU is
shared among multiple VMs, passthrough dedicates the entire GPU to one
VM for maximum performance and compatibility.
3. CUDA Cores: These are specific type of processing unit designed to work
with NVIDIA's CUDA programming model, they play a fundamental role in
parallel processing and accelerating various computing tasks focused on
graphics rendering. They often use a Single Instruction, Multiple Data
(SIMD) architecture so that a single instruction is executed simultaneously
on multiple data elements, resulting a high throughput in parallel
computing.

4. Tensor Cores: These are specialized hardware component in the NVIDIA
GPUs made for accelerating matrix-based computations that are commonly
used in deep learning and many artificial intelligence workloads. They are
optimized for mathematical operations involved in neural network training
and inference by taking advantage of their mixed precision computing,
where certain part of the calculations with higher precision and the rest
with half precision while maintaining the accuracy in results by using error
correction and accumulation.
GPU Briefs
• NVIDIA A16: Vultr Cloud GPU, powered by the NVIDIA A16, is a flexible
and reliable solution for low-latency VDI, efficient transcoding, and AI
inference. This technology helps businesses provide high-performance,
secure, and scalable computing solutions for different applications. With
improved computational power, organizations can increase productivity,
protect data more effectively, and use cost-efficient infrastructure. Learn
more about Vultr Cloud GPU A16.
• NVIDIA A40: Vultr Cloud GPU, powered by the NVIDIA A40, is designed for
workloads that require advanced visualization, such as 3D rendering,
virtual production, and complex simulations. This GPU offers high memory
capacity and processing power, making it ideal for data-intensive tasks.
Businesses can leverage the A40 to manage large datasets, perform real-time rendering, and support demanding creative and scientific workflows.
It also enables scalable, secure infrastructure that helps improve efficiency
and reduce operational costs. Learn more about Vultr Cloud GPU A40.
• NVIDIA A100 Tensor Core: Vultr Cloud GPU, powered by the NVIDIA
A100, is designed for tasks such as AI training, deep learning, and large-scale data processing. With its tensor cores and large memory, the A100
helps businesses handle complex computations, work with large datasets,
and improve AI model efficiency. It is suitable for research, scientific work,
and other tasks that need strong parallel processing. This GPU also allows
organizations to scale their infrastructure while managing costs. Learn
more about Vultr Cloud GPU A100.

• NVIDIA L40S: Vultr Cloud GPU, powered by the NVIDIA L40S, is optimized
for advanced graphics, AI inference, and real-time processing. The L40S
excels in handling tasks like 3D visualization, virtual environments, and
video processing, making it suitable for creative industries and high-end
computing projects. With its efficient performance and flexibility, the L40S
can help businesses deliver smoother graphics and faster data processing
while keeping infrastructure scalable and cost-effective. Learn more about
Vultr Cloud GPU L40S.

GPU Enabled Images
Pre-configured operating system templates optimized for GPU-accelerated computing workloads on Vultr's platform.

Vultr GPU Enabled Images
Introduction
Vultr GPU Enabled images for Vultr Cloud GPU instances streamline the
development of Artificial Intelligence (AI) and Machine Learning (ML) projects by
providing pre-installed software tailored to specific GPU providers.
This results in reduced time required to set up the server before you can use it
for operations like building, fine-tuning, or inferring a model. We ensure that the
pre-installed softwares are tested on our infrastructure and are reliable for all
your AI/ML development needs.
Softwares Included in Vultr GPU Enabled
Images for Vultr Cloud GPU Instances
Specific to AMD
• AMD GPU Drivers: These are software components that enable
communication between an AMD graphics card and the operating system.
These drivers are crucial for ensuring optimal performance, compatibility,
and stability across a variety of applications, including gaming,
professional graphics, and compute workloads.
• ROCm Software Stack: It is a software stack is AMD's open-source
platform designed to enable High-Performance computing (HPC), Artificial
Intelligence (AI), and Machine Learning (ML) applications on AMD GPUs.
ROCm provides a comprehensive ecosystem that includes libraries, tools,
and frameworks for GPU-accelerated workloads, supporting languages
such as Python, C++, and Fortran.
• Docker: It is a platform for developing, shipping, and running applications
inside containers.

Softwares Included in Vultr GPU Enabled
Images for Vultr Cloud GPU Instances
Specific to NVIDIA
• NVIDIA GPU Drivers: They ensure to enable your computer to utilize the
NVIDIA GPUs making them function properly.
• NVIDIA CUDA Toolkit: It is also a set of programming tools and libraries
to utilize the potential of NVIDIA GPUs, allowing users to speed up
computation and parallel processing tasks.
• NVIDIA Container Toolkit: It is a suite of tools, libraries, and runtime
components provided by NVIDIA that enables the use of NVIDIA GPUs
within containerized environments.
• Docker: It is a platform for developing, shipping, and running applications
inside containers.
More Resources
• Explore Vultr Cloud GPU Variants
• Provision Vultr Cloud GPU Instances
• Manage Vultr Cloud GPU Instances

Management
Tools and features for managing your Vultr infrastructure, including
access controls, monitoring, and account administration.

Change Hostname
Learn how to modify the hostname on your Vultr Cloud GPU instance for
proper system identification.

How to Change the Hostname on a
Vultr Cloud GPU Instance
Introduction
Changing the default hostname on an instance modifies the default server
configuration and reinstalls the operating system.
Follow this guide to change the hostname on a Vultr Cloud GPU instance using
the Vultr Console, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Cloud GPU instance to open its management page.
3. Navigate to the Settings tab.
4. Find and click Change Hostname on the left navigation menu.
5. Replace the existing value with your new hostname.
6. Click Reinstall to change your instance hostname.
7. Check the confirmation prompt and click Change Hostname to apply your
new hostname.
Terraform
1. Open your Terraform configuration for the existing Cloud GPU instance.
2. Update the hostname value in the instance resource to the new hostname.
```hcl
resource "vultr_instance" "gpu" {
```
# ...existing fields (region, plan, label, etc.)

hostname = "new-hostname"
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Change OS
Learn how to change the operating system on your Vultr Cloud GPU
instance.

How to Change the Operating
System on a Vultr Cloud GPU
Instance
Introduction
Changing the instance operating system wipes all data on your server and
installs a new file system. This is important when changing your default
operating system while maintaining your instance's IP networking information.
Follow this guide to change the operating system on a Vultr Cloud Compute
instance using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Cloud GPU instance to open its management page.
3. Navigate to the Settings tab.
4. Find and click Change OS on the left navigation menu.
5. Click the Choose new OS drop-down and select a new operating system
to install on your instance.
6. Click Change OS to change the instance operating system.
7. Check the Change OS confirmation prompt and click Change OS to apply
the new instance changes.
Vultr API
1. Send a GET request to the List Instances endpoint and note the target
instance's ID.

```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List OS endpoint to view all available operating
systems and note the target OS ID.
```bash
$ curl "https://api.vultr.com/v2/os" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PATCH  request to the Update Instance endpoint with a new os_id
value to change the instance's operating system.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
  "os_id" : "new-instance-os_id"
}'
```
Vultr CLI
1. List all instances in your Vultr account and note the target instance's ID.
```bash
$ vultr-cli instance list
```
2. List all available operating systems and note the target OS ID.

```bash
$ vultr-cli instance os list <instance-id>
```
3. Change the target instance's operating system.
```bash
$ vultr-cli instance os change <instance-id> --os <os_id>
```
Terraform
1. Open your Terraform configuration for the existing Cloud GPU instance.
2. Update the os_id  value in the instance resource to the new operating
system ID.
```hcl
resource "vultr_instance" "gpu" {
```
    # ...existing fields (region, plan, label, etc.)
os_id = 1743  # Example: Ubuntu 22.04 LTS x64
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Destroy Instance
Learn how to permanently delete a Vultr Cloud GPU Instance and all
associated data.

How to Destroy a Vultr Cloud GPU
Instance
Introduction
Destroying an instance removes the public IP address and deletes the server
from your Vultr account. Destroying an instance cannot be reversed and any
instance data cannot be recovered unless a backup or snapshot is available in
your Vultr account.
Follow this guide to destroy a Vultr Cloud GPU instance using the Vultr Console,
API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Cloud GPU instance to open its management page.
3. Click Destroy Server on the top-right navigation menu to destroy the
server instance.
4. Check the confirmation prompt and click Destroy Server to apply
changes.
Vultr API
1. Send a GET request to the List Instances endpoint and note the target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete Instance endpoint to destroy the
instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all instances in your Vultr account and note the target instance's ID.
```bash
$ vultr-cli instance list
```
2. Destroy the instance.
```bash
$ vultr-cli instance delete <instance_id>
```
Terraform
1. Open your Terraform configuration and locate the Cloud GPU instance
resource.
2. Remove the resource block or destroy it by target.
```hcl
resource "vultr_instance" "gpu" {
label = "gpu-instance-1"
region = "ewr"
plan = "vcg-1c-8gb"
os_id = 2284
hostname = "gpu-instance-1"
}
```
# To delete, either remove this block from configuration
# or run: terraform destroy -target vultr_instance.gpu
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 0 changed, 1 destroyed.

Monitor Instance
Learn how to monitor performance and usage statistics for your Vultr
Cloud GPU instance to track activity and resource utilization.

How to Monitor a Vultr Cloud GPU
Instance
Introduction
Monitoring an instance provides information about performance and usage
statistics. This enables you to keep track of your instance activity and usage
ratio depending on the running services.
Follow this guide to monitor a Vultr Cloud GPU instance using the Vultr Console,
API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Cloud GPU instance to open its management page.
3. View the instance usage summary within the Overview section.
4. Navigate to the Usage Graphs tab to monitor your instance usage
statistics.
5. Monitor the instance bandwidth usage statistics within the Monthly
Bandwidth section.
6. Monitor the instance performance statistics within the Server Monitors
section.
7. Click the Range drop-down to select a specific timeframe and view the
monitoring information within the following categories:
- vCPU Usage: Displays the server vCPU usage statistics.

- Disk Operations: Displays the number of read and write operations
on the server’s primary storage disk.
- Network: Displays the instance’s public network interface traffic
statistics in bytes.
Vultr API
1. Send a GET  request to the List Instances endpoint and note the target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Instance Bandwidth endpoint to monitor the
instance's bandwidth usage statistics.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
bandwidth" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all instances in your Vultr account and note the target instance's ID.
```bash
$ vultr-cli instance list
```
2. Monitor the instance's bandwidth usage statistics.

```bash
$ vultr-cli instance bandwidth <instance-id>

Reinstall Instance
Learn how to reinstall your Vultr Cloud GPU instance to reset it to a clean
state while maintaining the same IP address and hostname.
```

How to Reinstall a Vultr Cloud GPU
Instance
Introduction
Reinstalling a Vultr Cloud GPU instance wipes the file system, resets all
configurations and reinstalls the operating system. Any data available on the
instance's file system is permanently deleted and cannot be recovered unless
backed up.
Follow this guide to reinstall a Vultr Cloud GPU instance using the Vultr Console,
API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Cloud GPU instance to open its management page.
3. Click Server Reinstall on the top-right navigation menu to reinstall the
server's file system.
4. Check the confirmation prompt and click Reinstall Server to apply
changes.
Vultr API
1. Send a GET request to the List Instances endpoint and note the target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Reinstall Instance endpoint to reinstall the
instance with a new hostname.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
reinstall" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "hostname" : "new_instance_hostname"
  }'
```
Vultr CLI
1. List all instances in your Vultr account and note the target instance's ID.
```bash
$ vultr-cli instance list
```
2. Reinstall the instance with a new hostname.
```bash
$ vultr-cli instance reinstall --host
<new_instance_hostname> <instance_id>
```
Terraform
1. Open your Terraform configuration for the existing Cloud GPU instance.
2. Trigger a reinstall by replacing the instance during apply.

```bash
$ terraform apply -replace=vultr_instance.gpu
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 1 destroyed.

Restart Instance
A guide explaining how to properly restart your Vultr Cloud GPU instance
when needed.

How to Restart a Vultr Cloud GPU
Instance
Introduction
Restarting an instance performs a hard reboot and stops all running processes
on your server before starting them again. Restarting does not alter the
instance data or file system and enables the application of updates or
configuration changes that require a reboot.
Follow this guide to restart a Vultr Cloud GPU instance using the Vultr Console,
API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Cloud GPU instance to open its management page.
3. Click Server Restart on the top-right navigation menu to restart your
server.
4. Click Restart Server in the confirmation prompt to apply changes.
Vultr API
1. Send a GET request to the List Instances endpoint and note the target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Reboot Instances endpoint to restart the
instance.
```bash
$ curl "https://api.vultr.com/v2/instances/reboot" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "instance_ids" : [
      "instance_id"
    ]
  }'
```
Vultr CLI
1. List all instances in your Vultr account and note the target instance's ID.
```bash
$ vultr-cli instance list
```
2. Restart the target instance.
```bash
$ vultr-cli instance restart <instance_id>

Startup Script
Learn how to modify the startup script on your Vultr Cloud GPU instance
to customize its initialization process.
```

How to Change the Startup Script
on a Vultr Cloud GPU Instance
Introduction
Startup scripts enable you to run specific configurations to automate the
operating system installation processes. Changing the startup script on an
active instance wipes the file system and reinstalls the default operating
system.
Follow this guide to change the startup script on a Vultr Cloud GPU instance
using the Vultr Console, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target instance to open its management page.
3. Navigate to the Settings tab.
4. Find and click Change StartUp Script on the left navigation menu.
5. Enter a new script name in the name field and click the Type drop down to
set the script type.
6. Enter your startup script data in the Script field and click Add Script to
enable the script on your instance.
7. Navigate to Change StartUp Script in your instance settings to verify
that the new script is added.
Terraform
1. Open your Terraform configuration for the existing Cloud GPU instance.

2. Create or reference a vultr_startup_script  resource and attach it to the
instance.
# Create a new startup script
resource "vultr_startup_script" "init" {
name = "init-nginx"
type = "boot"  # boot pxeboot
script = <<-EOT
    #!/bin/bash
    apt-get update -y
    apt-get install -y nginx
    systemctl enable --now nginx
    EOT
}
# Attach the startup script to the GPU instance
resource "vultr_instance" "gpu" {
    # ...existing fields (region, plan, os_id, label, etc.)
script_id = vultr_startup_script.init.id
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Stop Instance
Learn how to properly stop a Vultr Cloud GPU instance to pause resources
while maintaining your configuration.

How to Stop a Vultr Cloud GPU
Instance
Introduction
Stopping an instance shuts it down and disables connectivity to the main
network interface. The operating system and all running processes are stopped,
but the instance normal billing cycle continues unless destroyed.
Follow this guide to stop a Vultr Cloud GPU instance using the Vultr Console, API,
or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target instance to open its management page.
3. Click Stop Server on the top-right navigation menu to stop the instance.
4. Click Stop Server in the confirmation prompt to stop the instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note the target
instance's ID in the output.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST request to the Halt Instances endpoint to stop the instance.

```bash
$ curl "https://api.vultr.com/v2/instances/halt" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
     "instance_ids" : [
       "your-instance-id"
     ]
   }'
```
Vultr CLI
1. List all instances in your Vultr account and note the target instance's ID.
```bash
$ vultr-cli instance list
```
2. Stop the instance.
```bash
$ vultr-cli instance stop <your-instance-id>

Tags
Learn how to organize and categorize your Vultr Cloud GPU instances
using the tag management system
```

How to Manage Tags on a Vultr
Cloud GPU Instance
Introduction
Tagging enables the assignment of specific labels called tags on an instance for
identification in your Vultr account. Tags consist of multiple characters that help
identify, organize, and manage instances in your Vultr account.
Follow this guide to manage tags on a Vultr Cloud GPU instance using the Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Cloud GPU instance to open its management page.
3. Navigate to the Tags tab.
4. Enter a new tag in the Add Tag field and click Add to apply the new tag.
5. Find and click Delete within the Existing Tags section to remove a
specific tag on your instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note the target
instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Instance endpoint to add new tags to
the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "tags" : ["tag1", "tag2"]
  }'
```
Vultr CLI
1. List all instances in your Vultr account and note the target instance's ID.
```bash
$ vultr-cli instance list
```
2. Add new tags to the instance.
```bash
$ vultr-cli instance tags <instance_id> --tags <tag1,tag2>
```
Terraform
1. Open your Terraform configuration for the existing Cloud GPU instance.
2. Update the tags  value in the instance resource to include the desired tags.
```hcl
resource "vultr_instance" "gpu" {
```
    # ...existing fields (region, plan, label, etc.)

tags = ["tag1", "tag2"]
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Networking
Manage your Vultr infrastructures network configurations, connections,
and security settings to optimize performance and accessibility.

Enable Firewall
Learn how to activate a Vultr Firewall Group to protect your Vultr Cloud
GPU instance from unauthorized access.

How to Enable a Vultr Firewall
Group on a Vultr Cloud GPU
Instance
Introduction
Vultr Firewall groups enable the creation of firewall rules to filter incoming traffic
on an instance's public network interface. Firewall rules consist of IPv4 or IPv6
port and service definitons to filter network traffic.
Follow this guide to enable a Vultr Firewall group on a Vultr Cloud GPU instance
using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target instance to open its management page.
3. Navigate to the Settings tab.
4. Click Firewall on the left navigation menu.
5. Click the Firewall drop-down to select a new firewall group.
6. Click Update Firewall Group to apply changes on the instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note the target
instance's ID in your output.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Firewall Groups endpoint to list all firewall
groups in your Vultr account.
```bash
$ curl "https://api.vultr.com/v2/firewalls" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PATCH  request to the Update Instance endpoint to attach a firewall
group to the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "firewall_group_id" : "<firewall-id>",
  }'
```
Vultr CLI
1. List all firewall groups in your Vultr account and note the target firewall
group's ID.
```bash
$ vultr-cli firewall group list
```
2. List all instances in your Vultr account and note the target instance's ID.
```bash
$ vultr-cli instance list
```
3. Attach the firewall group to the instance.
```bash
$ vultr-cli instance update-firewall-group --instance-id
<instance-id> --firewall-group-id <firewall-id>
```
Terraform
1. Open your Terraform configuration for the existing Cloud GPU instance.
2. Create or reference a vultr_firewall_group  resource and attach it to the
instance.
# Create a firewall group
resource "vultr_firewall_group" "web" {
description = "Web server firewall group"
}
# Add example rules to the group
resource "vultr_firewall_rule" "allow_http" {
firewall_group_id = vultr_firewall_group.web.id
protocol = "tcp"
ip_type = "v4"
subnet = "0.0.0.0"
subnet_size = 0
port = "80"
}
resource "vultr_firewall_rule" "allow_https" {
firewall_group_id = vultr_firewall_group.web.id
protocol = "tcp"
ip_type = "v4"
subnet = "0.0.0.0"
subnet_size = 0
port = "443"
}

# Attach the firewall group to the GPU instance
resource "vultr_instance" "gpu" {
    # ...existing fields (region, plan, os_id, label, etc.)
firewall_group_id = vultr_firewall_group.web.id
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

IPv4
Learn how to configure, assign, and manage IPv4 addresses on your Vultr
Cloud GPU instance.

How to Manage IPv4 on a Vultr
Cloud GPU Instance
Introduction
A public IPv4 network is available and attached to your Vultr Cloud Compute
instance after deployment unless disabled by default. You can attach multiple
IPv4 addresses on an instance to enable connections on the main public
networking interface.
Follow this guide to manage the IPv4 information on a Vultr Cloud GPU instance
using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target instance to open its management page.
3. Navigate to the Settings tab.
4. Click IPv4 on the left navigation menu to view your instance's public IPv4
network information.
5. Click Add Another IPv4 Address to attach another public IP address to
the instance.
6. Check the confirmation prompt and click Add IPv4 Address to attach the
new public IP address and restart your instance.
7. Click the default IPv4 reverse DNS value and replace it with your values to
enable reverse DNS on your instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note the target
instance's ID in your output.

```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Instance IPV4 Information endpoint to
view the instance's IPv4 information.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv4" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Create IPv4 endpoint to attach a new IPv4
address on the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv4" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "reboot" : true
  }'
```
4. Send a POST  request to the Create Instance Reverse IPv4 endpoint to
enable reverse DNS on the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv4/reverse" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{

    "ip" : "<ipv4-address>",
    "reverse" : "<domain>"
  }'
```
Vultr CLI
1. List all instances in your Vultr account and note the target instance's ID.
```bash
$ vultr-cli instance list
```
2. List the instance's IPv4 address information.
```bash
$ vultr-cli instance ipv4 list <instance-id>
```
3. Create a new public IPv4 address and attach it to the instance.
```bash
$ vultr-cli instance ipv4 create <instance-id> --reboot
```
4. Create a new IPv4 reverse DNS entry on the instance.
```bash
$ vultr-cli instance reverse-dns set-ipv4 <instance-id> --
entry <domain> --ip <ipv4-address>

IPv6
Learn how to configure and manage IPv6 connectivity on your Vultr Cloud
GPU instance.
```

How to Manage IPv6 on a Vultr
Cloud GPU Instance
Introduction
A public IPv6 network is available and attached to your Vultr Cloud Compute
instance after deployment unless disabled by default. You can manage the IPv6
address information on an instance and enable reverse DNS on the public
networking interface.
Follow this guide to manage the IPv6 information on a Vultr Cloud GPU instance
using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target instance to open its management page.
3. Navigate to the Settings tab.
4. Click IPv6 on the left navigation menu to view your instance's public IPv6
network information.
5. Enter your IPv6 address in the IP field and a domain in the Reverse DNS
field to enable reverse DNS on your instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note the target
instance's ID in your output.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Get Instance IPv6 Information endpoint to
view the instance's IPv6 information.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv6" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a GET  request to the Create Instance Reverse IPv6 endpoint to
create a new reverse DNS entry using the IPv6 address.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
ipv6/reverse" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "ip" : "<ipv6-address>",
    "reverse" : "<domain>"
  }'
```
Vultr CLI
1. List all instances in your Vultr account and note the target instance's ID.
```bash
$ vultr-cli instance list
```
2. List the instance's IPv6 network information.

```bash
$ vultr-cli instance ipv6 list <instance-id>
```
3. Create a new IPv6 reverse DNS entry on the instance.
```bash
$ vultr-cli instance reverse-dns set-ipv6 <instance-id> --
entry <domain> --ip <ipv6-address>
```
Terraform
Terraform can enable or disable IPv6 for a Cloud GPU instance at creation time.
Managing existing IPv6 addresses or reverse DNS records after deployment is
not supported directly in Terraform and must be done through the Vultr Console,
API, or CLI.
1. Open your Terraform configuration for the existing Cloud GPU instance.
2. Enable IPv6 on the instance and (optionally) set reverse DNS.
# Enable IPv6 on the instance
resource "vultr_instance" "gpu" {
    # ...existing fields (region, plan, os_id, label, etc.)
enable_ipv6 = true
}
# Optional: set reverse DNS for the instance's primary IPv6
# (v6 address is known after the instance exists)
resource "vultr_reverse_ipv6" "gpu_ptr" {
ip = vultr_instance.gpu.v6_main_ip
reverse = "host.example.com."
}
3. Apply the configuration and observe the following output:

Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Reserved IPs
Learn how to assign and manage Reserved IP addresses on your Vultr
Cloud GPU instances for static networking.

How to Attach Reserved IPs on a
Vultr Cloud GPU Instance
Introduction
Reserved IP addresses enable you to reserve a specific public IP address you
can attach to instances. You can attach multiple reserved IPs on a single
instance to enable new network interfaces.
Follow this guide to attach reserved IPs on a Vultr Cloud GPU instance using the
Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products, expand the Network group and click Reserved
IPs.
2. Click your target reserved IP to open its management page.
3. Click the Attach to Server drop-down and select your target Cloud GPU
instance.
4. Click Attach to apply the reserved IP to your Cloud GPU instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note the target
instance's ID in your output.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Reserved IPs endpoint and note the target
reserved IP's ID in your output.
```bash
$ curl "https://api.vultr.com/v2/reserved-ips" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Attach Reserved IP endpoint to attach the
reserved IP to the instance.
```bash
$ curl "https://api.vultr.com/v2/reserved-ips/{reserved-ip}/
attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "instance_id" : "<instance-id>"
  }'
```
Vultr CLI
1. List all reserved IPs in your Vultr account and note the target reserved IP's
ID.
```bash
$ vultr-cli reserved-ip list
```
2. List all instances in your Vultr account and note the target instance's ID.
```bash
$ vultr-cli instance list
```
3. Attach the reserved IP to the instance.
```bash
$ vultr-cli reserved-ip attach <reserved-ip-id> --instance-id <instance-id>
```
Terraform
1. Open your Terraform configuration for the existing Cloud GPU instance.
2. Update the reserved_ip_id  value in the instance resource to the ID of the
target reserved IP.
```hcl
resource "vultr_instance" "gpu" {
```
    # ...existing fields (region, plan, label, etc.)
reserved_ip_id = "your-reserved-ip-id"
}
Or create a new reserved IP in Terraform and attach it to the instance:
TERRAFORM
resource "vultr_reserved_ip" "gpu_ip" {
region = "del"
ip_type = "v4"
label = "gpu-reserved-ip"
}
resource "vultr_instance" "gpu" {
    # ...existing fields (region, plan, os_id, label, etc.)
reserved_ip_id = vultr_reserved_ip.gpu_ip.id
}
3. Apply the configuration and observe the following output:

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

VPC 2.0
A guide for connecting VPC 2.0 networks to Vultr Cloud GPU instances for
enhanced private networking capabilities.

VPC 2.0 Product Documentation
VPC 2.0 Product Documentation
How to Attach VPC 2.0 Networks a
Vultr Cloud GPU Instance
Introduction
A Virtual Private Cloud (VPC) 2.0 network enables a secure and isolated private
networking interface on your instance for communication with other instances
on the same network. You can attach multiple VPC 2.0 networks to enable
communication between an instance and other nodes attached to the same
network.
Follow this guide to attach VPC 2.0 networks on a Vultr Cloud GPU instance
using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target instance to open its management page.
3. Navigate to the Settings tab.
4. Click VPC 2.0 on the left navigation menu.
5. Click Enable VPC 2.0 to activate a new VPC 2.0 network interface.
6. Click Enable VPC 2.0 in the confirmation prompt to apply changes and
attach a new VPC 2.0 network to your instance.
7. Click the VPC 2.0 drop-down to select a specific network and click Attach
to apply changes.
Vultr API
1. Send a GET request to the List Instances endpoint and note the target
instance's ID in your output.

VPC 2.0 Product Documentation
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Instance VPC 2.0 Networks endpoint to
list all VPC 2.0 networks in your Vultr account and note the target VPC 2.0
network's ID.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
vpc2" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Attach VPC 2.0 to Instance endpoint to
attach the VPC 2.0 network to the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
vpc2/attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "vpc_id": "<vpc-id>"
  }'
```
Vultr CLI
1. List all instances available in your Vultr account and note the target
instance's ID.
```bash
VPC 2.0 Product Documentation
$ vultr-cli instance list
```
2. List all VPC 2.0 networks in your Vultr account and note the target VPC 2.0
network's ID.
```bash
$ vultr-cli vpc2 list
```
3. Attach the VPC 2.0 network to the instance.
```bash
$ vultr-cli vpc2 nodes attach <vpc2-id> \
--nodes="<instance-id>"
```
Terraform
1. Open your Terraform configuration for the existing Cloud GPU instance.
2. Create (or reference) a VPC 2.0 network and attach it to the instance.
# Create a new VPC 2.0 network
resource "vultr_vpc2" "private_net" {
region = "del"
description = "Private network for GPU workloads"
}
# Attach the VPC 2.0 network to the GPU instance
resource "vultr_instance" "gpu" {
    # ...existing fields (region, plan, os_id, label, etc.)
vpc2_ids = [vultr_vpc2.private_net.id]
}
3. Apply the configuration and observe the following output:

VPC 2.0 Product Documentation
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

VPC
A private network solution that allows secure communication between
Vultr instances within the same region

How to Attach VPC Networks on a
Vultr Cloud GPU Instance
Introduction
A Virtual Private Cloud (VPC) network enables a secure and isolated private
networking interface on your instance for communication with other instances
in the same network. You can attach multiple VPC networks to enable
communication between an instance and other nodes attached to the same
network.
Follow this guide to attach VPC networks on a Vultr Cloud GPU instance using
the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target instance to open its management page.
3. Navigate to the Settings tab.
4. Click IPv4 on the left navigation menu.
5. Click the VPC Network drop-down, select a Vultr VPC network and click
Attach.
6. Click Attach VPC in the confirmation prompt to apply changes to your
instance.
Vultr API
1. Send a GET request to the List Instances endpoint and note the target
instance's ID in your output.

```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List VPCs endpoint to list all VPCs in your Vultr
account and note the target VPC network's ID.
```bash
$ curl "https://api.vultr.com/v2/vpcs" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Attach VPC to Instance endpoint to attach
the VPC network to the instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
vpcs/attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "vpc_id": "<vpc-id>"
  }'
```
Vultr CLI
1. List all instances in your Vultr account and note the target instance's ID.
```bash
$ vultr-cli instance list
```
2. List all VPC networks in your Vultr account and note the target VPC
network's ID.
```bash
$ vultr-cli vpc list
```
3. Attach the VPC network to the instance.
```bash
$ vultr-cli instance vpc attach <instance-id> --vpc-id="<vpc-id>"
```
Terraform
1. Open your Terraform configuration for the existing Cloud GPU instance.
2. Create (or reference) a VPC network and attach it to the instance.
# Create a new VPC network
resource "vultr_vpc" "private_net" {
region = "del"
description = "Private network for GPU workloads"
}
# Attach the VPC network to the GPU instance
resource "vultr_instance" "gpu" {
    # ...existing fields (region, plan, os_id, label, etc.)
vpc_ids = [vultr_vpc.private_net.id]
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

FAQ
Frequently asked questions and answers about Vultr services, features,
and common issues.

Frequently Asked Questions (FAQs)
About Cloud GPU
Introduction
These are the frequently asked questions for Vultr Cloud GPU instances.
How can I access a Vultr Cloud GPU
instance?
You can access a Vultr Cloud GPU instance depending on its operating system.
Use SSH or the Vultr Console for Linux instances and the Remote Desktop
Protocol for Windows instances.
Can I run AI and machine learning
applications on Vultr Cloud GPUs?
Yes, you can run AI and machine learning applications on a Vultr Cloud GPU.
Specific applications may require specific GPU requirements, ensure to visit
your application's documentation to verify the required resources.
Can I upgrade a Vultr Cloud GPU instance?
No, you cannot upgrade a Vultr Cloud GPU instance.

Does a Vultr Cloud GPU instance incur any
charges when stopped?
Yes, an instance incurs normal charges as it would when active. Destroy the
instance to avoid incurring additional charges.
Can I change my Vultr Cloud GPU instance
GPU device type?
No, you cannot change your Vultr Cloud GPU instance's GPU device type after
deployment.

Bare Metal
High-performance dedicated physical servers with no virtualization layer,
offering maximum control and resources for demanding workloads.

Provisioning
A guide explaining how to set up and deploy Vultr Bare Metal server
instances.

How to Provision Vultr Bare Metal
Instances
Introduction
Vultr Bare Metal instances are single-tenant dedicated cloud servers designed
for applications with the most demanding performance and security
requirements. Bare Metal instances don't use any virtualization and include an
operating system that enables you to run applications on the specified server
hardware.
Follow this guide to provision Vultr Bare Metal instances using the Vultr Console,
API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Compute on the list of product options.
2. Click Deploy to access the Deploy New Instance page.
3. Select Bare Metal from the list of options.
4. Choose your desired Vultr location to deploy the Bare Metal instance.
5. Select your Bare Metal instance specifications from the list of available
Vultr plans.
6. Click Configure Software.
7. Select a cloud image to install on your instance based on the following
options:
- Operating System: Installs a fresh operating system image on the
instance.

- Marketplace Apps: Install a prebuilt software stack or application
with the recommended operating system image.
- iPXE: Allows you to boot your instance using remote disk images or
scripts.
8. Select optional Server Settings to apply on the instance.
- SSH Keys: Installs a specific SSH key on the instance.
- Startup Script: Enables a startup script to execute at deployment or
a PXE script to automate the operating system installation.
- Firewall Group: Activates a Vultr Firewall group to filter incoming
network traffic on the instance.
9. Select the Bare Metal instance Disk configuration based on the following
options:
- RAID 1: Configures disks in a software RAID 1 array for data
redundancy.
- No RAID: Formats and mounts disks individually without RAID
configuration.
- No RAID (Extra disks unformatted): Leaves additional disks
unformatted for manual configuration.
10. Enter a new hostname in the Server Hostname field and a descriptive
label in the Server Label field to identify the instance.
11. Configure Additional Features for the instance.
- Instance Connectivity: Select how the instance connects to the
internet.
▪ Instance(s) with Public IP: Assigns public IP addresses directly
to the instance. Under Instance Address, Public IPv4 is
enabled by default. Select Public IPv6 to enable IPv6
addressing. After selecting IPv6, you can optionally deselect
Public IPv4 to create an IPv6-only instance.
▪ Private Instance(s) behind NAT Gateway: Routes internet
traffic through a NAT Gateway in a Virtual Private Cloud (VPC)
Network. Select an existing VPC Network with a NAT Gateway or
click Add VPC Network to create a new one.

- VPC Network: Connects the instance to a VPC Network in the current
location.
- Limited User Login: Creates a linuxuser non-root user with sudo
privileges as the default user account instead of root .
12. Click Deploy to provision the instance.
Vultr API
1. Send a POST request to the Create Bare Metal Instance endpoint to
create a new Vultr Bare Metal instance. Replace VULTR_LOCATION ,
INSTANCE_PLAN , OS_ID , INSTANCE_LABEL , and HOSTNAME with your target values.
```bash
$ curl "https://api.vultr.com/v2/bare-metals" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
"region" : "VULTR_LOCATION",
"plan" : "INSTANCE_PLAN",
"os_id" : OS_ID,
"label" : "INSTANCE_LABEL",
"hostname": "HOSTNAME"
}'
```
Visit the Create Bare Metal Instance API page to view additional
attributes you can apply on the Vultr Bare Metal instance.
Vultr CLI
1. Create a new Vultr Bare Metal instance. Replace VULTR_LOCATION ,
INSTANCE_PLAN , OS_ID , INSTANCE_LABEL , and HOSTNAME with your target values.
```bash
$ vultr-cli bare-metal create --region VULTR_LOCATION --plan
INSTANCE_PLAN --os OS_ID --label INSTANCE_LABEL --hostname
HOSTNAME
```
Run vultr-cli bare-metal create --help  to view additional options you can
apply on the Vultr Bare Metal instance.
Terraform
1. Ensure the Vultr Terraform provider is configured in your Terraform project.
2. Add the Bare Metal instance resource to your Terraform configuration.
```hcl
terraform {
required_providers {
vultr = {
source = "vultr/vultr"
version = "~> 2.26"
}
}
}
provider "vultr" {}
resource "vultr_bare_metal_server" "bm" {
region = "del"                   # Target
deployment region
plan =
"vbm-4c-32gb"           # Bare Metal plan ID
os_id = 2284                    # Ubuntu 24.04
LTS x64
label = "baremetal-instance-1"
hostname = "baremetal-instance-1"
enable_ipv6 = true
}
output "public_ip" {
value = vultr_bare_metal_server.bm.main_ip
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Connection
Establish and manage connections to your Vultr resources through
various networking and access methods.

OpenSSH
A secure connection protocol pre-installed on Vultr Bare Metal instances
for remote SSH access.

How to Connect to a Vultr Bare
Metal Instance Using OpenSSH
Introduction
OpenSSH is a connection protocol that enables SSH access on a server. It's
available and active on Vultr Bare Metal instances by default to enable secure
connections.
Follow this guide to connect to a Vultr Bare Metal instance using SSH on your
workstation.
Connect to an Instance Using the Default
User Credentials
1. Access your Vultr Bare Metal instance's management page.
2. Note the default credentials within the Overview tab and copy the user
password to your clipboard.
3. Open a new terminal window on your workstation.
4. Connect to your Vultr Bare Metal instance using SSH.
```bash
$ ssh username@SERVER-IP
```
5. Enter yes and press Enter when prompted to add the instance's public key
to your known hosts.
The authenticity of host '192.0.2.123 (192.0.2.123)' can't be established.
ED25519 key fingerprint is SHA256:gTAOuCiCa3Us4tpVaVHVk9d3qOjKrsqXPOsAFQbB8xw.

This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
6. Paste your instance password when prompted and press Enter to log in.
username@SERVER-IP's password:
7. View the active user information in your SSH session.
```bash
$ whoami
Connect to an Instance Using SSH Keys
```
Note
Generate an SSH key on your workstation and add it to your instance before
deployment. Adding an SSH key to an existing instance will result in data loss
and wipe your instance to install the new key.
1. Open a new terminal window on your workstation.
2. Connect to your instance using a specific SSH key on your workstation.
```bash
$ ssh -i /path/to/private/key username@SERVER-IP
```
3. Enter yes and press Enter when prompted to add the instance's public key
to your known hosts.
The authenticity of host '192.0.2.123 (192.0.2.123)' can't be established.
ED25519 key fingerprint is SHA256:gTAOuCiCa3Us4tpVaVHVk9d3qOjKrsqXPOsAFQbB8xw.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
4. View the active user information in your SSH session.

```bash
$ whoami

Putty
A guide for establishing SSH connections to Vultr Bare Metal servers
using PuTTY, a popular Windows SSH client.
```

How to Connect to a Vultr Bare
Metal Instance using Putty
Introduction
Putty is an SSH client for Windows workstations. It provides a unique
management panel and terminal to connect to instances using SSH. Putty
supports password-based authentication and SSH keys to connect to an
instance.
Follow this guide to connect to a Vultr Bare Metal instance using Putty on
Windows.
Connect to an Instance Using the Default
User Credentials
1. Open Putty from your applications menu.
2. Enter your instance's public IP address in the Host Name (or IP address)
field.
3. Keep 22 as the Port value and SSH as the connection type.
4. Click Open to connect to your instance using SSH.
5. Click Accept when prompted to add the instance's public key to your
workstation's known hosts.
6. Enter your instance username as the login as value.
7. Enter your user password when prompted and press Enter to log in.
8. View the active user information in your SSH session.

```bash
$ whoami
Connect to an Instance Using SSH Keys
```
1. Enter your instance's public IP address in the Host Name (or IP address)
field.
2. Keep 22 as the Port and SSH as the connection type.
3. Expand the SSH group on the main navigation menu to access additional
connection options.
4. Expand the Auth group and select Credentials from the list of options.
5. Click Browse within the Private key file for authentication field to load
your private key.
6. Click Data within the Connection group and enter the default instance
username in the Auto-login username field to use with your SSH key.
7. Navigate to Session on the main navigation menu and enter a new
session name in the Saved Sessions field.
8. Click Save to store your SSH key, user, and the instance IP configurations.
9. Click Open to connect to the instance using the SSH key session
information.
10. Click Accept when prompted to add the instance's public key to your
workstation's known hosts.
11. View the active user information in your SSH session.
```bash
$ whoami
```

Vultr Console
Access your Bare Metal instance through Vultrs browser-based console for
remote management without SSH.

How to Connect to a Vultr Bare
Metal Instance using the Vultr
Console
Introduction
Vultr Console is a noVNC terminal that provides direct console access to
instances. You can access the instance terminal, run commands, install
applications and manage processes using the Vultr Console. In addition, Vultr
Console supports multiple tools to enable clipboard sharing, virtual keyboard,
and special commands such as Ctrl Alt Del.
Follow this guide to connect to a Vultr Bare Metal instance using the Vultr
Console.
Note
Allow pop-ups in your web browser settings to enable access to the Vultr
Console.
1. Open the Vultr Console.
2. Navigate to Products and click Compute.
3. Click your target Bare Metal instance to open its management page.
4. Note the default credentials within the Overview tab and copy the user
password to your clipboard.
5. Find and click View Console on the top-right navigation menu to open the
Vultr console.
6. Enter your default username and press Enter when prompted.
7. Find and click Send Clipboard on the list of control bar options to paste
your instance password in the Vultr Console session.
8. Press Enter to log in to the instance.

Features
Explore Vultr's comprehensive suite of cloud infrastructure capabilities
and service offerings.

Cloud-Init
A guide for modifying the automated initialization data on Vultr Bare
Metal servers after deployment.

Cloud-Init Product Documentation
Cloud-Init Product Documentation
How to Update Cloud-Init User Data
on a Vultr Bare Metal Instance
Introduction
Cloud-Init enables the automatic initialization and configuration of instances
during the initial boot phase. Cloud-Init user data runs a specific script's
contents to automate the instance customization, software installation and
configuration of specific packages or services.
Follow this guide to update Cloud-Init user data on a Vultr Bare Metal instance
using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target instance to open its management page.
3. Navigate to the User-Data tab.
4. Enter a script or cloud config in the Cloud-Init User-Data field.
5. Click Update to apply changes.
Vultr API
1. Send a GET request to the List Bare Metal Instances endpoint and note
your target instance's ID.
$ curl "https://api.vultr.com/v2/bare-metals" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"

Cloud-Init Product Documentation
2. Send a PATCH  request to the Update Bare Metal endpoint to update the
Cloud-Init user data on the instance.
```bash
$ curl "https://api.vultr.com/v2/bare-metals/{baremetal-id}"
\
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "user_data" : "<cloud-init-data>"
  }'
```
Vultr CLI
1. List all Bare Metal instances available in your Vultr account and note the
target instance's ID.
```bash
$ vultr-cli bare-metal list
```
2. Upload new Cloud-Init user data to the instance using a file on your
workstation.
```bash
$ vultr-cli bare-metal user-data set <instance-id> --
userdata "<script-path>"
```
Terraform
Cloud-Init user data can only be set during instance creation in Terraform and
cannot be updated on an existing Bare Metal instance without recreating it.
1. Open your Terraform configuration for the new Bare Metal instance.

Cloud-Init Product Documentation
2. Add the user_data argument to the Bare Metal resource to run a script at
first boot.
```hcl
resource "vultr_bare_metal_server" "bm" {
```
# ...existing fields (region, plan, label, etc.)
user_data = <<-EOT
#cloud-config
packages:
- nginx
runcmd:
- systemctl enable --now nginx
EOT
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Explore GPU Variants
A comprehensive guide to Vultr's Bare Metal GPU options for high-performance computing tasks like AI, machine learning, and 3D
rendering.

Explore GPU Variants for Vultr Bare
Metal
Introduction
Vultr offers a wide range of Bare Metal GPU options to meet different user
needs. These powerful GPUs help users handle demanding tasks such as
machine learning, artificial intelligence, 3D rendering, and complex simulations.
With Vultr's bare metal resources, developers can create and launch new
applications more effectively, benefiting from direct access to dedicated
hardware for maximum performance and control.
This article explains the six different Vultr Bare Metal GPU offerings: A100
Tensor Core (PCIe and SXM), L40S, H100 Tensor Core, GH200 Superchip, and
AMD Instinct™ MI300X. You will gain an understanding of the core differences
between these GPU variants, helping you make the best choice for a specific
workload.
GPU Specifications and Performance
Overview
This section provides the necessary technical and performance data to compare
the 6 different GPUs based on their CUDA Cores/Stream Processors, Tflops
performance, parallel processing.
Below are the stats of the different Bare Metal GPUs Vultr offers to compare
performances:

CUDA Cores/ Tensor/ FP8 /
GPU Architecture
Variant Stream Matrix FP16
Memory Type
Processors Cores (Dense)
NVIDIA A100 312
NVIDIA
Tensor Core 6912 432 TFLOPS 80 GB
Ampere
GPU - PCIe (FP16)
NVIDIA A100 312
NVIDIA
Tensor Core 6912 432 TFLOPS 80 GB
Ampere
GPU - SXM (FP16)
366
NVIDIA L40S NVIDIA ADA
18716 568 TFLOPS 48 GB
GPU Lovelace
(FP16)
1979
NVIDIA H100
18432 640 TFLOPS 80 GB NVIDIA Hopper
GPU
(FP8)
1979
NVIDIA GH200
18432 640 TFLOPS 80 GB NVIDIA Hopper
Superchip
(FP8)
AMD 1.6
Instinct™ 19456 1216 PFLOPS 192 GB AMD CDNA 3
MI300X GPU (FP8)
NVIDIA HGX 4.5
NVIDIA
B200 (per 18432 576 PFLOPS 192 GB
Blackwell
GPU) (FP8)
AMD 5.0
Instinct™ 16384 1024 PFLOPS 288 GB AMD CDNA 4
MI355X GPU (FP8)
Key Terms
1. CUDA Cores: These are specific type of processing unit designed to work
with NVIDIA's CUDA programming model, they play a fundamental role in
parallel processing and accelerating various computing tasks focused on
graphics rendering. They often use a Single Instruction, Multiple Data
(SIMD) architecture so that a single instruction is executed simultaneously

on multiple data elements, resulting a high throughput in parallel
computing.
2. Stream Processors: These are the core computational units in AMD
GPUs, designed to handle parallel processing tasks such as graphics
rendering, general-purpose computation, and AI workloads. Stream
Processors also operate on a Single Instruction, Multiple Data (SIMD)
architecture, where a single instruction is executed across multiple data
points simultaneously.
3. Tensor Cores: These are specialized hardware component in the NVIDIA
GPUs made for accelerating matrix-based computations that are commonly
used in deep learning and many artificial intelligence workloads. They are
optimized for mathematical operations involved in neural network training
and inference by taking advantage of their mixed precision computing,
where certain part of the calculations with higher precision and the rest
with half precision while maintaining the accuracy in results by using error
correction and accumulation.
4. Matrix Cores: These are specialized hardware units integrated into AMD's
Instinct™ GPUs, specifically designed to accelerate matrix-based
computations central to artificial intelligence (AI) and high-performance
computing (HPC). Optimized for mixed-precision arithmetic, Matrix Cores
handle operations like matrix multiplications at exceptional speeds by
leveraging data types such as FP16, BF16, and INT8.
5. Tflops: Also known as TeraFLOPS, used to quantify the performance of a
system in floating-point operations per second, it involves floating-point
operation involving mathematical calculations using numbers with decimal
points. It is a useful indicator for comparing the capabilities of different
hardware components. High-performance computing applications like
simulations heavily rely on Tflops.
GPU Briefs
• NVIDIA A100 Tensor Core - PCIe: Vultr Bare Metal GPU, powered by the
NVIDIA A100 Tensor Core in PCIe format, is suitable for tasks such as AI
training and deep learning. This version connects through the PCIe
interface, making it compatible with many server setups. With its strong

processing capabilities and high memory bandwidth, it helps businesses
efficiently manage large datasets and complex models while supporting
scalable infrastructure. Learn more about Vultr Bare Metal A100.
• NVIDIA A100 Tensor Core - SXM: Vultr Bare Metal GPU, powered by the
NVIDIA A100 Tensor Core in SXM format, is optimized for high-performance
AI and data science workloads. This configuration allows for better power
delivery and thermal management, leading to enhanced performance. It is
ideal for training large neural networks and running extensive
computational tasks, helping organizations improve their efficiency and
output. Learn more about Vultr Bare Metal GPU A100.
• NVIDIA L40S: Vultr Bare Metal GPU, powered by the NVIDIA L40S, is built
for advanced graphics and AI applications. It offers strong performance for
tasks like 3D rendering, AI inference, and video processing. With its high
memory capacity and efficient processing, the L40S helps businesses
deliver detailed graphics and handle complex data tasks effectively. Learn
more about Vultr Bare Metal GPU L40S.
• NVIDIA H100 Tensor Core: Vultr Bare Metal GPU, powered by the NVIDIA
H100, is designed for next-generation AI workloads, including large
language model training and inference. With advanced architecture and
powerful tensor cores, the H100 enables organizations to achieve higher
performance and efficiency for demanding applications. It is ideal for
research and complex tasks that require significant computational
resources. Learn more about Vultr Bare Metal GPU H100.
• NVIDIA GH200 Superchip: Vultr Bare Metal GPU, powered by the NVIDIA
GH200 Superchip, combines multiple GPU components for extreme
performance in AI and high-performance computing. This design allows for
enhanced scalability and efficiency, making it suitable for complex tasks
that demand substantial computing power. It is ideal for large-scale AI
deployments, scientific simulations, and data analytics. Learn more about
Vultr Bare Metal GH200 Superchip.
• AMD Instinct™ MI300X: Vultr Bare Metal GPU, powered by the AMD
Instinct™ MI300X, is designed for cutting-edge AI and high-performance
computing (HPC) applications. With advanced memory bandwidth and
support for large-scale models, the MI300X delivers exceptional

performance for training and inference in AI and deep learning tasks. This
GPU is ideal for organizations seeking scalable and efficient solutions for
complex data processing and scientific simulations. Learn more about Vultr
Bare Metal AMD Instinct™ MI300X.
• AMD Instinct™ MI355X: Vultr Bare Metal GPU, powered by the AMD
Instinct™ MI355X, is built for next-generation AI, deep learning, and high-performance computing workloads. Featuring the latest CDNA 4
architecture, the MI355X offers industry-leading memory capacity with 288
GB HBM3e per GPU, combined with powerful FP8 and FP4 compute for
training and inference of very large models. Its design emphasizes memory
bandwidth and compute efficiency, making it ideal for generative AI, LLMs,
and large-scale scientific simulations. Learn more about Vultr Bare Metal
AMD Instinct™ MI355X.
• NVIDIA HGX B200: Vultr Bare Metal GPU, powered by the NVIDIA HGX
B200, represents the next generation of AI acceleration with the Blackwell
architecture. Designed for massive-scale AI workloads, including
generative AI, LLM training, and scientific computing, the B200 delivers
breakthrough performance with FP8 and FP4 precision. With up to 192 GB
of ultra-fast HBM3e memory per GPU and massive memory bandwidth, it
enables efficient training and deployment of the largest models. Its NVLink-powered architecture supports seamless multi-GPU scaling for enterprise
AI workloads. Ideal for cutting-edge research, AI inference at scale, and
data-intensive computing. Learn more about Vultr Bare Metal NVIDIA HGX
B200.

GPU Enabled Images
Pre-configured operating system templates optimized for GPU-accelerated computing workloads on Vultr's platform.

Vultr GPU Enabled Images
Introduction
Vultr GPU Enabled images for Vultr Bare Metal instances streamline the
development of Artificial Intelligence (AI) and Machine Learning (ML) projects by
providing pre-installed software tailored to specific GPU providers.
This results in reduced time required to set up the server before you can use it
for operations like building, fine-tuning, or inferring a model. We ensure that the
pre-installed softwares are tested on our infrastructure and are reliable for all
your AI/ML development needs.
Softwares Included in Vultr GPU Enabled
Images for Vultr Bare Metal Instances
Specific to AMD
• AMD GPU Drivers: These are software components that enable
communication between an AMD graphics card and the operating system.
These drivers are crucial for ensuring optimal performance, compatibility,
and stability across a variety of applications, including gaming,
professional graphics, and compute workloads.
• ROCm Software Stack: It is a software stack is AMD's open-source
platform designed to enable High-Performance computing (HPC), Artificial
Intelligence (AI), and Machine Learning (ML) applications on AMD GPUs.
ROCm provides a comprehensive ecosystem that includes libraries, tools,
and frameworks for GPU-accelerated workloads, supporting languages
such as Python, C++, and Fortran.
• Docker: It is a platform for developing, shipping, and running applications
inside containers.

Softwares Included in Vultr GPU Enabled
Images for Vultr Bare Metal Instances
Specific to NVIDIA
• NVIDIA GPU Drivers: They ensure to enable your computer to utilize the
NVIDIA GPUs making them function properly.
• NVIDIA CUDA Toolkit: It is also a set of programming tools and libraries
to utilize the potential of NVIDIA GPUs, allowing users to speed up
computation and parallel processing tasks.
• NVIDIA Container Toolkit: It is a suite of tools, libraries, and runtime
components provided by NVIDIA that enables the use of NVIDIA GPUs
within containerized environments.
• Docker: It is a platform for developing, shipping, and running applications
inside containers.
More Resources
• Explore Vultr Bare Metal GPU Variants
• Provision Vultr Bare Metal Instances
• Manage Vultr Bare Metal Instances

FAQ
Frequently asked questions and answers about Vultr's products, services,
and platform features.

Frequently Asked Questions (FAQs)
About Bare Metal
Introduction
These are the frequently asked questions for Vultr Bare Metal instances.
How do Vultr Bare Metal instances differ
from Vultr Cloud Compute instances?
Bare Metal instances offer direct access to dedicated servers without any
virtualization layer while Vultr Cloud Compute instances are deployed in a
virtualized cloud environment. Bare Metal grants you unrestricted access to the
underlying physical servers making the instances suitable for most resource
intensive workloads.
Can I install custom software and drivers on
a Vultr Bare Metal instance?
Yes, you can install custom software and drivers on a Vultr Bare Metal instance.
You can use Cloud-Init to enable the automatic installation of specific packages
during the initial boot phase.
Can I upgrade a Vultr Bare Metal instance?
No, you cannot upgrade a Vultr Bare Metal instance.

Does a Vultr Bare Metal instance incur any
charges when stopped?
Yes, a stopped instance incurs normal charges as it would while running.
However, the instance does not incur any charges when destroyed which may
lead to data loss.
What operating systems are supported for
Vultr Bare Metal instances?
All operating systems except for OpenBSD and FreeBSD images are supported
on Vultr Bare Metal instances. Use the iPXE boot feature to install a custom
operating system on your instance.

Management
Tools and features for administering, monitoring, and controlling your
Vultr infrastructure and resources.

Change Hostname
Learn how to change the hostname on your Vultr Bare Metal server to
improve system identification and network management.

How to Manage Change the
Hostname on a Vultr Bare Metal
Instance
Introduction
Changing the default hostname on an instance modifies the default server
configuration and reinstalls the operating system.
Follow this guide to change the hostname on a Vultr Bare Metal instance using
the Vultr Console, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Bare Metal instance name to open its management page.
3. Navigate to the Settings tab.
4. Click Change Hostname on the left navigation menu.
5. Replace the existing value with your new hostname.
6. Check the confirmation prompt and click Change Hostname to apply your
new hostname changes.
Terraform
1. Open your Terraform configuration for the existing Bare Metal instance.
2. Update the hostname value in the instance resource to the new hostname.
```hcl
resource "vultr_bare_metal_server" "bm1" {
```
    # ...existing fields (region, plan, label, os_id, etc.)
hostname = "new-hostname"
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 1 destroyed.

Change OS
Learn how to reinstall or change the operating system on your Vultr Bare
Metal server instance.

How to Change the Operating
System on a Vultr Bare Metal
Instance
Introduction
Changing the instance operating system wipes all data on your server and
installs a new file system. This is important when changing your default
operating system while maintaining your instance's IP networking information.
Follow this guide to change the operating system on a Vultr Cloud Compute
instance using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Bare Metal instance to open its management page.
3. Navigate to the Settings tab.
4. Click Change OS on the left navigation menu.
5. Click the OS drop-down to select a new operating system and the default
RAID configuration.
6. Click Change OS to apply the new operating system.
7. Check the confirmation prompt and click Change OS to reinstall the
instance with a new operating system.
Vultr API
1. Send a GET request to the List Bare Metal Instances endpoint and note
the target instance's ID.

```bash
$ curl "https://api.vultr.com/v2/bare-metals" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List OS endpoint to view all available operating
systems and note the target OS ID.
```bash
$ curl "https://api.vultr.com/v2/os" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PATCH  request to the Update Bare Metal endpoint with a new
 value to change the instance's operating system.
os_id
```bash
$ curl "https://api.vultr.com/v2/bare-metals/{baremetal-id}"
\
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "os_id" : "<new-instance-os-id>"
  }'
```
Vultr CLI
1. List all Bare Metal instances in your Vultr account and note the target
instance's ID.
```bash
$ vultr-cli bare-metal list
```
2. List all available operating systems and note the target OS ID.
```bash
$ vultr-cli bare-metal os list <baremetal-id>
```
3. Change the target instance's operating system.
```bash
$ vultr-cli bare-metal os change <instance-id> --os <os_id>
```
Terraform
1. Open your Terraform configuration for the existing Bare Metal instance.
2. Update the os_id  value in the instance resource to the new operating
system.
```hcl
resource "vultr_bare_metal_server" "bm1" {
```
    # ...existing fields (region, plan, label, hostname,
etc.)
os_id = 2284  # New OS ID
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 1 destroyed.

Destroy Instance
Learn how to permanently delete a Vultr Bare Metal Instance and all
associated data from your account.

How to Destroy a Vultr Bare Metal
Instance
Introduction
Destroying an instance removes the public IP address and deletes the server
from your Vultr account. Destroying an instance cannot be reversed and any
instance data cannot be recovered unless a backup or snapshot is available in
your Vultr account.
Follow this guide to destroy a Vultr Bare Metal instance using the Vultr Console,
API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Bare Metal instance to open its management page.
3. Click Destroy Server on the top-right navigation menu to destroy the
Bare Metal server instance.
4. Check the confirmation prompt and click Destroy Server to apply
changes.
Vultr API
1. Send a GET request to the List Bare Metal Instances endpoint and note
the target instance's ID.
```bash
$ curl "https://api.vultr.com/v2/bare-metals" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete Bare Metal endpoint to destroy the
instance.
```bash
$ curl "https://api.vultr.com/v2/bare-metals/{baremetal-id}"
\
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all Bare Metal instances available in your Vultr account and note the
target instance's ID.
```bash
$ vultr-cli bare-metal list
```
2. Destroy the instance.
```bash
$ vultr-cli bare-metal delete <instance_id>
```
Terraform
1. Open your Terraform configuration and locate the Bare Metal server
resource.
2. Remove the resource block or destroy it by target.

```hcl
resource "vultr_bare_metal_server" "bm1" {
label = "bm1"
region = "ewr"
plan = "vbm-4c-32gb"
os_id = 2284
hostname = "bm1"
}
```
# To delete, either remove this block from configuration
# or run: terraform destroy -target
vultr_bare_metal_server.bm1
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 0 changed, 1 destroyed.

Monitor Instance
Learn how to access and interpret performance metrics for your Vultr
Bare Metal instance to track resource usage and system activity.

How to Monitor a Vultr Bare Metal
Instance
Introduction
Monitoring an instance provides information about performance and usage
statistics. This enables you to keep track of your instance activity and usage
ratio depending on the running services.
Follow this guide to monitor a Vultr Bare Metal instance using the Vultr Console,
API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Bare Metal instance to open its management page.
3. View the instance usage summary within the Overview section.
4. Navigate to the Usage Graphs tab to monitor your instance usage
statistics.
5. Monitor the instance bandwidth usage statistics within the Monthly
Bandwidth section.
Vultr API
1. Send a GET request to the List Bare Metal Instances endpoint and note
the target instance's ID.
```bash
$ curl "https://api.vultr.com/v2/bare-metals" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Bare Metal Bandwidth endpoint to monitor
the target instance's bandwidth usage statistics.
```bash
$ curl "https://api.vultr.com/v2/bare-metals/{baremetal-id}/
bandwidth" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all instances in your Vultr account and note the target instance's ID.
```bash
$ vultr-cli bare-metal list
```
2. Monitor the instance's bandwidth usage statistics.
```bash
$ vultr-cli bare-metal bandwidth <instance-id>

Reinstall Instance
Learn how to reinstall the operating system on your Vultr Bare Metal
instance while preserving your IP address and hostname.
```

How to Reinstall a Vultr Bare Metal
Instance
Introduction
Reinstalling a Vultr Bare Metal instance wipes the server file system, resets all
configurations and reinstalls the operating system. Any data available on the
instance's file system is permanently deleted and cannot be recovered unless
backed up.
Follow this guide to reinstall a Vultr Bare Metal instance using the Vultr Console,
API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Bare Metal instance to open its management page.
3. Click Server Reinstall on the top-right navigation menu to reinstall the
server's file system.
4. Check the confirmation prompt and click Reinstall Server to apply
changes.
Vultr API
1. Send a GET request to the List Bare Metal Instances endpoint and note
the target instance's ID.
```bash
$ curl "https://api.vultr.com/v2/bare-metals" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Reinstall Bare Metal endpoint to reinstall the
instance with a new hostname.
```bash
$ curl "https://api.vultr.com/v2/bare-metals/{baremetal-id}/
reinstall" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}"
  --data '{
    "hostname" : "<new-baremetal-hostname>"
  }'
```
Vultr CLI
1. List all Bare Metal instances available in your Vultr account and note the
target instance's ID.
```bash
$ vultr-cli bare-metal list
```
2. Reinstall the instance with a new hostname.
```bash
$ vultr-cli bare-metal reinstall --host
<new_instance_hostname> <instance_id>
```
Terraform
1. Open your Terraform configuration for the existing Bare Metal instance.

2. Trigger a reinstall by replacing the instance during apply.
```bash
$ terraform apply -replace=vultr_bare_metal_server.bm1
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 1 destroyed.

Restart Instance
Learn how to properly restart your Vultr Bare Metal instance when
needed.

How to Restart a Vultr Bare Metal
Instance
Introduction
Restarting an instance performs a hard reboot and stops all running processes
on your server before starting them again. Restarting does not alter the
instance data or file system and enables the application of updates or
configuration changes that require a reboot.
Follow this guide to restart a Vultr Bare Metal instance using the Vultr Console,
API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Bare Metal instance to open its management page.
3. Click Server Restart on the top-right navigation menu to restart your
server.
4. Click Restart Server in the confirmation prompt to apply changes.
Vultr API
1. Send a GET request to the List Bare Metal Instances endpoint and note
the target instance's ID.
```bash
$ curl "https://api.vultr.com/v2/bare-metals" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Reboot Bare Metal endpoint to restart the
instance.
```bash
$ curl "https://api.vultr.com/v2/bare-metals/{baremetal-id}/
reboot" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all Bare Metal instances available in your Vultr account and note the
target instance's ID.
```bash
$ vultr-cli bare-metal list
```
2. Restart the instance.
```bash
$ vultr-cli bare-metal restart <instance_id>

Startup Script
Learn how to modify the startup script that runs when your Vultr Bare
Metal instance boots up
```

How to Change the Startup Script
on a Vultr Bare Metal Instance
Introduction
Startup scripts enable you to run specific configurations to automate the
operating system installation processes. Changing the startup script on an
active instance wipes the file system and reinstalls the operating system.
Follow this guide to change the startup script on a Vultr Bare Metal instance
using the Vultr Console, or Terraform
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target instance to open its management page.
3. Navigate to the Settings tab.
4. Find and click Change StartUp Script on the left navigation menu.
5. Enter a new script name in the name field and click the Type drop down to
set the script type.
6. Enter your startup script data in the Script field and click Add Script to
enable the script on your instance.
7. Navigate to Change StartUp Script in your instance settings to verify
that the new script is added.
Terraform
1. Open your Terraform configuration for the existing Bare Metal instance.
2. Create or reference a vultr_startup_script resource and attach it to the
instance.

# Create a new startup script
resource "vultr_startup_script" "init" {
name = "init-nginx"
type = "boot"  # boot pxeboot
script = <<-EOT
    #!/bin/bash
    apt-get update -y
    apt-get install -y nginx
    systemctl enable --now nginx
    EOT
}
# Attach the startup script to the Bare Metal instance
resource "vultr_bare_metal_server" "bm1" {
    # ...existing fields (region, plan, os_id, label, etc.)
script_id = vultr_startup_script.init.id
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Stop Instance
Learn how to properly stop a Vultr Bare Metal instance to pause services
while maintaining your configuration and data.

How to Stop a Vultr Bare Metal
Instance
Introduction
Stopping an instance shuts it down and disables connectivity to the main
network interface. The operating system and all running processes are stopped,
but the instance normal billing cycle continues unless destroyed.
Follow this guide to stop a Vultr Bare Metal instance using the Vultr Console,
API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target instance to open its management page.
3. Click Stop Server on the top-right navigation menu to stop the instance.
4. Click Stop Server in the confirmation prompt to stop the instance.
Vultr API
1. Send a GET request to the List Bare Metal Instances endpoint and note
the target instance's ID in your output.
```bash
$ curl "https://api.vultr.com/v2/bare-metals" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Halt Bare Metal endpoint to stop the
instance.
```bash
$ curl "https://api.vultr.com/v2/bare-metals/{baremetal-id}/
halt" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all Bare Metal instances in your Vultr account and note the target
instance's ID.
```bash
$ vultr-cli bare-metal list
```
2. Stop the instance.
```bash
$ vultr-cli bare-metal stop <instance-id>

Tags
Learn how to create, apply, and manage tags to organize and filter your
Vultr Bare Metal instances.
```

How to Manage Tags on a Vultr
Bare Metal Instance
Introduction
Tagging enables the assignment of specific labels called tags on an instance for
identification in your Vultr account. Tags consist of multiple characters that help
identify, organize, and manage instances in your Vultr account.
Follow this guide to manage tags on a Vultr Bare Metal instance using the Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Bare Metal instance to open its management page.
3. Navigate to the Tags tab.
4. Enter a new tag in the Add Tag field and click Add to apply the new tag.
5. Find and click Delete within the Existing Tags section to remove a
specific tag on your instance.
Vultr API
1. Send a GET request to the List Bare Metal Instances endpoint and note
the target instance's ID.
```bash
$ curl "https://api.vultr.com/v2/bare-metals" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Bare Metal Instance endpoint to
add new tags to the instance.
```bash
$ curl "https://api.vultr.com/v2/bare-metals/{baremetal-id}"
\
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "tags" : ["tag1", "tag2"]
  }'
```
Vultr CLI
1. List all Bare Metal instances available in your Vultr account and note the
target instance's ID.
```bash
$ vultr-cli bare-metal list
```
2. Add new tags to the instance.
```bash
$ vultr-cli bare-metal tags <instance_id> --tags <tag1,tag2>
```
Terraform
1. Open your Terraform configuration for the existing Bare Metal instance.
2. Update the tags  value in the instance resource to include the desired tags.
```hcl
resource "vultr_bare_metal_server" "bm1" {
```
    # ...existing fields (region, plan, label, etc.)
tags = ["tag1", "tag2"]
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Networking
Manage and configure network settings for your Vultr instances, including
IP addressing, connectivity options, and network security features.

Metal server.

How to Manage IPv4 on a Vultr
Bare Metal Instance
Introduction
A public IPv4 network is available and attached to your Vultr Cloud Compute
instance after deployment unless disabled by default. You can attach multiple
IPv4 addresses on an instance to enable connections on the main public
networking interface.
Follow this guide to manage the IPv4 information on a Vultr Bare Metal instance
using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target instance to open its management page.
3. Navigate to the Settings tab.
4. Click IPv4 on the left navigation menu to view your instance's public IPv4
network information.
5. Click the default IPv4 reverse DNS value and replace it with your domain
values to enable reverse DNS on your instance.
Vultr API
1. Send a GET request to the List Bare Metal Instances endpoint and note
the target instance's ID in your output.
```bash
$ curl "https://api.vultr.com/v2/bare-metals" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Bare Metal IPv4 Addresses endpoint to view
the instance's IPv4 information.
```bash
$ curl "https://api.vultr.com/v2/bare-metals/{baremetal-id}/
ipv4" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all Bare Metal instances available in your Vultr account and note the
target instance's ID in your output.
```bash
$ vultr-cli bare-metal list
```
2. List your target instance's IPv4 address information.
```bash
$ vultr-cli bare-metal ipv4 <instance-id>

IPv6
Learn how to configure and manage IPv6 networking on your Vultr Bare
Metal server.
```

How to Manage IPv6 on a Vultr
Bare Metal Instance
Introduction
A public IPv6 network is available and attached to your Vultr Cloud Compute
instance after deployment unless disabled by default. You can manage the IPv6
address information on an instance and enable reverse DNS on the public
networking interface.
Follow this guide to manage the IPv6 information on a Vultr Bare Metal instance
using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target instance to open its management page.
3. Navigate to the Settings tab.
4. Click IPv6 on the left navigation menu to view your instance's public IPv6
network information.
5. Enter your IPv6 address in the IP field and a domain in the Reverse DNS
field to enable reverse DNS on your instance.
Vultr API
1. Send a GET request to the List Bare Metal Instances endpoint and note
the target instance's ID in your output.
```bash
$ curl "https://api.vultr.com/v2/bare-metals" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Bare Metal IPv6 Addresses endpoint to view
the instance's IPv6 information.
```bash
$ curl "https://api.vultr.com/v2/bare-metals/{baremetal-id}/
ipv6" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all Bare Metal instances in your Vultr account and note the target
instance's ID.
```bash
$ vultr-cli bare-metal list
```
2. List the instance's IPv6 network information.
```bash
$ vultr-cli bare-metal ipv6 <instance-id>
```
Terraform
Terraform can enable or disable IPv6 for a Bare Metal instance at creation time.
Managing existing IPv6 addresses or reverse DNS records after deployment is
not supported directly in Terraform and must be done through the Vultr Console,
API, or CLI.
1. Open your Terraform configuration for the existing Bare Metal instance.

2. Enable IPv6 on the instance and (optionally) set reverse DNS.
# Enable IPv6 on the instance
resource "vultr_bare_metal_server" "bm1" {
    # ...existing fields (region, plan, os_id, label, etc.)
enable_ipv6 = true
}
# Optional: set reverse DNS for the instance's primary IPv6
# (v6 address is known after the instance exists)
resource "vultr_reverse_ipv6" "bm1_ptr" {
ip = vultr_bare_metal_server.bm1.v6_main_ip
reverse = "host.example.com."
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Reserved IPs
A guide for assigning and managing persistent IP addresses on Vultr Bare
Metal servers

How to Attach Reserved IPs on a
Vultr Bare Metal Instance
Introduction
Reserved IP addresses enable you to reserve a specific public IP address you
can attach to instances. You can attach multiple reserved IPs on a single
instance to enable new network interfaces.
Follow this guide to attach reserved IPs on a Vultr Bare Metal instance using the
Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products, expand the Network group and click Reserved
IPs.
2. Click your target reserved IP to open its management page.
3. Click the Attach to Server drop-down and select your target Bare Metal
instance.
4. Click Attach to apply the reserved IP to your Bare Metal instance.
Vultr API
1. Send a GET request to the List Bare Metal Instances endpoint and note
the target instance's ID in your output.
```bash
$ curl "https://api.vultr.com/v2/bare-metals" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Reserved IPs endpoint and note the target
reserved IP's ID in your output.
```bash
$ curl "https://api.vultr.com/v2/reserved-ips" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Attach Reserved IP endpoint to attach a new
reserved IP to the instance.
```bash
$ curl "https://api.vultr.com/v2/reserved-ips/{reserved-ip}/
attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "instance_id" : "<instance-id>"
  }'
```
Vultr CLI
1. List all reserved IPs in your Vultr account and note the target reserved IP's
ID.
```bash
$ vultr-cli reserved-ip list
```
2. List all Bare Metal instances in your Vultr account and note the target
instance's ID.
```bash
$ vultr-cli bare-metal list
```
3. Attach the reserved IP to the Bare Metal instance.
```bash
$ vultr-cli reserved-ip attach <reserved-ip-id> --instance-id <baremetal-instance-id>
```
Terraform
1. Open your Terraform configuration for the existing Bare Metal instance.
2. Update the reserved_ip_id  value in the Bare Metal resource to the ID of the
target reserved IP.
```hcl
resource "vultr_bare_metal_server" "bm1" {
```
    # ...existing fields (region, plan, label, etc.)
reserved_ip_id = "your-reserved-ip-id"
}
Or create a new reserved IP in Terraform and attach it to the Bare Metal
instance:
TERRAFORM
resource "vultr_reserved_ip" "bm1_ip" {
region = "del"
ip_type = "v4"
label = "bm1-reserved-ip"
}
resource "vultr_bare_metal_server" "bm1" {
    # ...existing fields (region, plan, os_id, label, etc.)
reserved_ip_id = vultr_reserved_ip.bm1_ip.id
}
3. Apply the configuration and observe the following output:

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

VPC 2.0
A guide for connecting Vultr Bare Metal instances to VPC 2.0 networks for
enhanced private networking capabilities.

VPC 2.0 Product Documentation
VPC 2.0 Product Documentation
How to Attach VPC 2.0 Networks on
a Vultr Bare Metal Instance
Introduction
A Virtual Private Cloud (VPC) 2.0 network enables a secure and isolated private
networking interface on your instance for communication with other instances
on the same network. You can attach multiple VPC 2.0 networks to enable
communication between an instance and other nodes attached to the same
network.
Follow this guide to attach VPC 2.0 networks on a Vultr Bare Metal instance
using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target instance to open its management page.
3. Navigate to the Settings tab.
4. Click VPC 2.0 on the left navigation menu.
5. Click Enable VPC 2.0 to attach a new VPC 2.0 network to your instance.
6. Click Enable VPC 2.0 in the confirmation prompt to apply changes and
attach a new VPC 2.0 network to your instance.
7. Click the VPC 2.0 drop-down to select a specific network and click Attach
to apply changes.
Vultr API
1. Send a GET request to the List Bare Metal Instances endpoint and note
the target instance's ID in your output.

VPC 2.0 Product Documentation
```bash
$ curl "https://api.vultr.com/v2/bare-metals" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Instance VPC 2.0 Networks endpoint to
list all VPC 2.0 networks in your Vultr account and note the target VPC 2.0
network's ID.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
vpc2" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Attach VPC 2.0 to Instance endpoint to
attach the VPC 2.0 network to the Bare Metal instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
vpc2/attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "vpc_id": "<vpc-id>"
  }'
```
Vultr CLI
1. List all Bare Metal instances in your Vultr account and note the target
instance's ID.
```bash
VPC 2.0 Product Documentation
$ vultr-cli bare-metal list
```
2. List all VPC 2.0 networks in your Vultr account and note the target VPC 2.0
network's ID.
```bash
$ vultr-cli vpc2 list
```
3. Attach the VPC 2.0 network to the instance.
```bash
$ vultr-cli vpc2 nodes attach <vpc2-id> \
--nodes="<instance-id>"
```
Terraform
1. Open your Terraform configuration for the existing Bare Metal instance.
2. Create (or reference) a VPC 2.0 network and attach it to the Bare Metal
instance.
# Create a new VPC 2.0 network
resource "vultr_vpc2" "private_net" {
region = "del"
description = "Private network for Bare Metal workloads"
}
# Attach the VPC 2.0 network to the Bare Metal instance
resource "vultr_bare_metal_server" "bm1" {
    # ...existing fields (region, plan, os_id, label, etc.)
vpc2_ids = [vultr_vpc2.private_net.id]
}
3. Apply the configuration and observe the following output:

VPC 2.0 Product Documentation
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

VPC
A private network solution that allows you to securely connect multiple
Vultr instances within isolated network environments.

How to Attach VPC Networks on a
Vultr Bare Metal Instance
Introduction
A Virtual Private Cloud (VPC) network enables a secure and isolated private
networking interface on your instance for communication with other instances
in the same network. You can attach a single VPC network to enable
communication between a Bare Metal Instance and other nodes attached to the
same network.
Note
You must restart the instance for cloud-init to reconfigure the network
interfaces.
Follow this guide to attach a VPC network on a Vultr Bare Metal instance using
the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target instance to open its management page.
3. Navigate to the Settings tab.
4. Click IPv4 on the left navigation menu.
5. Click Enable VPC to attach a new VPC network to your instance.
6. Click Enable VPC in the confirmation prompt to apply changes.
7. Click Attach VPC in the confirmation prompt to apply changes to your
instance.

Vultr API
1. Send a GET  request to the List Bare Metal Instances endpoint and note
the target instance's ID in your output.
```bash
$ curl "https://api.vultr.com/v2/bare-metals" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List VPCs endpoint to list all VPCs in your Vultr
account and note the target VPC network's ID.
```bash
$ curl "https://api.vultr.com/v2/vpcs" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Attach VPC to Instance endpoint to attach
the VPC network to the Bare Metal instance.
```bash
$ curl "https://api.vultr.com/v2/instances/{instance-id}/
vpcs/attach" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
    "vpc_id": "<vpc-id>"
  }'
```

Vultr CLI
1. List all Bare Metal instances in your Vultr account and note the target
instance's ID.
```bash
$ vultr-cli bare-metal list
```
2. List all VPC networks in your Vultr account and note the target VPC
network's ID.
```bash
$ vultr-cli vpc list
```
3. Attach the VPC network to the instance.
```bash
$ vultr-cli instance vpc attach <instanceID> --vpc-id="<vpc-id>"
```
Terraform
1. Open your Terraform configuration for the existing Bare Metal instance.
2. Create (or reference) a VPC network and attach it to the Bare Metal
instance.
# Create a new VPC network
resource "vultr_vpc" "private_net" {
region = "del"
description = "Private network for Bare Metal workloads"

}
# Attach the VPC network to the Bare Metal instance
resource "vultr_bare_metal_server" "bm1" {
    # ...existing fields (region, plan, os_id, label, etc.)
vpc_ids = [vultr_vpc.private_net.id]
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Clusters
Manage cluster subscriptions on Vultr to organize compute resources with
shared networking and automated fabric provisioning for GPU and CPU
workloads.

Instance Templates
Create, manage, and configure reusable instance templates on Vultr that
define the plan, OS, SSH keys, and VPC for consistent cluster
deployments.

How to Create an Instance
Template
Create a reusable Vultr instance template that defines the compute plan,
OS, SSH keys, startup script, VPC, and storage for cluster deployments.

Introduction
An instance template is a reusable blueprint that defines the plan, OS, SSH
keys, startup script, VPC, and storage configuration for instances. Templates
ensure consistent deployments across a cluster and simplify scaling by
eliminating the need to specify configuration details for each new instance.
This guide explains how to create an instance template using the Vultr API.
The following table describes the available fields for creating an instance
template:
Field Type RequiredDescription
The compute plan identifier (e.g.,
string Yes
plan
).
vhp-4c-8gb-intel
label string No A descriptive label for the template.
integer No The operating system ID.
os_id
iso_id string No The ISO image ID.
snapshot_id string No The snapshot ID.
integer No The Marketplace application ID.
marketplace_app_id
marketplace_image_id integer No The Marketplace image ID.
string No The startup script ID to execute on boot.
script_id
Array of SSH key IDs to install on the
ssh_key_ids array No
instance.
Array of VPC network IDs to attach to the
vpc_ids array No
instance.
Array of Vultr File Storage (VFS)
array No
vfs_ids
subscription IDs to attach.
Base64-encoded Cloud-Init user data to
string No initialize and customize the instance at
user_data
boot.
Note

Creating an instance template requires only the plan  field. All other fields are
optional. To set an image source, choose only one of os_id , iso_id ,
snapshot_id , marketplace_app_id , or marketplace_image_id .
Send a POST  request to the Create Instance Template endpoint to create a
new template. Replace the placeholder values with your configuration.
```bash
$ curl "https://api.vultr.com/v2/instances/templates" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
-d '{
        "plan": "PLAN",
        "os_id": OS-ID,
        "label": "TEMPLATE-LABEL",
        "ssh_key_ids": [
            "SSH-KEY-ID"
        ],
        "vpc_ids": [
            "VPC-ID"
        ]
    }'
A successful request returns an HTTP 200 OK  response with the template details.
```
Note the template   for use when creating clusters or instances.
id

How to Delete an Instance
Template
Delete a Vultr instance template to permanently remove it. Templates
referenced by active clusters cannot be deleted until the association is
removed.

Introduction
Deleting an instance template permanently removes it from your account.
Instances that were previously created from the template continue to run and
are not affected.
Note
An instance template cannot be deleted if it is in use by any cluster. Remove
the template association from all clusters first.
This guide explains how to delete an instance template using the Vultr API.
1. Send a GET  request to the List Instance Templates endpoint to retrieve
all templates.
```bash
$ curl "https://api.vultr.com/v2/instances/templates" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Note the of the template you want to delete.
id
2. Send a DELETE  request to the Delete Instance Template endpoint to
delete the template. Replace {template-id}  with the template id.
```bash
$ curl "https://api.vultr.com/v2/instances/templates/
{template-id}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
A successful deletion returns an HTTP 204 No Content  response with no
response body.
```
3. Send a GET  request to the List Instance Templates endpoint to retrieve
all templates.

```bash
$ curl "https://api.vultr.com/v2/instances/templates" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
Verify that the deleted template no longer appears in the list.

How to List All Instance
Templates
Retrieve all reusable instance templates associated with your Vultr
account to identify available configurations for cluster or instance
creation.
```

Introduction
Listing instance templates retrieves all reusable templates associated with your
account, including their plan, OS, SSH keys, and other configuration details. This
is useful for identifying available templates before creating a cluster or
instance.
This guide explains how to list all instance templates using the Vultr API.
Send a GET  request to the List Instance Templates endpoint to retrieve all
templates.
```console
$ curl "https://api.vultr.com/v2/instances/templates" \
```
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
The response contains all instance templates with their configuration details.

How to Retrieve an
Instance Template
Retrieve the full configuration of a Vultr instance template including the
plan, OS, SSH keys, startup script, and VPC settings via the API.

Introduction
Retrieving an instance template returns its full configuration including the plan,
OS, SSH keys, startup script, VPC, and storage settings. This is useful for
reviewing a template's details before using it to create a cluster or instance.
This guide explains how to retrieve an instance template using the Vultr API.
1. Send a GET  request to the List Instance Templates endpoint to retrieve
all templates.
```bash
$ curl "https://api.vultr.com/v2/instances/templates" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Note the id  of the template you want to retrieve.
2. Send a GET  request to the Get Instance Template endpoint to retrieve
the template details. Replace {template-id}  with the template id.
```bash
$ curl "https://api.vultr.com/v2/instances/templates/
{template-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
The response contains the template configuration details.

How to Update an Instance
Template
Update a Vultr instance template to change its plan, OS, SSH keys, label,
or VPC associations. Existing instances created from the template are
unaffected.
```

Introduction
Updating an instance template changes its configuration such as the plan, OS,
SSH keys, label, or VPC associations. At least one field must be provided in the
request. Updated templates apply to new instances created from the template
— existing instances are not affected.
This guide explains how to update an instance template using the Vultr API.
1. Send a GET  request to the List Instance Templates endpoint to retrieve
all templates.
```bash
$ curl "https://api.vultr.com/v2/instances/templates" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Note the id  of the template you want to update.
2. Send a PUT  request to the Update Instance Template endpoint to
update the template. Replace {template-id}  with the template id. Include
only the fields you want to change.
```bash
$ curl "https://api.vultr.com/v2/instances/templates/
{template-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
-d '{
        "label": "NEW-TEMPLATE-LABEL",
        "os_id": OS-ID,
        "ssh_key_ids": [
            "SSH-KEY-ID"
        ],
        "vpc_ids": [
            "VPC-ID"

]
}'
A successful update returns an HTTP 202 Accepted response.
```
3. Send a GET request to the Get Instance Template endpoint to retrieve
the updated template details.
```bash
$ curl "https://api.vultr.com/v2/instances/templates/
{template-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
Verify that the template details reflect the new values.

How to Add Instances to a
Cluster
Add existing instances to a Vultr cluster in bulk or individually. GPU
clusters automatically configure fabric networking when instances join.
```

Introduction
Adding instances to a cluster associates existing instances with the cluster and
configures the fabric networking automatically. For GPU clusters, the high-performance interconnect (RoCE or InfiniBand) is provisioned when instances
join — no manual VLAN or PKey setup is needed. You can add a single instance
or multiple instances at once.
Note
An instance can belong to only one cluster at a time. All instances in a cluster
must be in the same region and match the cluster's plan type.
This guide explains how to add instances to a cluster using the Vultr API.
1. Send a GET  request to the List Clusters endpoint to retrieve all clusters.
```bash
$ curl "https://api.vultr.com/v2/clusters" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Note the   of the cluster to which you want to add instances.
id
2. Send a GET  request to the List Instances endpoint to retrieve all
instances.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Note the  id  of the instance(s) you want to add to the cluster.

Add Multiple Instances
1. Send a POST  request to the Mass Update Cluster Instances endpoint to
add multiple instances to the cluster. Replace {cluster-id}  with the cluster
id and provide the instance IDs in the instances  array. Set action  to add .
```bash
$ curl "https://api.vultr.com/v2/clusters/{cluster-id}" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
-d '{
        "action": "add",
        "instances": [
            "INSTANCE-ID-1",
            "INSTANCE-ID-2"
        ]
    }'
A successful request returns an HTTP 202 Accepted  response.
```
2. Send a GET  request to the Get Cluster endpoint to retrieve the cluster
details. Replace {cluster-id}  with the cluster id.
```bash
$ curl "https://api.vultr.com/v2/clusters/{cluster-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
Verify that the added instances appear in the cluster's instance list.

Add a Single Instance
```
1. Send a POST  request to the Add Single Instance endpoint to add a single
instance to the cluster. Replace {cluster-id}  with the cluster id and
 with the instance id.
{instance-id}
```bash
$ curl "https://api.vultr.com/v2/clusters/{cluster-id}/add/
{instance-id}" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}"
A successful request returns an HTTP 202 Accepted  response.
```
2. Send a GET  request to the Get Cluster endpoint to retrieve the cluster
details.
```bash
$ curl "https://api.vultr.com/v2/clusters/{cluster-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
Verify that the instance appears in the cluster's instance list.

How to Check Cluster
Availability by Region
Check available cluster types and plans for a specific Vultr region before
creating a cluster. Filter results by VPS, bare-metal, or GPU fabric type.
```

Introduction
Checking cluster availability returns the available cluster types and plans for a
specific region. This is useful for determining which regions support vps , bare-
, or gpu-fabric  clusters before creating one.
metal
This guide explains how to check cluster availability by region using the Vultr
API.
Send a GET  request to the Get Cluster Availability endpoint to check
available cluster types. Replace REGION  with the region identifier (e.g., ewr , ord ,
). Set type  to filter by cluster type. Available types are vps , bare-metal , and
lax
gpu-fabric .
```console
$ curl "https://api.vultr.com/v2/clusters/availability" \
```
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
-d '{
        "region": "REGION",
        "type": "vps"
    }'
The response contains the available cluster types and plans for the specified
region.

How to Create a Cluster
Using an Instance
Template
Create a Vultr cluster using a reusable instance template that defines the
plan, OS, SSH keys, and startup script for consistent deployments.

Introduction
Instance templates define a reusable blueprint for instances including the plan,
OS, SSH keys, startup script, VPC, and storage configuration. Using a template
when creating a cluster ensures consistent deployments and simplifies scaling.
This guide explains how to create a cluster using an existing instance template
via the Vultr API. To create a cluster by specifying a plan directly, see How to
Create a Cluster.
1. Send a GET  request to the List Instance Templates endpoint to retrieve
all available templates. If you do not have a template, create one by
following How to Create an Instance Template.
```bash
$ curl "https://api.vultr.com/v2/instances/templates" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Note the of the template you want to use.
id
2. Send a POST  request to the Create Cluster endpoint to create a new
cluster using the template. Replace REGION  with the region identifier,
with the instance template id, and CLUSTER-LABEL with a
TEMPLATE-ID
descriptive name. Set type  to vps , bare-metal , or gpu-fabric  depending on
your cluster configuration. The desired_pool_count  must be equal to or
greater than min_pool_count .
```bash
$ curl "https://api.vultr.com/v2/clusters" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
-d '{
        "region": "REGION",
        "instance_template": "TEMPLATE-ID",
        "label": "CLUSTER-LABEL",

"type": "vps",
"min_pool_count": 2,
"desired_pool_count": 2,
"hostname": "HOSTNAME",
"notify_activate": true
}'
A successful request returns an HTTP 200 OK response with the cluster
details. Note the cluster id for future operations.
```
3. Send a GET request to the Get Cluster endpoint to retrieve the cluster
details. Replace {cluster-id} with the id from the previous step.
```bash
$ curl "https://api.vultr.com/v2/clusters/{cluster-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
Verify that the cluster status progresses from Pending to Active once all
instances are provisioned.

How to Create a Cluster
Create a Vultr cluster subscription by specifying a region, plan, and pool
size using the Vultr API for VPS, bare-metal, or GPU fabric workloads.
```

Introduction
A cluster is a logical container that organizes compute resources under a single
definition with shared networking. Creating a cluster provisions the container
and optionally deploys instances based on the specified plan and pool count.
Clusters support three types:
• vps: Cloud compute instances available in multiple plan categories
including Shared CPU, Dedicated CPU, CPU Optimized, and General
Purpose, suitable for a wide range of workloads from web applications to
compute-intensive services.
• bare-metal: Single-tenant physical servers dedicated to one customer,
offering maximum performance and direct hardware access without a
hypervisor layer.
• gpu-fabric: GPU servers interconnected with automated high-performance fabric networking (RoCE or InfiniBand), designed for AI/ML
training, distributed inference, and HPC workloads that require low-latency,
high-bandwidth communication between nodes.
This guide explains how to create a cluster using a plan directly using the Vultr
API. To create a cluster using a reusable instance template, see How to Create a
Cluster Using an Instance Template.
1. Send a GET request to the Get Cluster Availability endpoint to check
available cluster types in your target region. Replace REGION with the region
identifier (e.g., ewr , ord ).
```bash
$ curl "https://api.vultr.com/v2/clusters/availability" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
-d '{
"region": "REGION",
"type": "vps"
}'

The response contains the available cluster types and plans for the
specified region.
```
2. Send a POST  request to the Create Cluster endpoint to create a new
cluster. Replace REGION  with the region identifier, PLAN  with the compute
plan, and CLUSTER-LABEL  with a descriptive name. Set type  to vps , bare-metal , or gpu-fabric . The desired_pool_count  must be equal to or greater than
min_pool_count .
```bash
$ curl "https://api.vultr.com/v2/clusters" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
-d '{
        "region": "REGION",
        "plan": "PLAN",
        "label": "CLUSTER-LABEL",
        "type": "vps",
        "min_pool_count": 2,
        "desired_pool_count": 2,
        "os_id": 2284,
        "hostname": "HOSTNAME",
        "notify_activate": true
    }'
A successful request returns an HTTP 200 OK  response with the cluster
details. Note the cluster id  for future operations.
```
3. Send a GET  request to the Get Cluster endpoint to retrieve the cluster
details. Replace {cluster-id}  with the id from the previous step.
```bash
$ curl "https://api.vultr.com/v2/clusters/{cluster-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
Verify that the cluster status progresses from Pending  to Active  once all
instances are provisioned.

How to Delete a Cluster
Delete a Vultr cluster subscription to remove the cluster container and
fabric associations while keeping the underlying instances on your
account.
```

Introduction
Deleting a cluster removes the cluster subscription and its fabric associations.
The underlying instances are not destroyed, they remain on your account as
standalone servers.
Note
A cluster with attached instances cannot be deleted. Remove all instances
from the cluster first.
This guide explains how to delete a cluster using the Vultr API.
1. Send a GET  request to the Get Cluster endpoint to retrieve the cluster
details and verify that no instances are attached. Replace {cluster-id}  with
the id of the cluster you want to delete.
```bash
$ curl "https://api.vultr.com/v2/clusters/{cluster-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
Verify that the cluster has no attached instances. If instances are attached,
remove them first using How to Remove Instances from a Cluster.
```
2. Send a DELETE  request to the Delete Cluster endpoint to delete the
cluster. Replace {cluster-id}  with the cluster id.
```bash
$ curl "https://api.vultr.com/v2/clusters/{cluster-id}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
A successful deletion returns an HTTP 204 No Content  response with no
response body.
```
3. Send a GET  request to the List Clusters endpoint to retrieve all clusters.
```bash
$ curl "https://api.vultr.com/v2/clusters" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
Verify that the deleted cluster no longer appears in the list.

How to List All Clusters
Retrieve all cluster subscriptions associated with your Vultr account using
the API with cursor-based pagination support for large result sets.
```

Introduction
Listing clusters retrieves all cluster subscriptions associated with your account,
including their status, region, attached instance count, and configuration
details. The endpoint supports cursor-based pagination for accounts with many
clusters.
This guide explains how to list all clusters using the Vultr API.
Send a GET  request to the List Clusters endpoint to retrieve all clusters.
```console
$ curl "https://api.vultr.com/v2/clusters" \
```
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
The response contains all clusters with their details. Use the cursor  and per_page
query parameters to paginate through large result sets.

How to Remove Instances
from a Cluster
Remove instances from a Vultr cluster in bulk or individually. Detached
instances remain on your account as standalone servers with fabric
removed.

Introduction
Removing instances from a cluster detaches them from the cluster and removes
their fabric networking associations. The instances are not destroyed, they
remain on your account as standalone servers.
This guide explains how to remove instances from a cluster using the Vultr API.
1. Send a GET  request to the List Clusters endpoint to retrieve all clusters.
```bash
$ curl "https://api.vultr.com/v2/clusters" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Note the  id  of the cluster from which you want to remove instances.
2. Send a GET  request to the Get Cluster endpoint to retrieve the cluster
details. Replace {cluster-id}  with the cluster id.
```bash
$ curl "https://api.vultr.com/v2/clusters/{cluster-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Note the   of the instance(s) you want to remove from the cluster.
id
Remove Multiple Instances
1. Send a POST  request to the Mass Update Cluster Instances endpoint to
remove multiple instances from the cluster. Replace {cluster-id}  with the
cluster id and provide the instance IDs in the instances  array. Set action  to
.
remove

```bash
$ curl "https://api.vultr.com/v2/clusters/{cluster-id}" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
-d '{
        "action": "remove",
        "instances": [
            "INSTANCE-ID-1",
            "INSTANCE-ID-2"
        ]
    }'
A successful request returns an HTTP 202 Accepted  response.
```
2. Send a GET  request to the Get Cluster endpoint to retrieve the cluster
details.
```bash
$ curl "https://api.vultr.com/v2/clusters/{cluster-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
Verify that the removed instances no longer appear in the cluster's
instance list.
Remove a Single Instance
```
1. Send a POST  request to the Remove Single Instance endpoint to remove
a single instance from the cluster. Replace {cluster-id}  with the cluster id
and {instance-id}  with the instance id.
```bash
$ curl "https://api.vultr.com/v2/clusters/{cluster-id}/
remove/{instance-id}" \

-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}"
A successful request returns an HTTP 202 Accepted  response.
```
2. Send a GET  request to the Get Cluster endpoint to retrieve the cluster
details.
```bash
$ curl "https://api.vultr.com/v2/clusters/{cluster-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
Verify that the instance no longer appears in the cluster's instance list.

How to Retrieve a Cluster
Retrieve full details of a Vultr cluster including its label, region, type, pool
configuration, attached instances, and current status via the API.
```

Introduction
Retrieving a cluster returns its full details including the label, region, type, pool
configuration, attached instances, instance template, and current status. This is
useful for checking cluster health, reviewing configuration, and obtaining
instance IDs for management operations.
This guide explains how to retrieve a cluster using the Vultr API.
1. Send a GET  request to the List Clusters endpoint to retrieve all clusters.
```bash
$ curl "https://api.vultr.com/v2/clusters" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Note the id  of the cluster you want to retrieve.
2. Send a GET  request to the Get Cluster endpoint to retrieve the cluster
details. Replace {cluster-id}  with the id of the cluster.
```bash
$ curl "https://api.vultr.com/v2/clusters/{cluster-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
The response contains the cluster details including attached instances and
current status.

How to Retrieve Cluster
Metrics
Retrieve GPU and fabric performance metrics for all instances in a Vultr
cluster with configurable time periods of 1, 7, or 30 days via the API.
```

Introduction
Retrieving cluster metrics returns GPU and fabric performance data for all
instances in a cluster. This is useful for monitoring cluster health, identifying
performance bottlenecks, and tracking resource utilization.
This guide explains how to retrieve cluster metrics using the Vultr API.
1. Send a GET  request to the List Clusters endpoint to retrieve all clusters.
```bash
$ curl "https://api.vultr.com/v2/clusters" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Note the  id  of the cluster for which you want to retrieve metrics.
2. Send a GET  request to the Get Cluster Metrics endpoint to retrieve
metrics for the cluster. Replace {cluster-id}  with the cluster id. Optionally
add the period  query parameter to specify the time range: -1days  (default),
-7days , or -30days .
```bash
$ curl "https://api.vultr.com/v2/clusters/{cluster-id}/
metrics?period=-7days" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
The response contains GPU and fabric metrics for all instances in the
cluster.

How to Update a Cluster
Update a Vultr cluster's label, hostname, and pool count to scale the
cluster up or down by adjusting the desired and minimum pool size via
the API.
```

Introduction
Updating a cluster allows you to change its label, hostname, and pool size.
Adjusting min_pool_count  and desired_pool_count  scales the cluster up or down by
provisioning or removing instances automatically.
Note
The desired_pool_count  must be equal to or greater than min_pool_count .
This guide explains how to update a cluster using the Vultr API.
1. Send a GET  request to the List Clusters endpoint to retrieve all clusters.
```bash
$ curl "https://api.vultr.com/v2/clusters" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Note the id  of the cluster you want to update.
2. Send a PUT  request to the Update Cluster endpoint to update the cluster
properties. Replace {cluster-id}  with the cluster id. Include only the fields
you want to change.
```bash
$ curl "https://api.vultr.com/v2/clusters/{cluster-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
-d '{
        "label": "NEW-LABEL",
        "hostname": "NEW-HOSTNAME",
        "min_pool_count": MIN-POOL-COUNT,
        "desired_pool_count": DESIRED-POOL-COUNT
    }'
A successful update returns an HTTP 202 Accepted response.
```
3. Send a GET  request to the Get Cluster endpoint to retrieve the updated
cluster details.
```bash
$ curl "https://api.vultr.com/v2/clusters/{cluster-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
Verify that the cluster details reflect the new values.
```