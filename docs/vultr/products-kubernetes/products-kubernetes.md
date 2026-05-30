Kubernetes
A comprehensive guide to Vultr Kubernetes, covering deployment,
capabilities, administration, and essential operational aspects of
container orchestration.

Provisioning
A guide explaining how to set up and deploy a new Kubernetes cluster
using Vultr Kubernetes Engine (VKE)

How to Provision a Vultr
Kubernetes Engine Cluster
Introduction
Vultr Kubernetes Engine (VKE) is a fully-managed service that lets you deploy
Kubernetes clusters with predictable pricing. Vultr manages the control plane
and worker nodes while providing integration with other managed services such
as Load Balancers, Block Storage, and DNS. VKE clusters simplify orchestration,
allowing you to focus on scaling and building applications with minimal
overhead. Vultr Kubernetes Engine (VKE) is ideal for automating CI/CD pipelines,
managing microservices, or deploying AI-driven applications with global reach
and reliability.
Follow this guide to provision a Vultr Kubernetes Engine cluster on your Vultr
Account using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Kubernetes.
2. Click Add Cluster.
3. Enter your desired VKE cluster name in the Cluster Name field.
4. Click the Kubernetes Version drop-down and select your target version.
5. Optional: Enable High Availability for multiple nodes and Vultr Firewall
to filter network traffic.
6. Under Cluster Configuration, click the Node Pool Type drop-down and
select the node instance type.
7. Click the Node Pool Plan drop-down and select the target node plan.
8. Enter a Label for your node and select the Number of Nodes to attach to
the cluster.
9. Choose a Vultr Location for your cluster.

10. Optional: Choose an existing VPC network from VPC Network dropdown
to create a new Vultr Kubernetes Engine (VKE) cluster with an existing VPC.
Note
An existing VPC can only be attached to a new VKE cluster if both are in
the same region. If no existing VPC is selected, the VKE cluster will
automatically provision a new VPC in the same region by default.
11. Click Deploy Now to provision the Vultr Kubernetes Engine (VKE) cluster.
Vultr API
1. Send a GET  request to the List Regions endpoint and note your target
Vultr region ID.
```bash
$ curl "https://api.vultr.com/v2/regions" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List available plans in region endpoint to
view all available instance plans in your chosen region and note the target
node pool plan.
```bash
$ curl "https://api.vultr.com/v2/regions/{region-id}/
availability" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a GET  request to the Get Kubernetes Versions endpoint and note
your target Kubernetes version to use.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/versions" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
4. Send a POST  request to the Create Kubernetes Cluster endpoint to
provision a VKE cluster with your target region, plan, and Kubernetes
version.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "label": "{cluster-name}",
        "region": "{region-id}",
        "version": "{kubernetes-version}",
        "node_pools": [
            {
                "node_quantity": {number-of-nodes},
                "label": "{node-label}",
                "plan": "{node-plan}"
            }
        ]
    }'
```
Visit the Create Kubernetes Cluster page to view additional attributes
you can apply to your VKE cluster provisioning request.
5. Send a GET  request to the List all Kubernetes Clusters endpoint to list
all VKE clusters in your Vultr account.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```

Vultr CLI
1. List all Vultr regions and note your target region ID.
```bash
$ vultr-cli regions list
```
2. List all available instance plans in your target region and note the target
node pool plan.
```bash
$ vultr-cli regions availability <region-id>
```
3. List all available Kubernetes versions and note your target version to use.
```bash
$ vultr-cli kubernetes versions
```
4. Provision a VKE cluster with your target node plan, region ID, Kubernetes
version and region.
```bash
$ vultr-cli kubernetes create --label "<cluster-name>" --
region "<region-id>" --version "<kubernetes-version>" --node-pools "quantity:<number-of-nodes>,plan:<node-plan>,label:<node-label>"
```
Run vultr-cli kubernetes create --help to view additional options you can
apply to your VKE cluster provisioning request.
5. List all VKE clusters in your Vultr account.

```bash
$ vultr-cli kubernetes list --summarize
```
Terraform
1. Ensure the Vultr Terraform provider is configured in your Terraform project.
2. Define a VKE cluster with one node pool and apply.
```hcl
resource "vultr_kubernetes" "vke" {
label = "vke-cluster-1"
region = "ewr"
version = "1.29.3+1"   # example version
node_pools {
node_quantity = 3
label = "pool-a"
plan = "vc2-2c-4gb"
}
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Features
Explore Vultr's advanced platform features that enhance security,
reliability, and deployment capabilities for your cloud infrastructure.

Firewall
A security feature that allows you to control network traffic to your Vultr
Kubernetes Engine cluster by defining access rules.

How to Enable Firewall for Vultr
Kubernetes Engine Cluster
Introduction
Vultr Kubernetes Engine (VKE) cluster Firewall is a critical security feature within
VKE cluster that allows you to control and protect network traffic to and from
your VKE cluster. By enabling VKE cluster Firewall, you can define specific rules
that ensure only authorized connections are allowed, enhancing the security of
your containerized applications.
Follow this guide to enable Firewall for your Vultr Kubernetes Engine cluster on
your Vultr account using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Kubernetes.
2. Click your target VKE cluster to open its management page.
3. Click Firewall.
4. Click Enable Firewall to deploy a Firewall for the target VKE cluster.
5. Click firewall group to manage Firewall rules.
6. Add Firewall rules according to requirements.
Vultr API
1. Send a GET request to the List Regions endpoint and note your target
Vultr region ID.
```bash
$ curl "https://api.vultr.com/v2/regions" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List available plans in region endpoint to
view all available instance plans in your chosen region and note the target
node pool plan.
```bash
$ curl "https://api.vultr.com/v2/regions/{region-id}/
availability" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a GET  request to the Get Kubernetes Versions endpoint and note
your target Kubernetes version to use.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/versions" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
4. Send a POST  request to the Create Kubernetes Cluster endpoint to
create a VKE cluster with Firewall enabled. Post-creation, note the cluster's
ID.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "label": "{cluster-name}",
        "region": "{region-id}",
        "version": "{kubernetes-version}",
        "enable_firewall": true,
        "node_pools": [
            {

                "node_quantity": {number-of-nodes},
                "label": "{node-label}",
                "plan": "{node-plan}"
            }
        ]
    }'
Upon enabling the Firewall for your target cluster, create a Firewall group
and add Firewall Rules to manage network traffic for your VKE cluster.
```
5. Send a GET  request to the Get Kubernetes Cluster endpoint to get the
details of the target VKE cluster.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters/
{cluster-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all Vultr regions and note your target region ID.
```bash
$ vultr-cli regions list
```
2. List all available instance plans in your target region and note the target
node pool plan.
```bash
$ vultr-cli regions availability <region-id>
```
3. List all available Kubernetes versions and note your target version to use.
```bash
$ vultr-cli kubernetes versions
```
4. Create a VKE cluster with Firewall enabled and note the target cluster's ID.
```bash
$ vultr-cli kubernetes create --label "<cluster-name>" --
region "<region-id>" --version "<kubernetes-version>" --
enable-firewall true --node-pools "quantity:<number-of-nodes>,plan:<node-plan>,label:<node-label>"
Upon enabling the Firewall for your target cluster, create a Firewall group
and add Firewall Rules to manage network traffic for your VKE cluster.
```
5. Get the deatils of the target VKE cluster.
```bash
$ vultr-cli kubernetes get <cluster-id>
```
Terraform
1. Open your Terraform configuration for the existing VKE cluster.
2. Enable the cluster firewall and apply.
```hcl
resource "vultr_kubernetes" "vke" {
```
    # ...existing fields (label, region, version, node_pools)
enable_firewall = true
}
Optional: Manage firewall rules with vultr_firewall_group  and
 resources if you need custom ingress/egress policies.
vultr_firewall_rule
3. Apply the configuration and observe the following output:

Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

High Availability
A feature that ensures continuous operation of Kubernetes clusters by
eliminating single points of failure.

How to Enable High Availability for
Vultr Kubernetes Engine Cluster
Introduction
High availability is a key feature of Vultr Kubernetes Engine (VKE) cluster that
ensures your cluster remains resilient and operational, even in the event of
unexpected failures. By enabling high availability, your VKE cluster is
distributed across multiple nodes and regions, reducing the risk of downtime
and ensuring continuous availability of your applications. This feature integrates
seamlessly with Vultr’s global cloud infrastructure, providing reliable
performance and redundancy.
Follow this guide to enable High Availability for your Vultr Kubernetes Engine
cluster using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Kubernetes.
2. Click Add Cluster.
3. Enter a Cluster Name.
4. Select the target version from the Kubernetes Version drop-down.
5. Select Enable High Availability to configure multiple nodes for your
cluster.
6. Choose the Node Pool Type.
7. Click the Node Pool Plan drop-down and select the desired node plan.
8. Provide a Label, and select the Number of Nodes.
9. Choose a Vultr Location for your cluster.
10. Click Deploy Now to launch your cluster.

Vultr API
1. Send a GET  request to the List Regions endpoint and note your target
Vultr region ID.
```bash
$ curl "https://api.vultr.com/v2/regions" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List available plans in region endpoint to
view all available instance plans in your chosen region and note the target
node pool plan.
```bash
$ curl "https://api.vultr.com/v2/regions/{region-id}/
availability" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a GET  request to the Get Kubernetes Versions endpoint and note
your target Kubernetes version to use.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/versions" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
4. Send a POST  request to the Create Kubernetes Cluster endpoint to
create a VKE cluster with high availability. Post-creation, note the cluster's
ID.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "label": "{cluster-name}",
        "region": "{region-id}",
        "version": "{kubernetes-version}",
        "ha_controlplanes": true,
        "node_pools": [
            {
                "node_quantity": {number-of-nodes},
                "label": "{node-label}",
                "plan": "{node-plan}"
            }
        ]
    }'
```
5. Send a GET  request to the Get Kubernetes Cluster endpoint to get the
details of the target VKE cluster.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters/
{cluster-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all Vultr regions and note your target region ID.
```bash
$ vultr-cli regions list
```
2. List all available instance plans in your target region and note the target
node pool plan.
```bash
$ vultr-cli regions availability <region-id>
```
3. List all available Kubernetes versions and note your target version to use.
```bash
$ vultr-cli kubernetes versions
```
4. Create a VKE cluster with --high-avail  flag and note the target cluster's ID.
```bash
$ vultr-cli kubernetes create --label "<cluster-name>" --
region "<region-id>" --version "<kubernetes-version>" --high-avail true --node-pools "quantity:<number-of-nodes>,plan:<node-plan>,label:<node-label>"
```
5. Get the deatils of the target VKE cluster.
```bash
$ vultr-cli kubernetes get <cluster-id>
```
Terraform
1. Open your Terraform configuration for the existing VKE cluster.
2. Enable HA control planes by setting ha_controlplanes = true .
```hcl
resource "vultr_kubernetes" "vke" {
```
    # ...existing fields (label, region, version, node_pools)
ha_controlplanes = true
}
3. Apply the configuration and observe the following output:

Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Deploy Applications
A guide explaining how to deploy applications on your Vultr Kubernetes
Engine cluster.

How to Deploy an Application on
Vultr Kubernetes Engine Cluster
Introduction
Vultr Kubernetes Engine (VKE) provides a streamlined way to deploy pre-configured applications such as AMD Device Config, AMD GPU Operator, Cert-Manager, Vultr Webhook, Exascaler CSI, kube-state-metrics, Kube AI Models,
Kubernetes Dashboard, Longhorn, and Rook Ceph. These applications extend
cluster functionality by enabling features like GPU acceleration, certificate
management, storage integration, autoscaling, and monitoring. You can deploy
these applications with default settings or customize them using YAML
configurations to meet specific requirements.
Follow this guide to deploy a pre-configured application on your Vultr
Kubernetes Engine cluster in your Vultr account using the Vultr Console or
Terraform.
Vultr Console
1. Navigate to Products and click Kubernetes.
2. Click your target VKE cluster to open its management page.
3. Click Applications.
4. Select an application from the list.
5. Optional: In Advanced Configuration, enter custom YAML values or leave
the field blank to use the application's default settings.
6. Click Deploy Now to deploy the application.

Terraform
1. Ensure the Terraform Kubernetes provider is configured using your VKE
kubeconfig.
```hcl
provider "kubernetes" {
config_path = "./kubeconfig.yaml"  # from VKE cluster
configuration
}
```
2. Define a simple Deployment (or use Helm) and apply.
```hcl
resource "kubernetes_namespace" "apps" {
metadata { name = "apps" }
}
resource "kubernetes_deployment" "nginx" {
metadata {
name = "nginx"
namespace =
kubernetes_namespace.apps.metadata[0].name
labels = { app = "nginx" }
}
spec {
replicas = 1
selector { match_labels = { app = "nginx" } }
template {
metadata { labels = { app = "nginx" } }
spec {
container {
name = "nginx"
image = "nginx:1.25"
port { container_port = 80 }
}
}
}

}
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Management
Manage your Vultr Kubernetes clusters with configuration options,
deletion procedures, and resource management tools.

Cluster Configuration
Learn how to obtain your Vultr Kubernetes Engine (VKE) cluster
configuration for kubectl access and management

How to Retrieve the Cluster
Configuration for Vultr Kubernetes
Engine Cluster
Introduction
Retrieving a Vultr Kubernetes Engine (VKE) cluster configuration allows you to
access essential details about your Kubernetes cluster, including API endpoints,
authentication credentials, and resource specifications. This process is crucial
for managing and interacting with your VKE cluster effectively. Vultr Kubernetes
Engine provides straightforward methods to retrieve these configurations,
ensuring you have the necessary information to operate and scale your VKE
cluster efficiently.
Follow this guide to retrieve the Vultr Kubernetes Engine cluster configuration
from your Vultr account using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Kubernetes.
2. Click your target VKE cluster to open its management page.
3. In the top-right corner, click Download Configuration.
Vultr API
1. Send a GET request to the List all Kubernetes Clusters endpoint and
note the target VKE cluster's ID.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Get Kubernetes Cluster Kubeconfig
endpoint to retrieve the config file for the target VKE cluster.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters/
{cluster-id}/config" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-o kubeconfig.yaml
```
Vultr CLI
1. List the available VKE clusters in your Vultr account and note the target
VKE cluster's ID.
```bash
$ vultr-cli kubernetes list --summarize
```
2. Retrieve the VKE cluster configuration file.
```bash
$ vultr-cli kubernetes config <cluster-id> --output-file
"<your-path>"
```
Terraform
1. Use the  vultr_kubernetes  data source to read an existing cluster and output
its kubeconfig.

```hcl
data "vultr_kubernetes" "cluster" {
```
    # identify the cluster by id or label
cluster_id = var.cluster_id
}
output "kubeconfig" {
value = data.vultr_kubernetes.cluster.kubeconfig
}
2. Run terraform apply to fetch the kubeconfig.
Example output:
```yaml
Apply complete! Resources: 0 added, 0 changed, 0 destroyed.
Outputs:
kubeconfig = <<EOT
apiVersion: v1
clusters:
```
- cluster:
certificate-authority-data: REDACTED
server: https://vke-abc123.us-east-1.vultr-k8s.com:6443
name: vke-abc123
contexts:
- context:
cluster: vke-abc123
user: vke-abc123-user
name: vke-abc123
current-context: vke-abc123
kind: Config
preferences: {}
users:
- name: vke-abc123-user
user:
token: REDACTED
EOT

Delete
Learn how to permanently remove a Kubernetes cluster from your Vultr
account

How to Delete a Vultr Kubernetes
Engine Cluster
Introduction
Deleting a Vultr Kubernetes Engine (VKE) cluster involves completely removing
your VKE cluster’s infrastructure, including the control plane, worker nodes, and
all associated resources. This process is final and should be performed carefully.
VKE cluster provides a simple method to ensure the thorough and efficient
deletion of your VKE cluster when it’s no longer required.
Follow this guide delete a Vultr Kubernetes Engine cluster from your Vultr
account using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Kubernetes.
2. Click your target VKE cluster to open its management page.
3. Click the delete icon in the top right of the management page.
4. Check the Destroy VKE Cluster box in the confirmation prompt, and click
Destroy VKE Cluster to permanently delete the target VKE cluster.
Vultr API
1. Send a GET request to the List all Kubernetes Clusters endpoint and
note the target VKE cluster's ID.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete Kubernetes Cluster endpoint to
delete the target VKE cluster.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters/
{cluster-id}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a DELETE  request to the Delete VKE Cluster and All Related
Resources endpoint to delete the target VKE cluster along with all linked
resources.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters/
{cluster-id}/delete-with-linked-resources" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List the available VKE clusters and note the target VKE cluster's ID.
```bash
$ vultr-cli kubernetes list --summarize
```
2. Delete the target VKE cluster.
```bash
$ vultr-cli kubernetes delete <cluster-id>
```
3. Delete the target VKE cluster along with all linked resources.
```bash
$ vultr-cli kubernetes delete --delete-resources <cluster-id>
```
Terraform
1. Open your Terraform configuration where the VKE cluster is defined.
2. Remove the vultr_kubernetes resource block, or destroy it by target.
```hcl
resource "vultr_kubernetes" "vke" {
```
# ...existing fields (label, region, version, node_pools)
}
# To delete, either remove this block from configuration
# or run: terraform destroy -target vultr_kubernetes.vke
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 0 changed, 1 destroyed.

Linked Resources
A feature that allows you to view and manage resources connected to
your current Vultr product or service.

How to Retrieve Linked Resources
for Vultr Kubernetes Engine Cluster
Introduction
Linked Resources in a Vultr Kubernetes Engine (VKE) cluster include critical
components like load balancers and block storage, which provide network traffic
management and persistent storage solutions for your Kubernetes environment.
Accessing these linked resources is important for managing and optimizing your
cluster's performance and storage.
Follow this guide to retrieve the linked resources associated with your VKE
cluster from your Vultr account using the Vultr Console or API.
Vultr Console
1. Navigate to Products and click Kubernetes.
2. Click your target VKE cluster to open its management page.
3. Click Linked Resources.
4. You will be able to view any linked Block Storages and Load Balancer to
your VKE cluster.
Vultr API
1. Send a GET request to the List Kubernetes Clusters endpoint and note
the target VKE cluster's ID.
```bash
$ curl -X GET "https://api.vultr.com/v2/kubernetes/clusters"
\
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json"
```
2. Send a GET  request to the Kubernetes Resources endpoint to list all the
attached resources.
```bash
$ curl -X GET "https://api.vultr.com/v2/kubernetes/clusters/
<cluster-id>/resources" \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json"
```

Upgrade
A guide explaining how to update your Vultr Kubernetes Engine (VKE)
cluster to a newer version

How to Upgrade the Cluster
Version for Vultr Kubernetes
Engine Cluster
Introduction
Upgrading a Vultr Kubernetes Engine (VKE) cluster version involves updating
both the control plane and worker nodes to a newer Kubernetes version. This
ensures that your cluster benefits from the latest features, improvements, and
security patches. Vultr Kubernetes Engine simplifies the upgrade process,
allowing you to maintain your VKE cluster’s efficiency and compatibility with
new Kubernetes releases.
Warning
Upgrading your VKE cluster will result in new worker nodes being provisioned,
causing node IPs to change. Ensure that any dependencies relying on static
node IPs are updated accordingly to prevent disruptions.
Follow this guide to upgrade your Vultr Kubernetes Engine cluster version on
your Vultr account using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Kubernetes.
2. Click your target VKE cluster to open its management page.
3. Click Manage Upgrades.
4. If any upgrades are available for the VKE cluster, they will be displayed on
the right side with a Start Upgrade button.
5. Click Start Upgrade. The upgrade process may take a few minutes.

Vultr API
1. Send a GET  request to the List all Kubernetes Clusters endpoint and
note the target VKE cluster's ID.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Get Kubernetes Available Upgrades
endpoint to list available upgrades for your VKE cluster.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters/
{cluster-id}/available-upgrades" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Start Kubernetes Cluster Upgrade endpoint
to start the VKE cluster upgrade.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters/
{cluster-id}/upgrades" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "upgrade_version" : "{target-kubernetes-version}"
    }'
```

Vultr CLI
1. List the available VKE clusters in your Vultr account and note the target
VKE cluster's ID.
```bash
$ vultr-cli kubernetes list --summarize
```
2. List all the available upgrades for the target VKE cluster.
```bash
$ vultr-cli kubernetes upgrades list <cluster-id>
```
3. Start the upgrade process for the target VKE cluster.
```bash
$ vultr-cli kubernetes upgrades start <cluster-id> --version
"<target-kubernetes-version>"
```
Terraform
1. Open your Terraform configuration for the existing VKE cluster.
2. Set the cluster version  to the desired target and apply. Worker nodes will
be recreated.
```hcl
resource "vultr_kubernetes" "vke" {
```
    # ...existing fields (label, region, node_pools)
version = "1.29.3+1"   # target version
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Update
Learn how to update your Vultr Kubernetes Engine (VKE) clusters label to
better organize and identify your clusters without disrupting workloads or
configurations.

How to Update a Vultr Kubernetes
Engine Cluster
Introduction
Updating a Vultr Kubernetes Engine (VKE) cluster enables you to change its
label without affecting workloads, configurations, or underlying resources.
Labels help you effectively manage multiple clusters, ensuring clear
identification and organization within your infrastructure.
Follow this guide to update a Vultr Kubernetes Engine cluster in your Vultr
account using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Kubernetes.
2. Click your target VKE cluster to open its management page.
3. In the Overview section, find the cluster's Label.
4. Click the edit icon and update the Label with the appropriate name.
Vultr API
1. Send a GET request to the List all Kubernetes Clusters endpoint and
note the target VKE cluster's ID.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Kubernetes Cluster endpoint to
update the label of the target VKE cluster.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters/
{cluster-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "label": "{updated-cluster-name}"
    }'
```
Vultr CLI
1. List the available VKE clusters and note the target VKE cluster's ID.
```bash
$ vultr-cli kubernetes list --summarize
```
2. Update the target VKE cluster.
```bash
$ vultr-cli kubernetes update <cluster-id> --label "<updated-cluster-name>"
```
Terraform
1. Open your Terraform configuration for the existing VKE cluster.
2. Change the label and apply.
```hcl
resource "vultr_kubernetes" "vke" {
```
    # ...existing fields (region, version, node_pools)
label = "updated-cluster-name"
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Node Pool
A grouping of worker nodes with identical configurations within a
Kubernetes cluster.

Delete
Learn how to remove node pools from your Vultr Kubernetes Engine (VKE)
cluster to adjust your clusters resources.

How to Delete Node Pools from a
Vultr Kubernetes Engine Cluster
Introduction
Managing resources efficiently in a Vultr Kubernetes Engine (VKE) cluster
includes the ability to remove individual worker nodes or delete entire Node
Pools when scaling down infrastructure. Removing a single instance from a
Node Pool ensures better cost management and workload reallocation, while
deleting an entire Node Pool eliminates unnecessary resources and optimizes
cluster performance.
Follow this guide to delete a Node or an entire Node Pool from a Vultr
Kubernetes Engine cluster on your Vultr account using the Vultr Console, API,
CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Kubernetes.
2. Click your target VKE cluster to open its management page.
3. Click Nodes.
4. Locate your target Node Pool and click the plus icon to expand the Node
Pool to view the attached instances.
5. Click the delete icon to remove the target Node from the Node Pool.
6. To delete a Node Pool, click the delete icon at the Node Pool level.
7. Check the Yes, destroy this node pool box in the confirmation prompt,
and click Destroy Node Pool to permanently delete the target Node Pool.

Vultr API
1. Send a GET  request to the List all Kubernetes Clusters endpoint and
note the target VKE cluster's ID.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters" \
-X GET \
-H "Authorization: Bearer $VULTR_API_KEY"
```
2. Send a GET  request to the List NodePools endpoint to view all Node Pools
and note the target Node Pool's ID.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters/
{cluster-id}/node-pools" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a GET  request to the Get NodePool endpoint and note the target
Node's ID.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters/
{cluster-id}/node-pools/{nodepool-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
4. Send a DELETE  request to the Delete NodePool Instance endpoint to
delete the target Node from the Node Pool.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters/
{cluster-id}/node-pools/{nodepool-id}/nodes/{node-id}" \

-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
5. Send a DELETE  request to the Delete Nodepool endpoint to delete the
target Node Pool.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters/
{cluster-id}/node-pools/{nodepool-id}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List the available VKE clusters in your Vultr account and note the target
VKE cluster's ID.
```bash
$ vultr-cli kubernetes list --summarize
```
2. List all the available Node Pools in the VKE cluster and note the target
Node Pool's ID.
```bash
$ vultr-cli kubernetes node-pool list <cluster-id> --
summarize
```
3. List the attached instances of the target Node Pool and note the taget
Node's ID.
```bash
$ vultr-cli kubernetes node-pool get <cluster-id> <nodepool-id>
```
4. Delete the target Node from the Node Pool.
```bash
$ vultr-cli kubernetes node-pool node delete <cluster-id>
<nodepool-id> <node-id>
```
5. Delete the target Node Pool from the VKE cluster.
```bash
$ vultr-cli kubernetes node-pool delete <cluster-id>
<nodepool-id>
```
Terraform
1. Open your Terraform configuration for the existing VKE cluster.
2. Remove the Node Pool block you want to delete, or reduce node_quantity  to
remove nodes.
```hcl
resource "vultr_kubernetes" "vke" {
```
    # ...existing fields (label, region, version)
    # keep only the node pools you want to retain
node_pools {
node_quantity = 3
label = "pool-a"
plan = "vc2-2c-4gb"
}
    # node_pools "pool-b" removed from configuration
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Recycle
A feature that allows you to restart your Vultr instance while preserving
its data and configuration.

How to Recycle a Node Pool
Instance in a Vultr Kubernetes
Engine Cluster
Introduction
Recycling a Node Pool instance in a Vultr Kubernetes Engine (VKE) cluster
involves removing a specific node and allowing the cluster to replace it with a
fresh instance. This operation is useful for resolving node-level issues, applying
updates, or recovering from resource constraints without disrupting the entire
Node Pool.
Warning
Recycling a node permanently deletes the target instance and replaces it with
a new one of the same configuration. Any ephemeral data, logs, or local
configurations will be lost. Workloads will be rescheduled to other available
nodes or the newly created instance. Linked resources remain attached, but if
the node was part of a Load Balancer backend, there may be brief downtime
while the new node is registered. To prevent data loss, ensure that important
data is stored in Persistent Volumes, external storage, or backed up
appropriately before recycling.
Follow this guide to recycle a Node in a Vultr Kubernetes Engine cluster on your
Vultr account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products and click Kubernetes.
2. Click your target VKE cluster to open its management page.
3. Click Nodes.

4. Locate your target Node Pool and click the plus icon to expand the Node
Pool to view the attached instances.
5. To recycle the target Node, click the Replace Node icon.
6. Check the Yes, replace this node box in the confirmation prompt, and
click Replace Node to replace the target Node with a new one.
Vultr API
1. Send a GET  request to the List all Kubernetes Clusters endpoint and
note the target VKE cluster's ID.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters" \
-X GET \
-H "Authorization: Bearer $VULTR_API_KEY"
```
2. Send a GET  request to the List NodePools endpoint to view all Node Pools
and note the target Node Pool's ID.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters/
{cluster-id}/node-pools" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a GET  request to the Get NodePool endpoint and note the target
Node's ID.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters/
{cluster-id}/node-pools/{nodepool-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
4. Send a POST  request to the Recycle a NodePool Instance endpoint to
replace the target Node with a new one.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters/
{cluster-id}/node-pools/{nodepool-id}/nodes/{node-id}/
recycle" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List the available VKE clusters in your Vultr account and note the target
VKE cluster's ID.
```bash
$ vultr-cli kubernetes list --summarize
```
2. List all the available Node Pools in the VKE cluster and note the target
Node Pool's ID.
```bash
$ vultr-cli kubernetes node-pool list <cluster-id> --
summarize
```
3. List the attached instances of the target Node Pool and note the target
Node's ID.
```bash
$ vultr-cli kubernetes node-pool get <cluster-id> <nodepool-id>
```
4. Recycle the target Node by replacing it with a new one.

```bash
$ vultr-cli kubernetes node-pool node recycle <cluster-id>
<nodepool-id> <node-id>
```

Scale
Learn how to increase or decrease the number of nodes in a Vultr
Kubernetes Engine (VKE) cluster node pool to accommodate your
workload requirements.

How to Scale Node Pools in a Vultr
Kubernetes Engine Cluster
Introduction
Scaling a Vultr Kubernetes Engine (VKE) cluster involves adjusting the number
of worker nodes to match fluctuating workload demands. This can be done by
either adding new Node Pools to expand the cluster or resizing existing ones,
ensuring the cluster can efficiently handle changing application requirements
while maintaining optimal performance. Vultr Kubernetes Engine offers an
intuitive process for scaling Node Pools based on the needs of your application.
Follow this guide to scale a node pool in your Vultr Kubernetes Engine cluster on
your Vultr account using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Kubernetes.
2. Click your target VKE cluster to open its management page.
3. Click Nodes.
4. To add a new Node Pool, click Add Node Pool.
5. Select a Node Pool Type and Plan from the drop-down.
6. Provide a Label and select Number of Nodes to attach to the cluster.
7. Click Create Node Pool. This will add a new Node Pool to the VKE cluster.
8. Click Number of Nodes to resize any existing Node Pool.
9. Choose a Scaling Type amongst Autoscale and Manual.
- For Autoscale: set the Minimum Nodes and Maximum Nodes.
- For Manual: set the number of Nodes.
10. Click Apply to resize the Node Pool.

Vultr API
1. Send a GET  request to the List all Kubernetes Clusters endpoint and
note the target VKE cluster's ID.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters" \
-X GET \
-H "Authorization: Bearer $VULTR_API_KEY"
```
2. Send a POST  request to the Create NodePool endpoint to add a new Node
Pool to the VKE Cluster.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters/
{cluster-id}/node-pools" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
-d '{
        "node_quantity": {number-of-nodes},
        "min_nodes": {min-number-of-nodes},
        "max_nodes": {max-number-of-nodes},
        "auto_scaler": true,
        "tag": "{tag}",
        "label": "{node-label}",
        "plan": "{node-plan}"
    }'
```
Visit the Create NodePool page to view additional attributes you can
apply while creating a new Node Pool for your VKE cluster.
3. Send a GET  request to the List NodePools endpoint to view all Node Pools
and note the target Node Pool's ID.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters/
{cluster-id}/node-pools" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
4. Send a PATCH  request to the Update NodePool endpoint to resize the
target Node Pool.
```bash
$ curl "https://api.vultr.com/v2/kubernetes/clusters/
{cluster-id}/node-pools/{node-pool-id}" \
    -X PATCH \
    -H "Authorization: Bearer ${VULTR_API_KEY}" \
    -H "Content-Type: application/json" \
    -d '{
        "node_quantity": {number-of-nodes},
        "min_nodes": {min-number-of-nodes},
        "max_nodes": {max-number-of-nodes},
        "auto_scaler": true,
        "tag": "{tag}"
    }'
```
Visit the Update NodePool page to view additional attributes you can
apply while resizing your Node Pool.
Vultr CLI
1. List the available VKE clusters in your Vultr account and note the target
VKE cluster's ID.
```bash
$ vultr-cli kubernetes list --summarize
```
2. Add another Node Pool to the target VKE cluster.
```bash
$ vultr-cli kubernetes node-pool create <cluster-id> \
--label "<node-label>" \
--plan "<node-plan>" \
--quantity <number-of-nodes> \
--min-nodes <min-number-of-nodes> \
--max-nodes <max-number-of-nodes> \
--auto-scaler true \
--tag "<tag>"
```
Run vultr-cli kubernetes node-pool create --help  to view additional options
you can apply while creating a new Node Pool for your VKE cluster.
3. List all the available Node Pools in the VKE cluster and note the target
Node Pool's ID.
```bash
$ vultr-cli kubernetes node-pool list <cluster-id> --
summarize
```
4. Resize the target Node Pool.
```bash
$ vultr-cli kubernetes node-pool update <cluster-id> <node-pool-id> \
--quantity <number-of-nodes> \
--min-nodes <min-number-of-nodes> \
--max-nodes <max-number-of-nodes> \
--auto-scaler true \
--tag "<tag>" \
--node-labels "<key1=value1,key2=value2>"
```
Run vultr-cli kubernetes node-pool update --help  to view additional options
you can apply while resizing your Node Pool.
Terraform
1. Open your Terraform configuration for the existing VKE cluster.

2. Add a new node_pools  block or update an existing one to change size or
autoscaler settings, then apply.
```hcl
resource "vultr_kubernetes" "vke" {
```
    # ...existing fields (label, region, version)
    # resize an existing pool
node_pools {
node_quantity = 5
label = "pool-a"
plan = "vc2-2c-4gb"
min_nodes = 3
max_nodes = 8
auto_scaler = true
}
    # optionally add another node pool
node_pools {
node_quantity = 2
label = "pool-b"
plan = "vc2-2c-4gb"
}
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Changelog
A chronological record of updates, improvements, and changes to Vultr
Kubernetes Engine.

Vultr Kubernetes Engine Changelog
Introduction
Vultr Kubernetes Engine (VKE) is a fully managed Kubernetes product with
predictable pricing. When you deploy VKE, you get a managed Kubernetes
control plane that includes our Cloud Controller Manager (CCM) and the
Container Storage Interface (CSI).
This changelog lists important changes for each Kubernetes version we support
in VKE. Changelogs are also referred to as release notes. Historical changelogs
for archived versions are available below.
Current Versions
VKE on 1.35.x
v1.35.2+1 (2026-03-17)
• calico -> v3.31.4
• etcd -> v3.6.8
• vultr-ccm -> v0.17.0
• vultr-csi -> v0.18.0
• cni -> v1.9.1
• crictl -> v1.35.0
• runc -> v1.4.1
• containerd -> v2.2.2

• CoreDNS → v1.14.2
• Enable CoreDNS autopath
• Add UDP support for Vultr CCM
1.35.0+1 (2026-02-17)
• Initial release of v1.35 support
VKE on 1.34.x
v1.34.1+3 (2026-01-09)
• Resolved issue preventing the cluster autoscaler from performing scale
operations
v1.34.1+2 (2025-11-07)
• vultr-ccm: v0.16.0
• Resolve Vultr Load Balancer status update failures during activation
v1.34.1+1 (2025-10-27)
• Initial release of v1.34 support

VKE on 1.33.x
v1.33.5+3 (2026-01-09)
• Resolved issue preventing the cluster autoscaler from performing scale
operations
v1.33.5+2 (2025-11-07)
• vultr-ccm: v0.16.0
• Resolve Vultr Load Balancer status update failures during activation.
v1.33.5+1 (2025-10-27)
• calico: v3.30.3
• etcd: v3.6.6
• vultr-ccm: v0.15.0
• vultr-csi: v0.17.1
• cni: v1.8.0
• crictl: v1.34.0
• runc: v1.3.2
• containerd: v1.7.25
• Upgrade workers node to Ubuntu 24.04 LTS.
• Resolved Vultr CSI block device symlink issue on nodes.
v1.33.0+1 (2025-05-14)
• Initial release of v1.33 support

VKE on 1.32.x
v1.32.9+3 (2026-01-09)
• Resolved issue preventing the cluster autoscaler from performing scale
operations
v1.32.9+2 (2025-11-07)
• vultr-ccm -> v0.16.0
• Resolve Vultr Load Balancer status update failures during activation
v1.32.9+1 (2025-10-27)
• calico -> v3.30.3
• etcd -> v3.6.6
• vultr-ccm -> v0.15.0
• vultr-csi -> v0.17.1
• cni -> v1.8.0
• crictl -> v1.34.0
• runc -> v1.3.2
• containerd -> v1.7.25
• Upgrade workers node to Ubuntu 24.04 LTS
• Resolved Vultr CSI block device symlink issue on nodes
v1.32.4+1 (2025-05-14)
• calico -> v3.30.0
• etcd -> v3.5.21
• vultr-ccm -> v0.14.0
• vultr-csi -> v0.16.0
• cni -> v1.7.1

• crictl -> v1.33.0
• runc -> v1.3.0
• containerd -> v1.7.25
• Add support for OIDC-based authentication
• Resolved Vultr CSI remount errors during pod/node migrations
v1.32.2+1 (2025-03-10)
• calico -> v3.29.2
• etcd -> v3.5.19
• vultr-ccm -> v0.14.0
• vultr-csi -> v0.14.0
• cni -> v1.6.2
• crictl -> v1.32.0
• runc -> v1.2.5
• containerd -> v1.7.25
1.32.1+1 (2025-01-21)
• Initial release of v1.32 support
VKE on 1.31.x
v1.31.8+1 (2025-05-14)
• calico -> v3.30.0
• etcd -> v3.5.21
• vultr-ccm -> v0.14.0
• vultr-csi -> v0.16.0
• cni -> v1.7.1
• crictl -> v1.33.0
• runc -> v1.3.0
• containerd -> v1.7.25
• Add support for OIDC-based authentication

• Resolved Vultr CSI remount errors during pod/node migrations
v1.31.10+1 (2025-03-10)
• calico -> v3.29.2
• etcd -> v3.5.19
• vultr-ccm -> v0.14.0
• vultr-csi -> v0.14.0
• cni -> v1.6.2
• crictl -> v1.32.0
• runc -> v1.2.5
• containerd -> v1.7.25
v1.31.5+1 (2025-01-21)
• calico -> v3.29.1
• etcd -> v3.5.17
• vultr-ccm -> v0.13.3
• vultr-csi -> v0.14.0
• cni -> v1.6.2
• crictl -> v1.32.0
• runc -> v1.2.4
• containerd -> v2.0.2
• Added VFS (Vultr File System) support
• Resolved intermittent loss of public IPv4 addresses on worker nodes
v1.31.2+1 (2024-11-13)
• calico -> v3.29.0
• etcd -> v3.5.16
• vultr-ccm -> v0.13.3
• vultr-csi -> v0.13.4
• cni -> v1.6.0
• crictl -> v1.31.1

• runc -> v1.2.1
• containerd -> v2.0.0
• Added support for GH200
• Enable Calico eBPF support, removing the need for kube-proxy
v1.31.0+1 (2024-08-20)
• Initial release of v1.31 support
VKE on v1.30.x
v1.30.12+1 (2025-05-14)
• calico -> v3.30.0
• etcd -> v3.5.21
• vultr-ccm -> v0.14.0
• vultr-csi -> v0.16.0
• cni -> v1.7.1
• crictl -> v1.33.0
• runc -> v1.3.0
• containerd -> v1.7.25
• Add support for OIDC-based authentication
• Resolved Vultr CSI remount errors during pod/node migrations
v1.30.10+1 (2025-03-10)
• calico -> v3.29.2
• etcd -> v3.5.19
• vultr-ccm -> v0.14.0
• vultr-csi -> v0.14.0
• cni -> v1.6.2
• crictl -> v1.32.0
• runc -> v1.2.5
• containerd -> v1.7.25

v1.30.9+1 (2025-01-21)
• calico -> v3.29.1
• etcd -> v3.5.17
• vultr-ccm -> v0.13.3
• vultr-csi -> v0.14.0
• cni -> v1.6.2
• crictl -> v1.32.0
• runc -> v1.2.4
• containerd -> v2.0.2
• Added VFS (Vultr File System) support
• Resolved intermittent loss of public IPv4 addresses on worker nodes
v1.30.6+1 (2024-11-13)
• calico -> v3.29.0
• etcd -> v3.5.16
• vultr-ccm -> v0.13.3
• vultr-csi -> v0.13.4
• cni -> v1.6.0
• crictl -> v1.31.1
• runc -> v1.2.1
• containerd -> v2.0.0
• Added support for GH200
• Enable Calico eBPF support, removing the need for kube-proxy
v1.30.3+1 (2024-08-20)
• calico -> v3.28.0
• etcd -> v3.5.15
• vultr-ccm -> v0.13.1
• vultr-csi -> v0.13.2
• cni -> v1.45.1

• crictl -> v1.30.1
• runc -> v1.1.13
• containerd -> v1.7.20
• Fixed hairpinning issues in the new CCM and resolved the problem of load
balancers being created multiple times
• Updated workers to use the new Nvidia packages
• Integrated the VCR auth plugin into workers, eliminating the need for
customers to add VCR credentials for repositories within the same account
• Allowed UDP traffic for workers in the firewall
v1.30.0+1 (2024-05-14)
• Initial release of v1.30 support
Archived Versions
VKE on v1.29.x
v1.29.10+1 (2024-11-13)
• calico -> v3.29.0
• etcd -> v3.5.16
• vultr-ccm -> v0.13.3
• vultr-csi -> v0.13.4
• cni -> v1.6.0
• crictl -> v1.31.1
• runc -> v1.2.1
• containerd -> v2.0.0
• Added support for GH200
• Enable Calico eBPF support, removing the need for kube-proxy

v1.29.7+1 (2024-08-20)
• calico -> v3.28.0
• etcd -> v3.5.15
• vultr-ccm -> v0.13.1
• vultr-csi -> v0.13.2
• cni -> v1.45.1
• crictl -> v1.30.1
• runc -> v1.1.13
• containerd -> v1.7.20
• Fixed hairpinning issues in the new CCM and resolved the issues of load
balancers being created multiple times
• Updated workers to use the new Nvidia packages
• Integrated the VCR auth plugin into workers, eliminating the need for
customers to add VCR credentials for repositories within the same account
• Allowed UDP traffic for workers in the firewall
v1.29.4+1 (2024-05-14)
• calico -> v3.27.3
• etcd -> v3.5.13
• vultr-ccm -> v0.12.0
• vultr-csi -> v0.12.4
• cni -> v1.4.0
• crictl -> v1.30.0
• runc -> v1.1.12
• containerd -> v1.7.15
• Add VKE Baremetal support
• Replace Kube-Proxy service with a DaemonSet
• Increase payload size to accommodate larger ETCD databases
• XFS Support
- Ensure the appropriate storage class is properly configured

v1.29.2+1 (2024-02-27)
• calico -> v3.27.2
• etcd -> v3.5.12
• vultr-csi -> v0.12.3
• containerd -> v1.7.13
• Switched VKE Worker OS: Moved from Debian 11 to Ubuntu 22.04 LTS
v1.29.1+1 (2024-01-30)
• Initial release of v1.29 support
VKE on v1.28.x
v1.28.12+1 (2024-08-20)
• calico -> v3.28.0
• etcd -> v3.5.15
• vultr-ccm -> v0.13.1
• vultr-csi -> v0.13.2
• cni -> v1.45.1
• crictl -> v1.30.1
• runc -> v1.1.13
• containerd -> v1.7.20
• Fixed hairpinning issues in the new CCM and resolved the issues of load
balancers being created multiple times
• Updated workers to use the new Nvidia packages
• Integrated the VCR auth plugin into workers, eliminating the need for
customers to add VCR credentials for repositories within the same account
• Allowed UDP traffic for workers in the firewall

v1.28.9+1 (2024-05-14)
• calico -> v3.27.3
• etcd -> v3.5.13
• vultr-ccm -> v0.12.0
• vultr-csi -> v0.12.4
• cni -> v1.4.0
• crictl -> v1.30.0
• runc -> v1.1.12
• containerd -> v1.7.15
• Add VKE Baremetal support
• Replace Kube-Proxy service with a DaemonSet
• Utilize GPU Operator for Nvidia package management instead of
preloading drivers on the machine.
• Increase payload size to accommodate larger ETCD databases
• XFS Support
- Ensure the appropriate storage class is properly configured
v1.28.7+1 (2024-02-27)
• calico -> v3.27.2
• etcd -> v3.5.12
• vultr-csi -> v0.12.3
• containerd -> v1.7.13
• Switched VKE Worker OS: Moved from Debian 11 to Ubuntu 22.04 LTS
v1.28.6+1 (2024-01-30)
• calico -> v3.27.0
• etcd -> v3.5.11
• vultr-ccm -> v0.11.0
• vultr-csi -> v0.12.0
• cni -> v1.4.0

• crictl -> v1.29.0
• runc -> v1.1.11
• containerd -> v1.7.12
• Resolve issue causing excessive resource usage on HA clusters with large
etcd db’s
• Upgrade VKE to kernel 6.X
v1.28.3+2 (2023-11-10)
• vultr-csi -> v0.10.1
• Resolve max CPU issue related to Nvidia packages due to unattended
upgrades
v1.28.3+1 (2023-11-06)
• calico -> v3.26.3
• etcd -> v3.5.10
• runc -> v1.1.9
• containerd -> v1.7.7
• High Availability (HA) control plane support
v1.28.2+1 (2023-09-25)
• Initial release of v1.28 support
VKE on v1.27.x
v1.27.11+1 (2024-02-27)
• calico -> v3.27.2
• etcd -> v3.5.12
• vultr-csi -> v0.12.3
• containerd -> v1.7.13

• Switched VKE Worker OS: Moved from Debian 11 to Ubuntu 22.04 LTS
v1.27.11-1 (2024-02-27)
• calico -> v3.27.2
• etcd -> v3.5.12
• vultr-csi -> v0.12.3
• containerd -> v1.7.13
• Switched VKE Worker OS: Moved from Debian 11 to Ubuntu 22.04 LTS
• BYO CNI Feature
• Arkenstone support
v1.27.10+1 (2024-01-30)
• calico -> v3.27.0
• etcd -> v3.5.11
• vultr-ccm -> v0.11.0
• vultr-csi -> v0.12.0
• cni -> v1.4.0
• crictl -> v1.29.0
• runc -> v1.1.11
• containerd -> v1.7.12
• Resolve issue causing excessive resource usage on HA clusters with large
etcd db’s
• Upgrade VKE to kernel 6.X
v1.27.7+2 (2023-11-10)
• vultr-csi -> v0.10.1
• Resolve max CPU issue related to Nvidia packages due to unattended
upgrades

v1.27.7+1 (2023-11-06)
• calico -> v3.26.3
• etcd -> v3.5.10
• runc -> v1.1.9
• containerd -> v1.7.7
• High Availability (HA) control plane support
v1.27.6+1 (2023-09-25)
• calico -> v3.26.1
• coredns -> v1.11.1
• konnectivity -> v0.0.37
• etcd -> v3.5.9
• vultr-ccm -> v0.10.0
• vultr-csi -> v0.9.0
• cni -> v1.3.0
• crictl -> v1.28.0
• runc -> v1.1.8
• containerd -> v1.7.6
• Implement hard-eviction thresholds on worker nodes
v1.27.2+1 (2023-06-23)
• Initial release of v1.27 support
VKE on v1.26.x
v1.26.10+2 (2023-11-10)
• vultr-csi -> v0.10.1

• Resolve max CPU issue related to Nvidia packages due to unattended
upgrades
v1.26.10+1 (2023-11-06)
• calico -> v3.26.3
• etcd -> v3.5.10
• runc -> v1.1.9
• containerd -> v1.7.7
• High Availability (HA) control plane support
v1.26.9+1 (2023-09-25)
• calico -> v3.26.1
• coredns -> v1.11.1
• konnectivity -> v0.0.37
• etcd -> v3.5.9
• vultr-ccm -> v0.10.0
• vultr-csi -> v0.9.0
• cni -> v1.3.0
• crictl -> v1.28.0
• runc -> v1.1.8
• containerd -> v1.7.6
• Implement hard-eviction thresholds on worker nodes
v1.26.5+1 (2023-06-23)
• calico -> v3.26.0
• coredns -> v1.10.1
• konnectivity -> v0.0.37
• etcd -> v3.5.9
• vultr-ccm -> v0.9.0
• vultr-csi -> v0.9.0
• cni -> v1.3.0

• crictl -> v1.27.0
• runc -> v1.1.7
• containerd -> v1.7.2
• VKE is now available in Sao Paulo
• VKE is now available in Tel Aviv
v1.26.2+2 (2023-03-22)
• Resolve issue with RFC 3849 IPv6 space by switching to ULA space
• Implement soft-eviction thresholds on worker nodes
- Memory available <=250Mi for 1 minute
v1.26.2+1 (2023-03-14)
• Initial release of v1.26 support
VKE on v1.25.x
v1.25.10+1 (2023-06-23)
• calico -> v3.26.0
• coredns -> v1.10.1
• konnectivity -> v0.0.37
• etcd -> v3.5.9
• vultr-ccm -> v0.9.0
• vultr-csi -> v0.9.0
• cni -> v1.3.0
• crictl -> v1.27.0
• runc -> v1.1.7
• containerd -> v1.7.2
• VKE is now available in Sao Paulo
• VKE is now available in Tel Aviv

v1.25.7+2 (2023-03-22)
• Resolve issue with RFC 3849 IPv6 space by switching to ULA space
• Implement soft-eviction thresholds on worker nodes
- Memory available <=250Mi for 1 minute
v1.25.7+1 (2023-03-14)
• Vultr CSI -> v0.9.0
- Block stats now available
- Block resizing introduced
• Vultr CCM -> v0.9.0
- Dual-Stack load-balancers implemented
• konnectivity -> v0.0.37
• Initial IPv6 Dual Stack support
- All worker nodes are now provisioned with a public IPv6 address
- Cluster networking setup to use IPv6 by default
• Konnectivity fixes implemented to resolve issues with sockets being
unavailable
• Added stricter memory and CPU accounting for resource management on
nodes
v1.25.6+1 (2023-01-25)
• calico -> v3.25.0
• coredns -> v1.10.0
• konnectivity -> v0.0.36
• etcd -> v3.5.7
• vultr-ccm -> v0.7.0
• vultr-csi -> v0.7.0
• cni -> v1.2.0
• crictl -> v1.26.0
• runc -> v1.1.4

• containerd -> v1.6.15
• Upgraded to Debian 11 for worker and controller nodes
• The kubelet and the container runtime are configured to use the systemd
cgroup driver
• Cluster-autoscaler bumped to version 1.26.1
v1.25.3+1 (2022-11-16)
• calico -> v3.24.5
• coredns -> v1.10.0
• konnectivity -> v0.0.33
• etcd -> v3.5.5
• vultr-ccm -> v0.7.0
• vultr-csi -> v0.7.0
• cni -> v1.1.1
• crictl -> v1.25.0
• runc -> v1.1.4
• containerd -> v1.6.9
• Fixed bug that affected the VKE labels on worker nodes
• Initial Release for v1.25 support
VKE on v1.24.x
v1.24.11+2 (2023-03-22)
• Resolve issue with RFC 3849 IPv6 space by switching to ULA space
• Implement soft-eviction thresholds on worker nodes
- Memory available <=250Mi for 1 minute
v1.24.11+1 (2023-03-14)
• Vultr CSI -> v0.9.0
- Block stats now available
- Block resizing introduced

• Vultr CCM -> v0.9.0
- Dual-Stack load-balancers implemented
• konnectivity -> v0.0.37
• Initial IPv6 Dual Stack support
- All workers nodes are now provisioned with a public IPv6 address
- Cluster networking setup to use IPv6 by default
• Konnectivity fixes implemented to resolve issues with socket being
unavailable
• Added stricter memory and CPU accounting for resource management on
nodes
v1.24.10+2 (2023-01-26)
• Fixed Cloud-init failing to complete bug causing VMs to not boot properly.
v1.24.10+1 (2023-01-25)
• calico -> v3.25.0
• coredns -> v1.10.0
• konnectivity -> v0.0.36
• etcd -> v3.5.7
• vultr-ccm -> v0.7.0
• vultr-csi -> v0.7.0
• cni -> v1.2.0
• crictl -> v1.26.0
• runc -> v1.1.4
• containerd -> v1.6.15
• Upgraded to Debian 11 for worker and controller nodes
• The kubelet and the container runtime are configured to use the systemd
cgroup driver
• Cluster-autoscaler bumped to version 1.26.1

v1.24.8+1 (2022-11-16)
• calico -> v3.24.5
• coredns -> v1.10.0
• konnectivity -> v0.0.33
• etcd -> v3.5.5
• vultr-ccm -> v0.7.0
• vultr-csi -> v0.7.0
• cni -> v1.1.1
• crictl -> v1.25.0
• runc -> v1.1.4
• containerd -> v1.6.9
v1.24.3+3 (2022-08-30)
• calico -> v3.23.1
• coredns -> v1.9.3
• konnectivity -> v0.0.32
• etcd -> v3.5.4
• vultr-ccm -> v0.6.0
• vultr-csi -> v0.7.0
• cni -> v1.1.1
• crictl -> v1.24.2
• runc -> v1.1.3
• containerd -> v1.6.6
• Adjusted support RBAC rules to check for PDB issues prior to initiating
upgrades
• Added resolv-conf flag to kubelet
v1.24.3+1 (2022-08-05)
• Initial release of v1.24 support

VKE on v1.23.x
v1.23.16+1 (2023-01-26)
• Fixed Cloud-init failing to complete bug causing VMs to not boot properly.
v1.23.16+1 (2023-01-25)
• calico -> v3.25.0
• coredns -> v1.10.0
• konnectivity -> v0.0.36
• etcd -> v3.5.7
• vultr-ccm -> v0.7.0
• vultr-csi -> v0.7.0
• cni -> v1.2.0
• crictl -> v1.26.0
• runc -> v1.1.4
• containerd -> v1.6.15
• Upgraded to Debian 11 for worker and controller nodes
• The kubelet and the container runtime are configured to use the systemd
cgroup driver
• Cluster-autoscaler bumped to version 1.26.1
v1.23.14+1 (2022-11-16)
• calico -> v3.24.5
• coredns -> v1.10.0
• konnectivity -> v0.0.33
• etcd -> v3.5.5
• vultr-ccm -> v0.7.0
• vultr-csi -> v0.7.0
• cni -> v1.1.1
• crictl -> v1.25.0

• runc -> v1.1.4
• containerd -> v1.6.9
• Fixed bug that affected the VKE labels on worker nodes
v1.23.10+1 (2022-09-26)
• calico -> v3.24.1
• coredns -> v1.10.0
• konnectivity -> v0.0.33
• etcd -> v3.5.5
• vultr-ccm -> v0.7.0
• vultr-csi -> v0.7.0
• cni -> v1.1.1
• crictl -> v1.25.0
• runc -> v1.1.4
• containerd -> v1.6.8
v1.23.9+1 (2022-08-30)
• calico -> v3.23.1
• coredns -> v1.9.3
• konnectivity -> v0.0.32
• etcd -> v3.5.4
• vultr-ccm -> v0.6.0
• vultr-csi -> v0.7.0
• cni -> v1.1.1
• crictl -> v1.24.2
• runc -> v1.1.3
• containerd -> v1.6.6
• Adjusted support RBAC rules to check for PDB issues prior to initiating
upgrades
• Added resolv-conf flag to kubelet

v1.23.7+1 (2022-06-13)
• Implemented autoscaler support
• calico -> v3.23.1
• coredns -> v1.9.2
• konnectivity -> v0.0.31
• etcd -> v3.5.4
• vultr-ccm -> v0.6.0
• vultr-csi -> v0.7.0
• Added Open-iSCSI support to worker nodes
• cni -> v1.1.1
• crictl -> v1.24.1
• runc -> v1.1.2
• containerd -> v1.6.4
• Implemented reserved limits on worker nodes to prevent resource
starvation to essential components
• Resolved DNS issues on control-plane nodes
v1.23.5+3 (2022-04-20)
• CSI updated to v0.6.0 to support new block storage types
• Updates to support more regions
v1.23.5+2 (2022-04-07)
• Added fix to disable swap memory on worker nodes
• Added crictl config to worker nodes
• Disabled resolvconf and set systemd-resolve as primary resolver
v1.23.5+1 (2022-03-23)
• Initial release of v1.23 support

VKE on v1.22.x
v1.22.13+1 (2022-09-26)
• calico -> v3.24.1
• coredns -> v1.10.0
• konnectivity -> v0.0.33
• etcd -> v3.5.5
• vultr-ccm -> v0.7.0
• vultr-csi -> v0.7.0
• cni -> v1.1.1
• crictl -> v1.25.0
• runc -> v1.1.4
• containerd -> v1.6.8
v1.22.12+1 (2022-08-30)
• calico -> v3.23.1
• coredns -> v1.9.3
• konnectivity -> v0.0.32
• etcd -> v3.5.4
• vultr-ccm -> v0.6.0
• vultr-csi -> v0.7.0
• cni -> v1.1.1
• crictl -> v1.24.2
• runc -> v1.1.3
• containerd -> v1.6.6
• Adjusted support RBAC rules to check for PDB issues prior to initiating
upgrades
• Added resolv-conf flag to kubelet

v1.22.10+1 (2022-06-13)
• Implemented autoscaler support
• calico -> v3.23.1
• coredns -> v1.9.2
• konnectivity -> v0.0.31
• etcd -> v3.5.4
• vultr-ccm -> v0.6.0
• vultr-csi -> v0.7.0
• Added Open-iSCSI support to worker nodes
• cni -> v1.1.1
• crictl -> v1.24.1
• runc -> v1.1.2
• containerd -> v1.6.4
• Implemented reserved limits on worker nodes to prevent resource
starvation to essential components
• Resolved DNS issues on control-plane nodes
v1.22.8+3 (2022-04-20)
• CSI updated to v0.6.0 to support new block storage types
• Updates to support more regions
v1.22.8+2 (2022-04-07)
• Added fix to disable swap memory on worker nodes
• Added crictl config to worker nodes
• Disabled resolvconf and set systemd-resolve as primary resolver
v1.22.8+1 (2022-03-23)
• Kubernetes components updated to v1.21.8 (CP + Worker nodes)

• Updated dependencies:
- containerd -> v1.6.1
- runc -> v1.1.0
- crictl -> v1.23.0
• Vultr CCM updated to v0.5.0
• Vultr CSI updated to v0.5.0
- csi-provisioner -> v3.1.0
- csi-attacher -> v3.4.0
- csi-node-driver-registrar -> v2.5.0
• Konnectivity updated to v0.0.30
v1.22.6+1 (2022-01-26)
• Initial release of v1.22 support
VKE on v1.21.x
v1.21.13+1 (2022-06-13)
• Implemented autoscaler support
• calico -> v3.23.1
• coredns -> v1.9.2
• konnectivity -> v0.0.31
• etcd -> v3.5.4
• vultr-ccm -> v0.6.0
• vultr-csi -> v0.7.0
• Added Open-iSCSI support to worker nodes
• cni -> v1.1.1
• crictl -> v1.24.1
• runc -> v1.1.2
• containerd -> v1.6.4
• Implemented reserved limits on worker nodes to prevent resource
starvation to essential components
• Resolved DNS issues on control-plane nodes

v1.21.11+3 (2022-04-20)
• CSI updated to v0.6.0 to support new block storage types
• Updates to support more regions
v1.21.11+2 (2022-04-07)
• Added fix to disable swap memory on worker nodes
• Added crictl config to worker nodes
• Disabled resolvconf and set systemd-resolve as primary resolver
v1.21.11+1 (2022-03-23)
• Kubernetes components updated to v1.21.11 (CP + Worker nodes)
• Updated dependencies:
- containerd -> v1.6.1
- runc -> v1.1.0
- crictl -> v1.23.0
• Vultr CCM updated to v0.5.0
• Vultr CSI updated to v0.5.0
- csi-provisioner -> v3.1.0
- csi-attacher -> v3.4.0
- csi-node-driver-registrar -> v2.5.0
• Konnectivity updated to v0.0.30
v1.21.9+1 (2022-01-26)
• Kubernetes components updated to v1.21.9 (CP + Worker nodes)
• Vultr CSI updated to v0.4.0

v1.21.7+2 (2022-01-11)
• Konnectivity updated to v0.0.27
• Improvements to the Kubernetes control plane for further stability and
security
v1.21.7+1 (2021-11-30)
• Kubernetes components updated to v1.21.7
• Vultr CCM updated to v0.4.0
- Fixes an issue with LB + SSL deploys
• CoreDNS bumped to v1.8.6
• Improvements to the Kubernetes control plane for further stability and
security
VKE on v1.20.x
v1.20.13+2 (2022-01-11)
• Konnectivity updated to v0.0.27
• Improvements to the Kubernetes control plane for further stability and
security
v1.20.13+1 (2021-11-30)
• Kubernetes components updated to v1.20.13
• Vultr CCM updated to v0.4.0
- Fixes an issue with LB + SSL deploys
• CoreDNS bumped to v1.8.6
• Improvements to the Kubernetes control plane for further stability and
security

v1.20.11+2 (2021-10-22)
• Improvements to the Kubernetes control plane for further stability and
security
v1.20.11+1 (2021-09-22)
• Konnectivity bumped to v0.0.24 (server + agent)
• Vultr CCM updated to v0.0.3
• Kubernetes components updated from v1.20.0 to v1.20.11
• Konnectivity and Kube API Server performance tuning
v1.20.0+1 (2021-08-19)
• Introduced Konnectivity Support: Provides a TCP-level proxy for control
plane to cluster communication
• Added Aggregation Layer Support: Extends Kubernetes with additional APIs
• Added NFS and CIFS support
• Added new storage class "WaitForFirstConsumer"
v1.20.0
• Initial release of v1.20 support

FAQ
A comprehensive resource addressing common questions about Vultr
Kubernetes Engine features, functionality, and management.

upgrades? 122
011 What are the security best practices for managing Vultr
Kubernetes Engine (VKE) cluster? 122
012 What is the default networking solution in Vultr Kubernetes
Engine (VKE) cluster? 122

013 What happens if I delete a worker node outside the Vultr
Kubernetes Engine (VKE) dashboard? 123

Frequently Asked Questions (FAQs)
About Vultr Kubernetes Engine
Introduction
These are the frequently asked questions for Vultr Kubernetes Engine (VKE).
What is Vultr Kubernetes Engine (VKE) and
how does it simplify Kubernetes
management?
Vultr Kubernetes Engine (VKE) is a fully managed Kubernetes service that
simplifies Kubernetes management by handling the control plane and worker
node management. It provides features such as automatic scaling, load
balancing, and integrated storage solutions. VKE allows users to focus on
deploying and scaling applications without needing to manage the underlying
Kubernetes infrastructure.
Can I attach an existing VPC to a new VKE
cluster?
Yes, you can attach an existing VPC to a new VKE cluster, but both the VPC and
the cluster must be in the same region. When creating a VKE cluster, you can
select an existing VPC from the VPC Network dropdown. If you do not select an
existing VPC, VKE will automatically provision a new VPC in the same location
by default.

How does Vultr Kubernetes Engine (VKE)
cluster handle scaling?
Vultr Kubernetes Engine (VKE) supports both manual and automatic scaling of
node pools. You can manually adjust the number of nodes in a pool or use the
autoscaler feature to automatically adjust the number of nodes based on
workload demands. The autoscaler maintains a specified range of nodes to
ensure your applications remain responsive during traffic spikes and cost-effective during low usage periods.
Can I run mixed workloads with different
compute types in the same Vultr Kubernetes
Engine (VKE) cluster?
Yes, Vultr Kubernetes Engine (VKE) allows you to create multiple Node Pools
within a single cluster, each with different compute types. This enables you to
run mixed workloads by selecting different Node Pool types (e.g., Regular Cloud
Compute, High Frequency, AMD/Intel High Performance) suited to your specific
workload requirements.
How does Vultr Kubernetes Engine (VKE)
cluster handle persistent data storage?
Vultr Kubernetes Engine (VKE) uses Vultr's Container Storage Interface (CSI) to
provide persistent block storage. You can choose between HDD and NVMe block
storage based on performance needs. Persistent Volume Claims (PVCs) are used
to allocate and manage storage for applications, ensuring data persistence
even if worker nodes are recreated.

What are the minimum requirements for
deploying a Vultr Kubernetes Engine (VKE)
cluster?
The minimum requirements include:
• At least one Node Pool with a minimum of one worker node.
• Worker nodes should have at least 2 GB of RAM.
• Basic network setup in the deployment location.
• Kubernetes version selection.
What is the minimum size for a block
storage volume in Vultr Kubernetes engine
(VKE)?
The minimum size for a block storage volume is:
• 10 GB for NVMe storage.
• 40 GB for HDD storage. These sizes are enforced by Vultr's CSI, and you
can specify the desired size when creating a Persistent Volume Claim
(PVC).
Does Vultr Kubernetes Engine (VKE) include
an ingress controller?
No, Vultr Kubernetes Engine (VKE) does not include a pre-configured ingress
controller. You will need to deploy an ingress controller such as Nginx, Traefik, or
HAProxy to manage external access to services in your cluster.

How does Vultr Kubernetes Engine (VKE)
cluster handle upgrades?
Vultr Kubernetes Engine (VKE) provides a dedicated Manage Upgrades tab for
controlling cluster upgrades. You can upgrade the Kubernetes version or apply
patches as new updates become available. Vultr handles the control plane
upgrades while you manage worker node upgrades. For smooth operation,
ensure that workloads can tolerate node restarts during upgrades.
What are the security best practices for
managing Vultr Kubernetes Engine (VKE)
cluster?
To enhance the security of Vultr Kubernetes Engine (VKE) cluster:
• Only use kubeconfig files from trusted sources, as maliciously crafted files
could compromise the cluster.
• Regularly audit Kubernetes Role-Based Access Control (RBAC) policies.
• Keep your Kubernetes version up to date using VKE's managed upgrades.
• Implement network policies to restrict unnecessary communication
between pods.
What is the default networking solution in
Vultr Kubernetes Engine (VKE) cluster?
Vultr Kubernetes Engine (VKE) uses the Calico Container Network Interface (CNI)
for networking. Calico provides a scalable networking solution with support for
advanced networking features like network policies, IP address management,
and high performance.

What happens if I delete a worker node
outside the Vultr Kubernetes Engine (VKE)
dashboard?
If you delete a worker node outside the Vultr Kubernetes Engine (VKE)
Dashboard, Vultr Kubernetes Engine (VKE) cluster will automatically redeploy
the node to maintain the node pool configuration and ensure cluster stability.
The system handles the replacement to keep your cluster’s desired state intact.