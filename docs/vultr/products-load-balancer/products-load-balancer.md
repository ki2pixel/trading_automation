Load Balancer
Distribute traffic across multiple servers with Vultr's Load Balancer to
improve application reliability, performance, and scalability.

Provisioning
A guide explaining how to set up and configure a Vultr Load Balancer for
distributing traffic across multiple servers.

How to Provision Vultr Load
Balancer
Introduction
Vultr Load Balancer efficiently distributes incoming traffic across multiple
servers, ensuring balanced resource utilization and enhanced reliability. This
service prevents individual servers from becoming overloaded by managing
traffic evenly, which helps maintain application performance and uptime. By
provisioning a Load Balancer, you can enhance the scalability and resilience of
your applications, improving overall user experience.
Follow this guide to provision a Vultr Load Balancer on your Vultr account using
the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Load Balancers.
2. Click Create Load Balancer.
3. In Load Balancer Basics, set:
- Label
- Algorithm (default: Round Robin)
- Timeout (seconds)
- Number of Nodes (odd number)
4. Configure additional settings:
- Force HTTP to HTTPS redirects all HTTP traffic to HTTPS. To enable
this option, create at least one HTTPS forwarding rule and add a valid
SSL certificate.

- Proxy Protocol forwards the client’s original IP address to backend
nodes. If you enable this feature, configure your backend nodes to
accept Proxy Protocol headers.
- Sticky Sessions ensures that the Load Balancer routes a client’s
requests to the same backend server.
5. Under Health Checks, set Protocol, Port, Path, and Health Check
Intervals.
6. In Locations, select one or more deployment locations.
7. In Load Balancer Configuration, expand sections as needed:
- Non‑Public VPC Network (optional)
- Forwarding Rules
- Firewall Rules
- SSL
Note
Create at least one HTTPS forwarding rule before enabling HTTP/2 or
HTTP/3. Enable HTTP/3 only if an HTTP/2 rule exists.
8. Click Create Load Balancer.
Vultr API
1. Send a GET request to the List Regions endpoint and note your target
region ID.
```bash
$ curl "https://api.vultr.com/v2/regions" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST request to the Create Load Balancer endpoint to provision a
Load Balancer.

```bash
$ curl "https://api.vultr.com/v2/load-balancers" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
"region" : "{region_id}",
"balancing_algorithm" : "{roundrobin_or_leastconn}",
"ssl_redirect" : false,
"http2": false,
"http3": false,
"proxy_protocol" : false,
"timeout" : {timeout_in_seconds},
"label" : "{label}",
"nodes" : {number_of_nodes},
"health_check" : {
"protocol" : "{http_or_https_or_tcp}",
"port" : {port},
"path" : "/health",
"check_interval" : {interval_in_seconds},
"response_timeout" : {timeout_in_seconds},
"unhealthy_threshold" : {unhealthy_threshold},
"healthy_threshold" : {healthy_threshold}
},
"forwarding_rules": [
{
"frontend_protocol" : "{http_or_https_or_tcp}",
"frontend_port" : {frontend_port_number},
"backend_protocol" : "{http_or_https_or_tcp}",
"backend_port" : {backend_port_number}
}
],
"firewall_rules": [
{
"port" : {allowed_port_number},
"source" : "{source_ip_cidr}",
"ip_type" : "{v4_or_v6}"
}
],
"auto_ssl": {
"domain_zone" : "{your_domain}",
"domain_sub" : "{subdomain}"
}
}'
```
Visit the Create Load Balancer page to view additional attributes you
can include in your request.
3. Send a GET  request to the List Load Balancers endpoint to list all the
available Load Balancers.
```bash
$ curl "https://api.vultr.com/v2/load-balancers" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all Vultr regions and note the target region ID.
```bash
$ vultr-cli regions list
```
2. Create a Load Balancer.
```bash
$ vultr-cli load-balancer create \
--region "<region_id>" \
--balancing-algorithm "<roundrobin_or_leastconn>" \
--ssl-redirect false \
--proxy-protocol false \
--response-timeout <timeout_in_seconds> \
--label "<label>" \
--nodes <number_of_nodes> \
--protocol "<http_or_https_or_tcp>" \
--port <port> \
--path "/health" \
--check-interval <interval_in_seconds> \
--healthy-threshold <healthy_threshold> \
--unhealthy-threshold <unhealthy_threshold> \
--forwarding-rules
"frontend_protocol:<http_or_https_or_tcp>,frontend_port:<fron
tend_port_number>,backend_protocol:<http_or_https_or_tcp>,bac

kend_port:<backend_port_number>" \
--firewall-rules
"port:<allowed_port_number>,ip_type:<v4_or_v6>,source:<source
_ip_cidr>"
```
Run vultr-cli load-balancer create --help  to view additional options you can
apply when creating a Load Balancer.
3. List all the available Load Balancers.
```bash
$ vultr-cli load-balancer list
```
Terraform
1. Ensure the Vultr Terraform provider is configured in your Terraform project.
2. Define the Load Balancer resource in your Terraform configuration file.
```hcl
resource "vultr_load_balancer" "lb" {
region = "ewr"
label = "vultr-load-balancer"
balancing_algorithm = "roundrobin"
forwarding_rules {
frontend_protocol = "http"
frontend_port = 82
backend_protocol = "http"
backend_port = 81
}
health_check {
path = "/test"
port = 8080
protocol = "http"
response_timeout = 1
unhealthy_threshold = 2
check_interval = 3
healthy_threshold = 4

}
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Global Load Balancer
Regions
A guide explaining how to configure and manage geographic regions for
Vultr's Global Load Balancer service

How to Manage Vultr Global Load
Balancer Regions
Introduction
Global Load Balancer Regions enable the distribution of traffic depending on
your user locations by creating child Load Balancer instances linked to a parent
Load Balancer. You can create one child Load Balancer in each Vultr region and
link multiple instances to distribute traffic. User requests to the parent Load
Balancer are routed to the nearest child Load Balancer in a region depending on
the user's location.
Follow this guide to manage Vultr Global Load Balancer regions using the Vultr
Console, API or CLI.
Vultr Console
1. Navigate to Products and click Load Balancers.
2. Open the parent (global) Load Balancer.
3. In the Location table, click the + icon to Add Locations.
4. Select one or more regions and click Add Locations. This provisions child
Load Balancers in the selected regions.
5. For each region row:
- Use the Network column (if shown) to select the VPC/network for the
child.
- Use the + icon in the Instances column to attach instances in that
region.

Vultr API
1. Send a GET  request to the List Regions endpoint and note your target
region ID.
```bash
$ curl "https://api.vultr.com/v2/regions" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Load Balancers endpoint and note your
target Load Balancer's ID.
```bash
$ curl "https://api.vultr.com/v2/load-balancers" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PATCH  request to the Update Load Balancer endpoint to create a
child Load Balancer in the target region.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "global_regions": [
            "{region_1_id}",
            "{region_2_id}"
        ]
    }'
```

Vultr CLI
1. List all the region IDs, note down the required region IDs.
```bash
$ vultr-cli regions list
```
2. List all available instances and note the target Load Balancer's ID.
```bash
$ vultr-cli load-balancer list
```
3. Update the instance by adding a region ID to provision a child Load
Balancer in the target regions.
```bash
$ vultr-cli load-balancer update <load_balancer_id> --global-regions <region_1_id> <region_2_id>
```

Management
Manage your Vultr resources with essential operations including
monitoring, deletion, and resizing capabilities.

Monitor
Learn how to monitor your Vultr Load Balancers performance and health
status.

How to Monitor a Vultr Load
Balancer
Introduction
In the latest Vultr Console UI, Load Balancer health is surfaced on the Load
Balancer’s Details page. There is currently no dedicated metrics charting
section in the portal for Load Balancers.
Follow this guide to view status in the Vultr Console.
1. Navigate to Products and click Load Balancers.
2. Click your target Load Balancer to open its management page.
3. Review the Details card for Status, Checks, and URL.
4. Use Rules and Resources sections to inspect configuration and attached
nodes/instances.

Delete
Learn how to permanently remove a Vultr Load Balancer from your
account when its no longer needed.

How to Delete a Vultr Load
Balancer
Introduction
Deleting a Vultr Load Balancer involves removing the Load Balancer from your
Vultr account, which terminates its service and stops all associated traffic
distribution. This action will cease the load balancing operations and clear any
related configurations, effectively halting the management of incoming traffic
across your servers.
Follow this guide to delete a Vultr Load Balancer on your Vultr account using the
Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Load Balancers.
2. Click your target Load Balancer to open its management page.
3. Click Destroy Load Balancer in the top-right corner of the management
page.
4. Click Delete Load Balancer to permanently delete the target Load
Balancer instance.
Vultr API
1. Send a GET request to the List Load Balancers endpoint and note the
target Load Balancer's ID.
```bash
$ curl "https://api.vultr.com/v2/load-balancers" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete Load Balancer endpoint to delete
the target Load Balancer.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available instances and note the target Load Balancer's ID.
```bash
$ vultr-cli load-balancer list
```
2. Delete the target Load Balancer.
```bash
$ vultr-cli load-balancer delete <load-balancer-id>
```
Terraform
1. Open your Terraform configuration file for the existing Load Balancer.
2. Remove the vultr_load_balancer  resource block, or destroy it by target.
```hcl
resource "vultr_load_balancer" "lb" {
region = "ewr"
label = "vultr-load-balancer"
balancing_algorithm = "roundrobin"
forwarding_rules {
frontend_protocol = "http"
frontend_port = 82
backend_protocol = "http"
backend_port = 81
}
health_check {
path = "/test"
port = 8080
protocol = "http"
response_timeout = 1
unhealthy_threshold = 2
check_interval = 3
healthy_threshold = 4
}
}
```
# To delete, either remove this block from configuration
# or run: terraform destroy -target vultr_load_balancer.lb
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 0 changed, 1 destroyed.

Resize
Learn how to adjust the capacity and performance of your Vultr Load
Balancer by changing its size.

How to Resize a Vultr Load
Balancer
Introduction
Resizing a Vultr Load Balancer by increasing the number of nodes involves
updating the Load Balancer’s configuration to incorporate additional servers.
This adjustment distributes incoming traffic across a greater number of nodes,
which enhances both performance and reliability by reducing the load on
individual servers and improving overall capacity. By scaling up the number of
nodes, you ensure that your application can handle higher traffic volumes and
maintain optimal performance.
Follow this guide to resize a Vultr Load Balancer on your Vultr account using the
Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Load Balancers.
2. Click your target Load Balancer to open its management page.
3. In Details, click the pencil icon.
4. Adjust Number of Nodes (odd number).
5. Click Save changes.
Vultr API
1. Send a GET request to the List Load Balancers endpoint and note the
target Load Balancer's ID.
```bash
$ curl "https://api.vultr.com/v2/load-balancers" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Load Balancers endpoint to increase
the node size of the target Load Balancer by an odd number.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "nodes": {new-node-size}
    }'
```
3. Send a GET  request to the Get Load Balancer endpoint to fetch the
details of the target Load Balancer.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available instances and note the target Load Balancer's ID.
```bash
$ vultr-cli load-balancer list
```
2. Update the target Load Balancer's node size.

```bash
$ vultr-cli load-balancer update <load-balancer-id> --nodes
<new-node-size>
```
3. Get the details of the target Load Balancer.
```bash
$ vultr-cli load-balancer get <load-balancer-id>
```
Terraform
1. Open your Terraform configuration file for the existing Load Balancer.
2. Update the number of nodes in the configuration.
```hcl
resource "vultr_load_balancer" "lb" {
```
    # ...existing fields (region, forwarding_rules,
health_check, etc.)
nodes = 3
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Update
Learn how to modify your existing Vultr Load Balancer configuration to
adapt to changing requirements.

How to Update a Vultr Load
Balancer
Introduction
Updating a Vultr Load Balancer enables you to modify various settings,
including changing its label for better identification within your infrastructure.
This process does not affect the functionality, traffic distribution, or
configuration of the Load Balancer. By adjusting the label, you can easily
manage multiple Load Balancers, ensuring clear tracking across your
environment.
Follow this guide to update the label of a Vultr Load Balancer on your Vultr
account using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Load Balancers.
2. Click your target Load Balancer to open its management page.
3. In Details, click the pencil icon, update the name.
4. Click Save changes.
Vultr API
1. Send a GET request to the List Load Balancers endpoint and note the
target Load Balancer's ID.
```bash
$ curl "https://api.vultr.com/v2/load-balancers" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Load Balancer endpoint to update
the target Load Balancer's label.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "label": "{updated_label}"
    }'
```
3. Send a GET  request to the Get Load Balancer endpoint to fetch the
details of the target Load Balancer.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available instances and note the target Load Balancer's ID.
```bash
$ vultr-cli load-balancer list
```
2. Update the target Load Balancer's label.

```bash
$ vultr-cli load-balancer update <load-balancer-id> --label
"<updated_label>"
```
3. Get the details of the target Load Balancer.
```bash
$ vultr-cli load-balancer get <load-balancer-id>
```
Terraform
1. Open your Terraform configuration file for the existing Load Balancer.
2. Change the label value to the new name and apply.
```hcl
resource "vultr_load_balancer" "lb" {
```
    # ...existing fields (region, forwarding_rules,
health_check, etc.)
label = "updated-label-name"
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Instances
Virtual machines with dedicated CPU, RAM, and storage resources that
provide reliable cloud computing environments for various workloads.

Attach
Learn how to connect your Vultr instance to a load balancer for improved
traffic distribution and high availability.

How to Attach an Instance to a
Vultr Load Balancer
Introduction
A Load Balancer distributes incoming traffic across multiple instances to
improve performance, increase availability, and provide failover support. To
function correctly, instances within the same geographic region must be
attached to the Vultr Load Balancer.
Follow this guide to attach an instance to a Vultr Load Balancer on your Vultr
account using the Vultr Console, API, CLI, or Terraform.
Note
Vultr Load Balancer can be attached to both Vultr Compute (VMs) and Vultr
Bare Metal servers.
Vultr Console
1. Navigate to Products and click Load Balancers.
2. Click your target Load Balancer to open its management page.
3. In Resources, expand the location where you want to link instances.
4. In Instances, go to the desired region, and click Add Instances.
5. Select one or more instances from the same region, then click Save
Changes.
Vultr API
1. Send a GET request to the List Load Balancers endpoint and note the
target Load Balancer's ID.

```bash
$ curl "https://api.vultr.com/v2/load-balancers" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Instances endpoint and note your target
instance's ID, ensuring it is in the same geographic region as the Load
Balancer.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PATCH  request to the Update Load Balancer endpoint to attach
instances to the target Load Balancer.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "instances": [
            "<instance_1_id>",
            "<instance_2_id>"
        ]
    }'
```
4. Send a GET  request to the Get Load Balancer endpoint to fetch the
details of the target Load Balancer.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \

-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available instances and note the target Load Balancer's ID.
```bash
$ vultr-cli load-balancer list
```
2. List all available instances and note your target instance's ID, ensuring it is
in the same geographic region as the Load Balancer.
```bash
$ vultr-cli instance list
```
3. Update the target Load Balancer by attaching the new instances.
```bash
$ vultr-cli load-balancer update <load-balancer-id> --
instances "<instance_1_id>" "<instance_2_id>"
"<instance_3_id>"
```
4. Get the details of the target Load Balancer.
```bash
$ vultr-cli load-balancer get <load-balancer-id>
```
Terraform
1. Open your Terraform configuration file for the existing Load Balancer.
2. Add the target instance IDs under the nodes  attribute.

```hcl
resource "vultr_load_balancer" "lb" {
```
# ...existing fields (region, forwarding_rules,
health_check, etc.)
nodes = [
vultr_instance.web1.id,
vultr_instance.web2.id
]
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Detach
Learn how to remove a server instance from your Vultr Load Balancer
configuration

How to Detach an Instance from a
Vultr Load Balancer
Introduction
Detaching an instance from a Vultr Load Balancer removes it from traffic
distribution, allowing you to scale down or perform maintenance without
affecting other instances. Before detaching, ensure that the instance is no
longer needed for load balancing to prevent disruptions.
Follow this guide to attach an instance to a Vultr Load Balancer on your Vultr
account using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Load Balancers.
2. Click your target Load Balancer to open its management page.
3. In Resources, expand the location to view the Instances in your desired
region's table.
4. Click the + icon, deselect the instance(s) to remove, and save.
Vultr API
1. Send a GET request to the List Load Balancers endpoint and note the
target Load Balancer's ID.
```bash
$ curl "https://api.vultr.com/v2/load-balancers" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Instances endpoint and note your
currently attached instance IDs.
```bash
$ curl "https://api.vultr.com/v2/instances" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PATCH  request to the Update Load Balancer endpoint, omitting
the instance you want to detach.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "instances": [
            "<remaining_instance_1_id>",
            "<remaining_instance_2_id>"
        ]
    }'
```
4. Confirm the update with a GET  request:
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all Load Balancers and note the target Load Balancer's ID.

```bash
$ vultr-cli load-balancer list
```
2. List all instances and note which ones are currently attached.
```bash
$ vultr-cli instance list
```
3. Detach an instance by omitting it from the --instances  flag in the update
command.
```bash
$ vultr-cli load-balancer update <load-balancer-id> \
--instances "<remaining_instance_1_id>"
"<remaining_instance_2_id>"
```
4. Confirm the update.
```bash
$ vultr-cli load-balancer get <load-balancer-id>
```
Terraform
1. Open your Terraform configuration file for the existing Load Balancer.
2. Remove the target instance ID from the nodes  list.
```hcl
resource "vultr_load_balancer" "lb" {
```
    # ...existing fields (region, forwarding_rules,
health_check, etc.)
nodes = [

vultr_instance.web1.id
# vultr_instance.web2.id (this instance is detached)
]
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Configuration
Learn how to configure essential settings for your Vultr services including
networking options and traffic management rules.

Networking
Manage network configurations, connectivity options, and traffic routing
for your Vultr infrastructure.

Reverse DNS
A guide explaining how to set up reverse DNS records for your Vultr Load
Balancer to enable proper IP address to hostname resolution.

How to Configure Reverse DNS for
Vultr Load Balancer
Introduction
Configuring Reverse DNS and Adding IPv6 Addresses for your Vultr Load
Balancer enhances network management and accessibility. Reverse DNS allows
you to map your Load Balancer's IP address to a hostname, improving domain
reputation and troubleshooting capabilities. Adding IPv6 addresses ensures your
services are accessible over the newer IP protocol, providing broader
connectivity and future-proofing your infrastructure.
Follow this guide to configure Reverse DNS and add IPv6 addresses for your
Vultr Load Balancer using the Vultr Console.
1. Navigate to Products and click Load Balancers.
2. Click your target Load Balancer to open its management page.
3. Scroll to Resources for the desired location. Expand the section and find
the Load Balancer Nodes table.
4. Click the pencil icon next to the node IP to edit Reverse DNS. Enter the
hostname and save.
5. To add an IPv6 address (if available), use the node controls in the same
section.

VPC Network
A secure, isolated virtual network for connecting and managing your Vultr
resources with private communication.

How to Configure Network Settings
for Vultr Load Balancer
Introduction
Configuring Network Settings for your Vultr Load Balancer involves associating
it with a specific Virtual Private Cloud (VPC) network. This allows the Load
Balancer to operate within the specified network, ensuring it interacts correctly
with other resources and adheres to network policies.
Follow this guide to configure network settings for your Vultr Load Balancer
using the Vultr Console, API, CLI, or Terraform.
Vultr Console
Non‑Public VPC can be selected at creation time and, for Global Load Balancers,
per region after creation.
Create time
1. Navigate to Products and click Load Balancers.
2. Click Create Load Balancer.
3. In Load Balancer Configuration, click Non‑Public VPC Network and
select your VPC.
4. Complete the remaining settings and click Create Load Balancer.
Per‑region (Global Load Balancer)
1. Open the parent Load Balancer.
2. In the Location table, use the Network column on a region row to select
the VPC for that child Load Balancer, then save.

Vultr API
1. Send a GET request to the List Load Balancers endpoint to find your Load
Balancer ID.
```bash
curl "https://api.vultr.com/v2/load-balancers" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Identify the target Load Balancer and VPC ID from the response.
3. Send a PATCH request to the Update Load Balancer endpoint to assign a
VPC network.
```bash
curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
"vpc": "vpc-id-goes-here"
}'
```
Vultr CLI
1. List all available Load Balancers and note the ID of your target Load
Balancer.
```bash
vultr-cli load-balancer list
```
2. Update the Load Balancer to assign it to a VPC.

```bash
vultr-cli load-balancer update <load-balancer-id> --vpc <vpc-id>
```
Terraform
1. Open your Terraform configuration file for the existing Load Balancer and
VPC.
2. Add the vpc_id  field to associate the Load Balancer with your target VPC.
```hcl
resource "vultr_vpc" "private_net" {
region = "ewr"
description = "private-network"
}
resource "vultr_load_balancer" "lb" {
region = "ewr"
label = "vultr-load-balancer"
balancing_algorithm = "roundrobin"
vpc = vultr_vpc.private_net.id
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Auto SSL
A feature that automatically provisions and manages SSL certificates for
Vultr Load Balancers to secure website traffic.

How to Configure Auto SSL for
Vultr Load Balancer
Introduction
Configuring Auto SSL for Vultr Load Balancer enables automatic management of
SSL certificates, enhancing the security of your load-balanced applications by
ensuring encrypted connections. This feature simplifies the process of securing
your domains by automatically issuing and renewing SSL certificates, protecting
your data in transit and improving trust with your users.
Follow this guide to configure Auto SSL for your Vultr Load Balancer using the
Vultr Console or API.
Vultr Console
Note
Auto SSL can only be used with domains that are using Vultr's DNS. Please
ensure the subdomain or domain is pointed to the Load Balancer.
1. Navigate to Products and click Load Balancers.
2. Click your target Load Balancer to open its management page.
3. Scroll to SSL, click the pencil icon, and choose Auto SSL.
4. Optional: Provide a Subdomain and select a Domain.
5. Click Save changes.
Vultr API
1. Send a GET request to the List Load Balancers endpoint and note the
target Load Balancer's ID.

```bash
$ curl "https://api.vultr.com/v2/load-balancers" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Load Balancer endpoint and apply
Auto SSL to the target Load Balancer.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "auto_ssl": {
            "domain_zone" : "{your_domain}",
            "domain_sub" : "{subdomain}"
        }
    }'
```
3. Send a GET  request to the Get Load Balancer endpoint to fetch the
details of the target Load Balancer.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"

Firewall
A security feature that allows you to control network traffic to your Vultr
resources by configuring access rules.
```

How to Configure Firewall Rules for
Vultr Load Balancer
Introduction
Configuring Firewall Rules for Vultr Load Balancer allows you to control the
traffic that can reach your load-balanced applications. By setting up firewall
rules, you can specify which IP addresses and ports are allowed or blocked,
enhancing the security of your services. This feature helps protect your backend
servers from unauthorized access and potential threats by filtering incoming
traffic based on your defined criteria.
Follow this guide to configure firewall rules for your Vultr Load Balancer using
the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Load Balancers.
2. Click your target Load Balancer to open its management page.
3. Scroll down to Load Balancer Configuration, then click the pencil icon in
the Firewall Rules section.
4. Add rules by specifying Port, IP Type (v4/v6), and Source (CIDR).
5. Click Save changes.
Vultr API
1. Send a GET request to the List Load Balancers endpoint and note the
target Load Balancer's ID.
```bash
$ curl "https://api.vultr.com/v2/load-balancers" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Load Balancer endpoint to add a
firewall rule to the target Load Balancer's algorithm.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "firewall_rules": [
        {
            "port" : {allowed_port_number},
            "ip_type" : "{v4_or_v6}",
            "source" : "{source_ip_cidr}"
        }
        ]
    }'
```
3. Send a GET  request to the List Firewall Rules endpoint to view all firewall
rules set for the target Load Balancer.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}/firewall-rules" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available instances and note the target Load Balancer's ID.
```bash
$ vultr-cli load-balancer list
```
2. Add firewall rule to the target Load Balancer.
```bash
$ vultr-cli load-balancer update <loadbalancer-id> --
firewall-rules
"port:<allowed_port_number>,ip_type:<v4_or_v6>,source:<source
_ip_cidr>"
```
3. View all firewall rules set for the target Load Balancer.
```bash
$ vultr-cli load-balancer firewall list <load-balancer-id>
```
Terraform
1. Open your Terraform configuration file for the existing Load Balancer.
2. Add firewall_rules  blocks to allow specific ports and sources, then apply.
```hcl
resource "vultr_load_balancer" "lb" {
```
    # ...existing fields (region, label, forwarding_rules,
health_check, etc.)
firewall_rules {
frontend_port = 443
ip_type = "v4"
source = "0.0.0.0/0"
}
firewall_rules {
frontend_port = 8080
ip_type = "v6"
source = "::/0"

}
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

IP Address
Information about IP addresses in Vultr, including how to manage, assign,
and troubleshoot both IPv4 and IPv6 addresses for your cloud resources.

Introduction
Retrieving IPv4 and IPv6 Addresses for your Vultr Load Balancer allows you to
obtain the network addresses associated with your Load Balancer. These
addresses are essential for configuring DNS settings, integrating with other
services, or ensuring correct network routing. By noting these addresses, you
can efficiently manage and direct traffic to your Load Balancer.
Follow this guide to retrieve IPv4 and IPv6 addresses for your Vultr Load
Balancer using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products and click Load Balancers.
2. Click your target Load Balancer to open its management page.
3. Note the IPv4 and IPv6 addresses.
Vultr API
1. Send a GET request to the List Load Balancers endpoint and note the
target Load Balancer's ID.
```bash
$ curl "https://api.vultr.com/v2/load-balancers" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Get Load Balancer endpoint and note the IPv4
and IPv6 addresses for the target Load Balancer.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available instances and note the target Load Balancer's ID.
```bash
$ vultr-cli load-balancer list
```
2. Retrieve the IPv4 and IPv6 addresses for the target Load Balancer.
```bash
$ vultr-cli load-balancer get <load-balancer-id>

SSL Certification
A guide for installing SSL certificates on Vultr Load Balancers to enable
secure HTTPS connections
```

How to Apply an SSL Certificate to
Vultr Load Balancer
Introduction
Applying an SSL Certificate to your Vultr Load Balancer enhances the security of
your traffic by encrypting data transmitted between clients and your Load
Balancer. By adding a private key, certificate, and certificate chain, you can
ensure secure communications and improve trustworthiness for your users.
Follow this guide to apply an SSL certificate to your Vultr Load Balancer using
the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Load Balancers.
2. Click your target Load Balancer to open its management page.
3. Scroll to SSL, click the pencil icon, and choose Auto SSL.
4. Paste the Private Key, Certificate, and Certificate Chain.
5. Click Save changes.
Vultr API
1. Send a GET request to the List Load Balancers endpoint and note the
target Load Balancer's ID.
```bash
$ curl "https://api.vultr.com/v2/load-balancers" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Load Balancer endpoint to apply an
SSL certificate to the target Load Balancer.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "ssl": {
            "private_key": "-----BEGIN PRIVATE KEY-----
\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----",
            "certificate": "-----BEGIN CERTIFICATE-----
\nYOUR_CERTIFICATE_HERE\n-----END CERTIFICATE-----",
            "chain": "-----BEGIN CERTIFICATE-----
\nYOUR_CHAIN_CERTIFICATE_HERE\n-----END CERTIFICATE-----"
        }
    }'
```
Vultr CLI
1. List all available instances and note the target Load Balancer's ID.
```bash
$ vultr-cli load-balancer list
```
2. Apply SSL certificate to target Load Balancer.
```bash
$ vultr-cli load-balancer update <load-balancer-id> \
--private-key "-----BEGIN PRIVATE KEY-----
\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----" \
--certificate "-----BEGIN CERTIFICATE-----
\nYOUR_CERTIFICATE_HERE\n-----END CERTIFICATE-----" \
--certificate-chain "-----BEGIN CERTIFICATE-----
\nYOUR_CHAIN_CERTIFICATE_HERE\n-----END CERTIFICATE-----"
```

Terraform
1. Open your Terraform configuration file for the existing Load Balancer.
2. Add the ssl block with your certificate details.
```hcl
resource "vultr_load_balancer" "lb" {
```
# ...existing fields (region, label, forwarding_rules,
health_check, etc.)
ssl {
private_key = file("path/to/privkey.pem")
certificate = file("path/to/cert.pem")
chain = file("path/to/chain.pem")
}
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Algorithms
Learn how to select and configure the traffic distribution methods for your
Vultr Load Balancer

How to Manage Load Balancing
Algorithms on a Vultr Load
Balancer
Introduction
A Load Balancing algorithm determines how a Vultr Load Balancer distributes
incoming traffic to linked instances. Vultr Load Balancers support the Least
Connections and Round Robin algorithms that manage the distribution of traffic
to instances depending on your application needs.
Follow this guide to manage load balancing algorithms on a Vultr Load Balancer
using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Load Balancers.
2. Click your target Load Balancer to open its management page.
3. In Details, click the pencil icon to edit and manage the Algorithm.
- Round Robin: Distributes traffic evenly across all linked instances in
a circular order.
- Least Connections: Forwards traffic to the instance with the lowest
number of active connections.
4. Click Save changes to apply the Load Balancing algorithm.

Vultr API
1. Send a GET  request to the List Load Balancers endpoint and note the
target Load Balancer's ID.
```bash
$ curl "https://api.vultr.com/v2/load-balancers" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Load Balancer endpoint to update
the target Load Balancer's algorithm.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "balancing_algorithm": "{roundrobin_or_leastconn}"
    }'
```
3. Send a GET  request to the Get Load Balancer endpoint to fetch the
details of the target Load Balancer.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```

Vultr CLI
1. List all available instances and note the target Load Balancer's ID.
```bash
$ vultr-cli load-balancer list
```
2. Update the target Load Balancer's algorithm.
```bash
$ vultr-cli load-balancer update <load-balancer-id> --
balancing-algorithm "<roundrobin_or_leastconn>"
```
3. Get the details of the target Load Balancer.
```bash
$ vultr-cli load-balancer get <load-balancer-id>
```
Terraform
1. Open your Terraform configuration for the existing Load Balancer.
2. Update the balancing_algorithm  field in the configuration.
```hcl
resource "vultr_load_balancer" "lb" {
```
    # ...existing fields (region, label, health_check, etc.)
balancing_algorithm = "leastconn"
}
3. Apply the configuration and observe the following output:

Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Forwarding Rules
Learn how to create, modify, and delete forwarding rules to control traffic
distribution on your Vultr Load Balancer.

How to Manage Forwarding Rules
on a Vultr Load Balancer
Introduction
Forwarding rules on a Vultr Load Balancer define how incoming traffic is
directed to your backend servers. These rules allow you to specify a protocol,
port, and target protocol/port for routing requests. By configuring forwarding
rules, you can manage and optimize how traffic is distributed, enhancing the
performance and accuracy of your load balancing setup.
Follow this guide to manage forwarding rules on a Vultr Load Balancer using the
Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Load Balancers.
2. Click your target Load Balancer to open its management page.
3. Scroll down to Rules and click the pencil icon in the Forwarding Rules
section.
4. Verify, modify, or click Add to create a rule.
5. Set the LB Protocol / Port and Instance Protocol / Port.
- HTTP: Forwards traffic using the Hypertext Transfer Protocol (HTTP).
- HTTPS: Forwards traffic using the Hypertext Transfer Protocol Secure
(HTTPS). Enabling HTTPS rules requires an SSL certificate linked to the
Vultr Load Balancer instance.
- TCP: Forwards traffic using the Transmission Control Protocol (TCP).

- UDP: Forwards traffic using the User Datagram Protocol (UDP). Ideal
for latency-sensitive applications such as DNS, VoIP, gaming, and
streaming.
6. Save the changes.
Vultr API
1. Send a GET  request to the List Load Balancers endpoint and note the
target Load Balancer's ID.
```bash
$ curl "https://api.vultr.com/v2/load-balancers" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Create Forwarding Rule endpoint to add new
forwarding rules to the target Load Balancer.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}/forwarding-rules" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "frontend_protocol": "{load-balancer-protocol}",
        "frontend_port": {load-balancer-port},
        "backend_protocol": "{instance-protocol}",
        "backend_port": {instance-port}
    }'
```
3. Send a GET  request to the List Forwarding Rules endpoint to view the
forwarding rules of the target Load Balancer.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}/forwarding-rules" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available instances and note the target Vultr Load Balancer ID.
```bash
$ vultr-cli load-balancer list
```
2. Add new forwarding rules to the target Load Balancer.
```bash
$ vultr-cli load-balancer forwarding create <load-balancer-id> --frontend-protocol "<load-balancer-protocol>" --
frontend-port <load-balancer-port> --backend-protocol
"<instance-protocol>" --backend-port <instance-port>
```
3. List all forwarding rules for the target Load Balancer.
```bash
$ vultr-cli load-balancer forwarding list <load-balancer-id>
```
Terraform
1. Open your Terraform configuration for the existing Load Balancer.
2. Add or update forwarding_rules  to declare the listener and backend
mapping, then apply.
```hcl
resource "vultr_load_balancer" "lb" {
```
    # ...existing fields (region, label, health_check, etc.)
forwarding_rules {
frontend_protocol = "http"
frontend_port = 80
backend_protocol = "http"
backend_port = 8080
}
forwarding_rules {
frontend_protocol = "https"
frontend_port = 443
backend_protocol = "https"
backend_port = 8443
}
forwarding_rules {
frontend_protocol = "tcp"
frontend_port = 3306
backend_protocol = "tcp"
backend_port = 3306
}
forwarding_rules {
frontend_protocol = "udp"
frontend_port = 53
backend_protocol = "udp"
backend_port = 53
}
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Health Checks
A monitoring feature that verifies your backend servers are operational
by periodically testing their response to HTTP, HTTPS, or TCP requests.

How to Manage Health Checks on a
Vultr Load Balancer
Introduction
Health Checks on a Vultr Load Balancer monitor the status of your backend
servers by periodically sending requests to them. These checks assess whether
a server is healthy and responsive, enabling the Load Balancer to route traffic
only to servers that are functioning correctly. By configuring health checks, you
ensure that traffic is directed away from servers experiencing issues,
maintaining the reliability and performance of your application.
Follow this guide to manage the health checks on a Vultr Load Balancer using
the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Load Balancers.
2. Click your target Load Balancer to open its management page.
3. In Details, review current health status and click the pencil icon.
4. Scroll down to the Health Checks section to manage it.
5. Enter the target port in the Port field to monitor.
6. Set the Interval in seconds to perform health checks on the target port.
7. Set the Response timeout in seconds for how long the Load Balancer
should wait between responses on the target port.
8. Set the Unhealthy Threshold to define how many times an instance
should fail before the Load Balancer stops forwarding traffic.
9. Set the Healthy Threshold to define how many times an instance should
pass before the Load Balancer starts forwarding traffic to it.
10. Enter the URL path in the HTTP Path field to perform healthy checks.
11. Click Save changes to apply the changes.

Vultr API
1. Send a GET  request to the List Load Balancers endpoint and note the
target Load Balancer's ID.
```bash
$ curl "https://api.vultr.com/v2/load-balancers" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Load Balancer endpoint to update
the target Load Balancer's health checks configuration.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "health_check" : {
            "protocol" : "{http_or_https_or_tcp}",
            "port" : {port},
            "path" : "{path}",
            "check_interval" : {interval_in_seconds},
            "response_timeout" : {timeout_in_seconds},
            "unhealthy_threshold" : {unhealthy_threshold},
            "healthy_threshold" : {healthy_threshold}
        }
    }'
```
3. Send a GET  request to the Get Load Balancer endpoint to fetch the
details of the target Load Balancer.
```bash
$ curl "https://api.vultr.com/v2/load-balancers/{load-balancer-id}" \

-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available instances and note the target Load Balancer's ID.
```bash
$ vultr-cli load-balancer list
```
2. Update the target Load Balancer's health checks configuration.
```bash
$ vultr-cli load-balancer update <load-balancer-id> \
--protocol "<http_or_https_or_tcp>" \
--port {port} \
--path "{path}" \
--check-interval <interval_in_seconds> \
--response-timeout <timeout_in_seconds> \
--healthy-threshold <healthy_threshold> \
--unhealthy-threshold <unhealthy_threshold>
```
3. Get the details of the target Load Balancer.
```bash
$ vultr-cli load-balancer get <load-balancer-id>
```
Terraform
1. Open your Terraform configuration for the existing Load Balancer.
2. Add or update the health_check  block to define probe protocol, port, path,
and thresholds, then apply.

```hcl
resource "vultr_load_balancer" "lb" {
```
    # ...existing fields (region, label, forwarding_rules,
etc.)
health_check {
path = "/health"
port = 8080
protocol = "http"
response_timeout = 3
unhealthy_threshold = 2
check_interval = 10
healthy_threshold = 3
}
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

FAQ
Frequently asked questions and answers about Vultr's products, services,
and platform features.

create? 103
011 What should I do if my instances fail health checks? 103
012 How can I manage Load Balancers using the API? 104

Frequently Asked Questions About
Vultr Load Balancer
Introduction
These are the frequently asked questions for Vultr Load Balancer.
What is Vultr Load Balancer and how does it
simplify traffic management?
The Vultr Load Balancer is a fully managed solution designed to distribute
incoming traffic across multiple backend servers to ensure high availability and
reliability of your applications. It simplifies traffic management by automating
the distribution process and offering several features.
What types of load balancing algorithms are
available?
Vultr Load Balancers support two algorithms:
• Round Robin: Distributes traffic evenly across servers in sequence,
without considering the traffic load on each server. This is the default
algorithm.
• Least Connections: Directs traffic to the server with the lowest number
of active connections, making it ideal for applications with long-running
sessions.

Can I configure firewall rules on a Vultr Load
Balancer?
Yes, Vultr Load Balancers allow you to configure internal firewall rules similar to
Vultr’s stand-alone Firewall. These rules can restrict traffic based on IPs or
ranges. You can set firewall rules on the Add Load Balancer page and the
Networking menu of the Manage Load Balancer page.
How do forwarding rules work on a Vultr
Load Balancer?
Forwarding rules map a Load Balancer port to an Instance port. You can
configure rules for HTTP, HTTPS, or TCP protocols. For instance, you might
forward HTTP port 80 on the Load Balancer to port 8000 on the instances. You
can create up to 15 forwarding rules.
How do I view metrics for my Vultr Load
Balancer?
Metrics are available on the Metrics tab of the Manage Load Balancer page after
the Load Balancer has been running for a few minutes. Metrics provide insights
into performance and health.
How can I use VPC network with my Load
Balancer?
The VPC Network option allows you to forward traffic via a Virtual Private Cloud
(VPC) instead of the public network if your instances are attached to a VPC.
Changing the network interface will briefly disrupt connections.

What is the default interval between health
checks and how can it be changed?
The default interval between health checks is 15 seconds. You can adjust this
interval when configuring health checks on the Add Load Balancer page or the
Health Checks menu of the Manage Load Balancer page.
What are the restrictions on ports when
configuring firewall rules?
When setting firewall rules on a Vultr Load Balancer, ports 65300 to 65310 are
reserved for internal use by the Load Balancer and cannot be configured for
traffic forwarding.
What is the maximum number of forwarding
rules I can create?
You can create a maximum of 15 forwarding rules for each Load Balancer.
What should I do if my instances fail health
checks?
If an instance fails health checks:
• Verify that the instance is running and accessible.
• Check the configured port and protocol for accuracy.
• Adjust health check parameters such as the interval, timeout, and
thresholds if necessary.

How can I manage Load Balancers using the
API?
The Vultr API provides endpoints to:
• Create, list, and update Load Balancers.
• Manage forwarding rules, including creation, listing, retrieval, and deletion.