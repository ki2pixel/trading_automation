Orchestration
Manage and automate your infrastructure resources with Vultr's
comprehensive orchestration tools for system backups, recovery, and
deployment.

Backups
Automated backup solutions for Vultr instances that protect your data
and enable quick recovery when needed.

Provisioning
The process of setting up and configuring a new server or service to
make it ready for use.

How to Manage Automatic Backups
for Vultr Cloud Compute
Introduction
Automatic Backups for Vultr instances are scheduled point-in-time data
recovery solutions that allow you to backup your Cloud Compute instances' data
with minimal intervention. These backups are suitable for mission-critical
applications because they aid in data protection, disaster recovery, compliance,
and auditing. Vultr supports daily, every other day, weekly, and monthly backup
schedules.
Follow this guide to manage Automatic Backups for Vultr instances using the
Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Compute.
2. Select your target Cloud Compute instance from the list.
3. Navigate to Backups and click Enable Backups.
4. Click Enable Backups to confirm.
5. Navigate to Backup Schedule. Then, select daily, weekly, or every other
day backup schedule. Set the day of the week and time and click Update.
6. From this point forward, any new backup appears under the backup history.
Click Convert to convert the backup to a manual snapshot or Restore to
restore the backup to the cloud compute instance.
7. Navigate to Products, select Orchestration, then click Backups. Click
the camera icon to convert the backup to a snapshot.

Vultr API
1. Send a GET  request to the List Instances endpoint to get the Cloud
Compute instance ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Instance endpoint to turn on
automatic backups.
```bash
$ curl "https://api.vultr.com/v2/instances/instance_id" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "backups" : "enabled",
        "backups_schedule" : {
            "type" : "daily",
            "hour" : "0"
        }
    }'
```
3. Send a PATCH  request to the Update Instance endpoint to turn off
automatic backups.
```bash
$ curl "https://api.vultr.com/v2/instances/instance_id" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{

        "backups" : "disabled"
    }'
```
Visit the Update Instance endpoint to view additional attributes to add to
your request.
4. Send a GET  request to the List Backups endpoint and note the backup ID.
```bash
$ curl "https://api.vultr.com/v2/backups" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
5. Send a GET  request to the Get Backup endpoint and specify the backup ID
to view the backup details.
```bash
$ curl "https://api.vultr.com/v2/backups/backup_id" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all cloud compute instances and note the instance ID.
```bash
$ vultr-cli instance list
```
2. Update the backup schedule by specifying the instance_id .
```bash
$ vultr-cli instance backup create instance_id --type weekly
--dow 0 --hour 0
```
3. List all backups by specifying a cloud compute instance ID.
```bash
$ vultr-cli instance backup get instace_id
```
4. List all Cloud Compute instance backups.
```bash
$ vultr-cli backups list
```
5. Get details of a specific backup by specifying the backup ID.
```bash
$ vultr-cli backups get backup_id
```
Run vultr-cli instance backup create --help  to view all options.
Terraform
1. Open your Terraform configuration for the existing instance.
2. Enable automatic backups and optionally set a backup schedule.
```hcl
resource "vultr_instance" "server" {
```
    # ...existing fields (region, plan, os_id or snapshot_id,
label)
backups = true
    # Optional: schedule (availability depends on plan)
backups_schedule {
type = "daily"    # daily weekly alternating
hour = 0          # 0-23
        # dow = 0         # for weekly: 0=Sunday ...

6=Saturday
}
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Management
Centralized tools and settings for administering your Vultr account,
resources, and infrastructure.

Delete Backups
Learn how to permanently remove backup snapshots from your Vultr
account to free up storage space.

How to Delete Backups for Vultr
Instances
Introduction
Deleting backups for Vultr instances completely removes the files from your
account. You should perform this operation after restoring the required backup
files. You can also consider converting a backup to a snapshot before deleting
the backup. After deleting a backup, you can't undo the operation and you
should take great care before making the decision.
Follow this guide to delete Backups for Vultr instances using the Vultr Console.
Vultr Console
1. Navigate to Products, select Orchestration, then click Backups.
2. Click the delete icon to remove the backup.
3. Click Remove Backup to confirm.

FAQ
Frequently asked questions and answers about Vultrs products, services,
and platform features.

Frequently Asked Questions (FAQs)
About Vultr Backups
Introduction
These are the frequently asked questions for Automatic Backups for Vultr
Instances.
Do automatic backups include the attached
Block Storage data?
No. Automatic Backups only include the Cloud Compute instance's active file
system. Backups do not include any attached Block Storage volumes.
Is it possible to convert an Automatic
Backup image to a Snapshot?
Yes, Vultr provides an option to convert your Automatic Backup images to
Snapshots. This option is helpful if you want to restore a backup to a different
instance. You can also use this option to preserve that backup image so that
Vultr does not automatically delete it during a backup cycle.
Do Automatic Backups attract additional
charges?
Yes. If you enable Automatic Backups, the Cloud Compute instance attracts a
20% monthly/hourly charge on top of the regular charges.

Can I customize the backup schedule for
Vultr instances?
Yes, Vultr allows you to choose from daily, every other day, weekly, or monthly
backups. You can also set the appropriate time for your backups to run,
especially when your instance is less busy.
What happens when I restore a backup for
Vultr instances?
When you restore a Cloud Compute instance backup, any data on your Cloud
Compute instance is overwritten. Therefore, take great care when executing this
operation and backup any important files.

ISOs
Manage custom ISO images for installing operating systems and
applications on your Vultr instances.

Provisioning
The process of setting up and configuring a new server or service to
make it ready for use.

How to Manage ISO Images for
Vultr Instances
Introduction
ISO Images for Vultr instances are compressed copies of an operating system's
installer. These images allow you to install custom operating systems on Cloud
Compute instances. The ISO files may contain pre-configured settings and
software according to specific needs to streamline server setup. The Vultr
library also allows you to choose and install various public standard ISOs
including Finnix, GParted, Hiren's BootCD PE, and SystemRescue.
Follow this guide to manage ISO Images for Vultr instances using the Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Orchestration. Then, choose ISOs.
2. Click Add ISO.
3. Enter the remote URL of your ISO file and click Upload.
Vultr API
1. Send a POST request to the Create ISO endpoint and specify the remote
ISO file URL.
```bash
$ curl "https://api.vultr.com/v2/iso" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \

--data '{
        "url" : "https://example.com/remote_iso_file_url.iso"
    }'
```
Visit the Create ISO endpoint to view additional attributes to add to your
request.
2. Send a GET  request to the List ISOs endpoint to list all ISOs.
```bash
$ curl "https://api.vultr.com/v2/iso" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. Create an ISO from an URL by defining the URL where you want to
download the ISO file.
```bash
$ vultr-cli iso create --url https://releases.ubuntu.com/
24.04/ubuntu-24.04-live-server-amd64.iso
```
2. List all ISOs.
```bash
$ vultr-cli iso list
```
3. List specific details about an ISO by specifying the ISO ID.
```bash
$ vultr-cli iso get iso_id
```
Run vultr-cli iso create --help to view all options.

Terraform
1. Define a custom ISO by URL and apply.
```hcl
resource "vultr_iso" "custom_iso" {
url = "https://example.com/remote_iso_file_url.iso"
}
```
2. Attach the ISO when creating an instance. Remember to set os_id = 159  for
custom ISO boot.
```hcl
resource "vultr_instance" "server" {
region = "ewr"
plan = "vc2-2c-4gb"
label = "iso-boot"
os_id = 159          # required for custom ISO
iso_id = vultr_iso.custom_iso.id
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Management
Tools and services for managing your Vultr infrastructure, including
account settings, billing, and resource administration.

Delete ISOs
Learn how to permanently remove custom ISO files from your Vultr
account when theyre no longer needed.

How to Delete ISO Images for Vultr
Instances
Introduction
Deleting ISO Images for Vultr instances allows you to completely remove the file
from your account and make room for more images. Vultr only permits two ISO
files at a time. Removing an ISO file doesn't affect any Cloud Compute instances
you've provisioned using the image.
Follow this guide to delete ISO images for Vultr instances using the Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Orchestration. Then, choose ISOs.
2. Select the target ISO image from the list and click the delete icon.
3. Click Delete ISO to confirm.
Vultr API
1. Send a GET request to the List ISOs endpoint to list all ISOs.
```bash
$ curl "https://api.vultr.com/v2/iso" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE request to the Delete ISO endpoint and specify an ISO ID to
delete the ISO file.

```bash
$ curl "https://api.vultr.com/v2/iso/iso_id" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Visit the Delete ISO endpoint to view additional attributes to add to your
request.
Vultr CLI
1. List all cloud compute instances and note the instance ID.
```bash
$ vultr-cli instance list
```
2. List all ISOs and note the ISO ID.
```bash
$ vultr-cli iso list
```
3. Delete an ISO by specifying an ISO ID.
```bash
$ vultr-cli iso delete iso_id
```
Run vultr-cli iso delete --help to view all options.
Terraform
1. Open your Terraform configuration where the ISO resource was defined.
2. Remove the vultr_iso  resource block, or destroy it by target.

```hcl
resource "vultr_iso" "custom_iso" {
url = "https://example.com/remote_iso_file_url.iso"
}
```
# To delete, either remove this block from configuration
# or run: terraform destroy -target vultr_iso.custom_iso
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 0 changed, 1 destroyed.

FAQ
Frequently asked questions and answers about Vultrs products, services,
and platform features.

Frequently Asked Questions (FAQs)
About Vultr ISOs
Introduction
These are the frequently asked questions for ISO images for Vultr Instances.
Is there a limit to the number of ISO images
I can upload to my Vultr account?
Yes. Vultr currently allows up to 2 ISO images per account. If you want to upload
more ISO images, consider removing old ISOs to free up space.
Can I upload an ISO file from a local
computer to Vultr?
Yes. However, before uploading an ISO file from your local file system, create a
publicly accessible URL. For instance, you can upload the file to an FTP server
and generate a URL.
Which other ISO files does Vultr support
apart from custom ISO files?
Vultr provides an ISO library that includes the Finnix, Gparted, Hiren's BootCD
PE, and SystemRescue images that you can choose when provisioning Cloud
Compute instances.

If I delete an ISO, will it affect any Cloud
Compute instances that I created with the
ISO?
You can not delete a custom ISO if it's attached to a Cloud Compute instance.
First, delete the instance, and then delete the ISO file.

Snapshots
Snapshots allow you to create point-in-time backups of your instances for
quick recovery, cloning, or deployment across regions.

Provisioning
A process that prepares and configures a new server or service to make it
ready for use.

How to Manage Snapshots for Vultr
Instances
Introduction
Snapshots for Vultr instances are point-in-time images of your entire Cloud
Compute instances hard drives. You can use snapshots to create backups or to
replicate Cloud Compute instances. Unlike Automatic Backups for Vultr
instances, you must take snapshots manually.
Follow this guide to manage Snapshots for Vultr instances using the Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Compute.
2. Select your target Cloud Compute instance from the list.
3. Navigate to Snapshots, enter a label and click Take Snapshot.
Vultr API
1. Send a GET request to the List Instances endpoint to get the Cloud
Compute instance ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Create Snapshot endpoint specifying a cloud
compute instance ID to create a snapshot.
```bash
$ curl "https://api.vultr.com/v2/snapshots" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
            "instance_id" : "instance_id",
            "description" : "Weekly-Snapshot-14-08-2024"
        }'
```
Visit the Create Snapshot endpoint to view additional attributes to add to
your request.
3. Send a GET  request to the List Snapshots endpoint to view all snapshots.
```bash
$ curl "https://api.vultr.com/v2/snapshots" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all cloud compute instances and note the instance ID.
```bash
$ vultr-cli instance list
```
2. Create a snapshot by specifying the Cloud Compute instance ID and the
snapshot description.
```bash
$ vultr-cli snapshot create --id instance_id --description
"Weekly Snapshot 14-08-2024"
```
3. List all snapshots.
```bash
$ vultr-cli snapshot list
```
Run vultr-cli snapshot create --help to view all options.
Terraform
1. Create a snapshot from an existing instance.
```hcl
resource "vultr_snapshot" "weekly" {
instance_id = var.instance_id
description = "Weekly-Snapshot-14-08-2024"
}
```
2. Optionally, boot a new instance from a snapshot by setting snapshot_id .
```hcl
resource "vultr_instance" "from_snapshot" {
region = "ewr"
plan = "vc2-2c-4gb"
label = "restored"
snapshot_id = vultr_snapshot.weekly.id
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Management
Administrative tools and settings for managing your Vultr account,
resources, and infrastructure.

Delete
Permanently removes the selected resource from your Vultr account.

How to Delete Snapshots
Introduction
Deleting snapshots completely removes the resource from your account. You
should only do this operation after restoring a snapshot to a Vultr Cloud
Compute instance or after provisioning a Vultr Cloud Compute instance using
the snapshot image. After deleting a snapshot, you can't undo the operation, so
you should take great care.
Follow this guide to delete snapshots using the Vultr Console, API, CLI, or
Terraform.
Vultr Console
1. Navigate to Products and select Orchestration.
2. Click Snapshots. Select the target snapshot from the list and click the
delete icon to remove the snapshot.
3. Click Remove Snapshot to confirm.
Vultr API
1. Send a GET request to the List Snapshots endpoint to list all snapshots.
```bash
$ curl "https://api.vultr.com/v2/snapshots" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE request to the Delete Snapshot endpoint specifying a
snapshot ID to delete a snapshot.

```bash
$ curl "https://api.vultr.com/v2/snapshots/snapshot_id" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Visit the Delete Snapshot endpoint to view additional attributes to add to
your request.
Vultr CLI
1. List all snapshots and note the target snapshot's ID.
```bash
$ vultr-cli snapshot list
```
2. Delete a snapshot by specifying a snapshot ID.
```bash
$ vultr-cli snapshot delete snapshot_id
```
Run vultr-cli snapshot delete --help to view all options.
Terraform
1. Open your Terraform configuration where the snapshot resource was
created.
2. Remove the vultr_snapshot  resource block, or destroy it by target.
```hcl
resource "vultr_snapshot" "weekly" {
instance_id = var.instance_id

description = "Weekly-Snapshot-14-08-2024"
}
```
# To delete, either remove this block from configuration
# or run: terraform destroy -target vultr_snapshot.weekly
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 0 changed, 1 destroyed.

Restore
Recover your server to a previous state using a backup or snapshot.

How to Restore Snapshots
Introduction
Restoring a snapshot involves recovering the exact state of a system at the
time the snapshot was created. Snapshots capture the complete configuration,
including the operating system, applications, and data, making it easy to revert
to a specific point in time. This process is essential for system recovery, testing,
or duplicating environments, ensuring consistency and minimizing downtime.
Follow this guide to restore snapshots using the Vultr Console, API, CLI, or
Terraform.
Note
When restoring a server backup that uses a static IP, you must reset the
network to DHCP to obtain a functional IP address. If network configuration
needs to be reset after restoring a snapshot, refer to Return a Vultr Server to
the Default DHCP Configuration. Restoring a snapshot on existing Vultr Cloud
Compute servers or provisioning new servers using snapshots may take an
additional 10-15 minutes compared to standard operations.
Vultr Console
1. Navigate to Products and click Compute.
2. Click your target Vultr Cloud Compute instance to open its management
page.
3. Navigate to the Snapshots tab.
4. Choose any snapshot you want to restore.
5. Click "Restore Snapshot" to start the restoration procedure on that target
Vultr Cloud Compute instance.

6. Optional: To provision a new Vultr Cloud Compute instance with snapshot,
select Snapshot in the Choose Image section. How to Provision Vultr
Cloud Compute Instance.
Vultr API
1. Send a GET  request to the List Snapshots endpoint to list all snapshots.
```bash
$ curl "https://api.vultr.com/v2/snapshots" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Instances endpoint to list all deployed
Vultr Cloud Compute instances. Note the target instance's ID.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Restore Instances endpoint to start the
restore procedure of the target Vultr Cloud Compute instance.
```bash
$ curl "https://api.vultr.com/v2/instances/<instance-id>/
restore" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "snapshot_id": "<snapshot-id>"
    }'
```
4. Optional: Send a POST  request to the Create Instances endpoint to
provision a new Vultr Cloud Compute instance using snapshot.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "region" : "<region>",
        "plan" : "<plan>",
        "snapshot_id" : "<snapshot-id>",
        "label" : "<label>",
        "hostname": "<hostname>"
    }'
```
Vultr CLI
1. List all snapshots and note the target snapshot's ID.
```bash
$ vultr-cli snapshot list
```
2. List all Vultr Cloud Compute instances and note target instance's ID.
```bash
$ vultr-cli instance list
```
3. Restore a snapshot on the target Vultr Cloud Compute instance.
```bash
$ vultr-cli instance restore <instance-id> --snapshot
<snapshot-id>
```
4. Optional: Provision a new Vultr Cloud Compute instance using snapshot.
```bash
$  vultr-cli instance create --region="<region>" --
plan="<plan>" --snapshot="<snapshot-id>" --label="<label>"
```
Terraform
1. Boot a new instance from a snapshot by setting snapshot_id , or update an
existing resource to change its boot image.
```hcl
resource "vultr_instance" "restored" {
region = "ewr"
plan = "vc2-2c-4gb"
label = "restored-from-snap"
snapshot_id = var.snapshot_id
}
```
2. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

FAQ
Frequently asked questions and answers about Vultrs products, services,
and platform features.

Frequently Asked Questions (FAQs)
About Vultr Snapshots
Introduction
These are the frequently asked questions for Snapshots for Vultr Instances.
How does Vultr bill me for Snapshots?
Vultr charges $0.05/GB per month for the compressed size of your Snapshots.
What is the difference between Vultr
Snapshot and Automatic Backups?
A Snapshot and an Automatic Backup are point-in-time images of Cloud
Compute Instances. However, Automatic Backups run automatically but you
must take a snapshot manually.
Does Vultr support Snapshots for Bare Metal
instances?
No, snapshots are not available for Bare Metal instances. If you want to backup
the instances, consider installing third-party backup applications.

Can I use a Snapshot in a different Vultr
location?
Vultr Snapshots span across all regions. For instance, if you provision a snapshot
in London and take a snapshot, you can provision a new instance in New York
using the same snapshot image.

Startup Scripts
Automate server configuration during deployment with customizable
startup scripts that execute when your Vultr instance first boots.

Provisioning
The process of setting up and configuring a new server or service to
make it ready for use.

How to Manage Startup Scripts for
Vultr Instances
Introduction
Startup Scripts for Vultr instances are files that run custom commands when
your instances boot. The scripts automate repetitive tasks like installing
software, configuring settings, querying third-party services, and more. These
scripts are suitable when provisioning multiple Cloud Compute instances
because they save time.
Follow this guide to manage Startup Scripts for Vultr Instances using the Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Orchestration and select Scripts.
2. Click Add Startup Script.
3. Enter a name, select the type, define some commands, and click Add
Script.
Vultr API
1. Send a POST request to the Create Startup Script endpoint and encode
the Startup script to Base64 format.
```bash
$ curl "https://api.vultr.com/v2/startup-scripts" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \

--data '{
"name" : "Sample-Script",
"type" : "pxe",
"script" : "QmFzZTY0IEV4YW1wbGUgRGF0YQ=="
}'
```
Visit the Create Startup Script endpoint to view additional attributes to
add to your request.
2. Send a GET request to the List Startup Scripts endpoint to view all
scripts.
```bash
$ curl "https://api.vultr.com/v2/startup-scripts" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. Create a new scripts.yaml file.
```bash
$ nano scripts.yaml
```
2. Enter your Startup scripts into the file.
```yaml
mkdir ~/my-apps
chmod 700 ~/my-apps
```
3. Save the file.
4. Convert the file contents to Base64 and note the output. For instance,
bWtkaXIgfi9teS1hcHBzCmNobW9kIDcwMCB+L215LWFwcHM= .

```bash
$ echo -n "$(<scripts.yaml)" base64
```
5. Create a new Startup script.
```bash
$ vultr-cli script create \
--name Sample-Script \
--type boot \
--script bWtkaXIgfi9teS1hcHBzCmNobW9kIDcwMCB+L215LWFwcHM=
```
6. List all scripts.
```bash
$ vultr-cli script list
```
7. Get the details of a specific script by specifying a script ID.
```bash
$ vultr-cli script get script_id
```
Run vultr-cli script create --help to view all options.
Terraform
1. Create a startup script and apply.
```hcl
resource "vultr_startup_script" "boot" {
name = "Sample-Script"
type = "boot"   # boot pxe
script = <<-EOT
      #!/bin/sh

      mkdir -p /opt/my-apps
      chmod 700 /opt/my-apps
    EOT
}
```
2. Attach the script to an instance via user_data  or by setting script_id .
```hcl
resource "vultr_instance" "server" {
region = "ewr"
plan = "vc2-2c-4gb"
label = "scripted"
```
    # Option A: user_data cloud-init
user_data = <<-EOT
      #cloud-config
      runcmd:
        - echo "Hello from cloud-init" > /root/hello.txt
    EOT
    # Option B: associate the startup script
script_id = vultr_startup_script.boot.id
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Management
Tools and options for managing your Vultr account, resources, and
infrastructure settings.

Delete Startup Scripts
Learn how to permanently remove custom startup scripts from your Vultr
account when theyre no longer needed.

How to Delete Startup Scripts for
Vultr Instances
Introduction
Deleting Startup Scripts for Vultr instances completely removes the script from
your account. This step is necessary if you no longer need to run the commands
when provisioning Cloud Compute instances. After deleting a startup script, you
can't undo the operation, so you should take great care.
Follow this guide to delete Startup Scripts for Vultr instances using the Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Orchestration and select Scripts.
2. Select the target startup script and click the delete icon to remove the
script.
3. Confirm the new change and click Delete.
Vultr API
1. Send a GET request to the List Startup Scripts endpoint and note the
script ID.
```bash
$ curl "https://api.vultr.com/v2/startup-scripts" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete Startup Script endpoint and specify
a script ID.
```bash
$ curl "https://api.vultr.com/v2/startup-scripts/script_id" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all scripts.
```bash
$ vultr-cli script list
```
2. Delete a script by specifying a script ID.
```bash
$ vultr-cli script delete script_id
```
Run vultr-cli script delete --help to view all options.
Terraform
1. Open your Terraform configuration where the Startup Script is defined.
2. Remove the vultr_startup_script  resource block, or destroy it by target.
```hcl
resource "vultr_startup_script" "boot" {
name = "Sample-Script"
type = "boot"  # boot pxe
script = "#!/bin/sh\necho hi\n"

}
```
# To delete, either remove this block from configuration
# or run: terraform destroy -target vultr_startup_script.boot
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 0 changed, 1 destroyed.

FAQ
Frequently asked questions and answers about Vultrs products, services,
and platform features.

Frequently Asked Questions (FAQs)
About Vultr Startup Scripts
Introduction
These are the frequently asked questions for Startup Scripts for Vultr Instances.
Which Startup Scripts types are supported?
Vultr supports several types of Startup Scripts:
• Linux systems use cloud-init user-data. See [Deploy a Vultr Server with
• Cloud-Init User-Data](https://docs.vultr.com/how-to-deploy-a-vultr-server-with-cloudinit-userdata) for more details.
• Fedora CoreOS uses Ignition. See the Ignition user guide and the Fedora
CoreOS documentation for details.
• Windows and *BSD systems use boot scripts.
• iPXE scripts automatically install operating systems.
How can I apply a Startup Script to an
Instance?
Startup scripts require a two-step process. First, add a script to your account.
Then, assign that script to an instance under Server Settings when deploying
the instance.

Can I add Startup Scripts using the Vultr
API?
Yes, you can manage Startup Scripts using the Startup Scripts API endpoints
and the Vultr CLI.