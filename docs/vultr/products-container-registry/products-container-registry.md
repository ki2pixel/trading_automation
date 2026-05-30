Container Registry
A managed container registry service for storing, managing, and
distributing container images within the Vultr ecosystem.

Provisioning
The process of setting up and configuring a new server or service to
make it ready for use.

How to Provision Vultr Container
Registry
Introduction
Vultr Container Registry is a managed storage and distribution system for Open
Container Initiative (OCI) images and related artifacts. This subscription allows
you to securely host multiple container images, enabling you to build and
deploy applications on platforms like Docker and Kubernetes. Vultr Container
Registry simplifies the management of containerized applications, providing a
reliable and scalable solution for your image storage needs.
Follow this guide to provision a Vultr Container Registry on your Vultr account
using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Container Registry.
2. Click Add Container Registry.
3. Provide a Registry Name.
4. Choose a Container Registry Location.
5. Pick a suitable Plan.
6. By default, the visibility is set to private. Select the checkbox to set the
visibility to public.
7. Click Add Container Registry.

Vultr API
1. Send a GET  request to the List Registry Regions endpoint and note your
target region name (e.g., ewr , sjp , blr ).
```bash
$ curl "https://api.vultr.com/v2/registry/region/list" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Registry Plans endpoint and note your
target plan key (e.g., start_up , business , premium , enterprise ).
```bash
$ curl "https://api.vultr.com/v2/registry/plan/list" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Create Container Registry endpoint to
create a registry with your target region and plan.
```bash
$ curl "https://api.vultr.com/v2/registry" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "name" : "{label}",
        "public" : false,
        "region" : "{region-name}",
        "plan" : "{plan-key}"
    }'
```
4. Send a GET  request to the List Container Registries endpoint to list all
the available registries.

```bash
$ curl "https://api.vultr.com/v2/registries" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all Vultr Container Registry regions and note your target region name
(e.g., ewr , sjp , blr ).
```bash
$ vultr-cli container-registry regions
```
2. List all Vultr Container Registry plans and note your target plan (e.g.,
, business , premium , enterprise ).
start_up
```bash
$ vultr-cli container-registry plans
```
3. Create a Vultr Container Registry with your target region and plan.
```bash
$ vultr-cli container-registry create --name "<label>" --
public false --region "<region-name>" --plan "<plan-key>"
```
4. List all the available Vultr Container Registry subscriptions.
```bash
$ vultr-cli container-registry list
```

Terraform
1. Ensure the Vultr Terraform provider is configured in your Terraform project.
2. Define the Container Registry resource in your Terraform configuration file.
```hcl
terraform {
required_providers {
vultr = {
source = "vultr/vultr"
version = "~> 2.27"
}
}
}
provider "vultr" {}
resource "vultr_container_registry" "registry" {
name = "container-registry"    # Registry name
region = "sjc"                   # Registry region (e.g.,
ewr, sjc, blr)
plan = "start_up"              # Plan key (start_up,
business, premium, enterprise)
public = false                   # Visibility
(false=private, true=public)
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Management
Manage your Vultr resources with tools for configuring, upgrading, and
removing instances.

Configurations
Settings that define how your Vultr resources are configured and operate
within your infrastructure.

Copy Registry Connection
Details
Instructions for retrieving and copying the connection details needed to
access your Vultr Container Registry

How to Retrieve Connection Details
for Vultr Container Registry
Introduction
Retrieving Connection Details for Vultr Container Registry provides essential
information, including endpoints and credentials, for seamless integration and
secure access. This allows you to effectively manage and deploy container
images across your applications. Vultr Container Registry ensures that you have
the necessary details to connect and work with your container registry
efficiently.
Follow this guide to retrieve the connection details of your container registry on
your Vultr account using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Container Registry.
2. Select your target registry to open its management page.
3. In the overview page, copy the registry connection details such as
Registry URL, Username and API Key.
Vultr API
1. Send a GET request to the List Container Registries endpoint and note
the target registry's ID.
```bash
$ curl "https://api.vultr.com/v2/registries" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Read Container Registry endpoint and note
the connection details for your target registry.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available registries in your Vultr account and note the target
registry's ID.
```bash
$ vultr-cli container-registry list
```
2. Get the target registry and note the connection details.
```bash
$ vultr-cli container-registry get <registry-id>
```
Terraform
1. Ensure the Vultr Terraform provider is configured in your Terraform project.
2. Define the Container Registry data source (filter by name), then apply.
```hcl
terraform {
required_providers {
vultr = {
source = "vultr/vultr"
version = "~> 2.27"
}
}
}
provider "vultr" {}
data "vultr_container_registry" "registry" {
filter {
name = "name"
values = ["container-registry"]
}
}
```
# Output the connection details
output "registry_name" {
value = data.vultr_container_registry.registry.name
}
output "registry_urn" {
value = data.vultr_container_registry.registry.urn
}
output "registry_date_created" {
value = data.vultr_container_registry.registry.date_created
}
output "registry_public" {
value = data.vultr_container_registry.registry.public
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 0 changed, 0 destroyed.
Outputs:
registry_date_created = "2025-01-01 10:00:00"
registry_name = "existingregistry"
registry_public = false
registry_urn = "sgp.vultrcr.com/existingregistry"

Generate Docker Config
A tool that creates a Docker configuration file for containerizing your
application on Vultr.

How to Generate Docker
Credentials for Vultr Container
Registry
Introduction
Generating Docker Credentials for Vultr Container Registry provides secure
access for pushing and pulling images. These credentials are essential for
authenticating and interacting with the container registry, ensuring seamless
integration with Docker and Kubernetes. For Kubernetes, these credentials
enable pods to authenticate and interact with the registry, facilitating the
deployment of containerized applications.
Follow this guide to generate Docker credentials for your container registry on
your Vultr account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products and click Container Registry.
2. Click your target registry to open its management page.
3. Click Docker/Kubernetes.
4. In the Docker Credentials section, provide a time duration for which the
docker credentials are valid.
1. Check the Push Access box to allow push privileges for these
particular credentials.
2. Click Generate Docker Config JSON to generate credentials in JSON
format.

5. In the Docker Credentials For Kubernetes section, provide a time
duration for which the credentials are valid.
1. Check the Push Access box to allow push privileges for these
particular credentials.
2. Click Generate Kubernetes YAML to generate a Kubernetes YAML
file.
Vultr API
1. Send a GET  request to the List Container Registries endpoint and note
the target registry's ID.
```bash
$ curl "https://api.vultr.com/v2/registries" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send an OPTIONS  request to the Create Docker Credentials endpoint and
note the generated credentials.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
docker-credentials?expiry_seconds=3600&read_write=true" \
-X OPTIONS \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send an OPTIONS  request to the Create Docker Credentials for
Kubernetes endpoint and note the generated YAML.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
docker-credentials/kubernetes?
expiry_seconds=3600&read_write=true&base64_encode=false" \

-X OPTIONS \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all the available registries in your Vultr account and note the target
registry's ID.
```bash
$ vultr-cli container-registry list
```
2. Generate Docker credentials for the target registry.
```bash
$ vultr-cli container-registry credentials docker <registry-id> --expiry-seconds 3600 --read-write true
```

Delete
Permanently removes the specified resource from your Vultr account.

How to Delete a Vultr Container
Registry
Introduction
Deleting a Vultr Container Registry removes all associated repositories and
images, helping to manage costs and simplify your infrastructure by eliminating
unused or redundant registries. This process ensures that you only retain the
resources you need, streamlining your container management.
Follow this guide to delete a container registry on your Vultr account using the
Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Container Registry.
2. Click your target registry to open its management page.
3. Click delete icon on the top-right of the management page.
4. Check the Yes, destroy this Container Registry box in the confirmation
prompt, and click Destroy Container Registry to permanently delete the
target registry.
Vultr API
1. Send a GET request to the List Container Registries endpoint and note
the target registry's ID.
```bash
$ curl "https://api.vultr.com/v2/registries" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete Container Registry endpoint to
delete the target registry.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all the available registries in your Vultr account and note the target
registry's ID.
```bash
$ vultr-cli container-registry list
```
2. Delete the target registry.
```bash
$ vultr-cli container-registry delete <registry-id>
```
Terraform
1. Open your Terraform configuration where the Container Registry is defined.
2. Remove the vultr_container_registry  resource block, or destroy it by target.
```hcl
resource "vultr_container_registry" "registry" {
name = "container-registry"
region = "sjc"
plan = "start_up"
public = false
}
```
# To delete, either remove this block from configuration
# or run: terraform destroy -target
vultr_container_registry.registry
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 0 changed, 1 destroyed.

Upgrade
Learn how to upgrade your Vultr server to a more powerful configuration
with additional resources.

How to Upgrade Vultr Container
Registry Plan
Introduction
Managing Your Vultr Container Registry Plan enhances your storage capacity,
access controls, and performance. By moving to a Premium, Business, or
Enterprise plan, you can better meet your growing needs and take advantage of
advanced features and improved capabilities. This upgrade ensures that your
container registry can scale effectively with your requirements.
Follow this guide to upgrade your Vultr Container Registry plan on your Vultr
account using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Container Registry.
2. Click your target registry to open its management page.
3. Click Settings to open its settings page.
4. Select a plan in the Upgrade Plan section.
5. Click Update to apply the change.
Vultr API
1. Send a GET request to the List Registry Plans endpoint and note the
target plan key.
```bash
$ curl "https://api.vultr.com/v2/registry/plan/list" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Container Registries endpoint and note
the target registry's ID.
```bash
$ curl "https://api.vultr.com/v2/registries" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PUT  request to the Update Container Registry endpoint to
upgrade the target registry plan.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "plan" : "{upgraded-plan-key}"
    }'
```
Vultr CLI
1. List all Vultr Container Registry plans and note the target plan.
```bash
$ vultr-cli container-registry plans
```
2. List all the available registries in your Vultr account and note the target
registry's ID.
```bash
$ vultr-cli container-registry list
```
3. Upgrade the plan of your target registry.
```bash
$ vultr-cli container-registry update <registry-id> --plan
"<upgraded-plan-key>"
```
Terraform
1. Open your Terraform configuration where the Container Registry is defined.
2. Update the plan  attribute in your Container Registry resource to upgrade
to your desired plan.
```hcl
terraform {
required_providers {
vultr = {
source = "vultr/vultr"
version = "~> 2.27"
}
}
}
provider "vultr" {}
resource "vultr_container_registry" "registry" {
name = "container-registry"
region = "sjc"
plan = "business"  # Updated from "start_up" to
"business"
public = false
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Visibility
Controls which users can view and access specific resources in your Vultr
account.

How to Manage the Visibility of
Vultr Container Registry
Introduction
Setting a Vultr Container Registry to Public allows broader access, making it
easier to share and deploy container images across multiple environments and
teams. By configuring your registry to be public, you facilitate wider distribution
and collaboration on your containerized applications.
Follow this guide to set your container registry visibility to public on your Vultr
account using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Container Registry.
2. Click your target registry to open its management page.
3. Click Settings to open its settings page.
4. In the Change Visibility section, check the Public box to set the visibility
to public, or uncheck the box to set it to private.
5. Click Update to apply the change.
Vultr API
1. Send a GET request to the List Container Registries endpoint and note
the target registry's ID.
```bash
$ curl "https://api.vultr.com/v2/registries" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Container Registry endpoint to
update the target registry visibility.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "public" : true
    }'
```
Vultr CLI
1. List all the available registries in your Vultr account and note the target
registry's ID.
```bash
$ vultr-cli container-registry list
```
2. Update the visibility of your target registry.
```bash
$ vultr-cli container-registry update <registry-id> --public
true
```
Terraform
1. Open your Terraform configuration where the Container Registry is defined.

2. Update the public  attribute in your Container Registry resource to change
the visibility.
```hcl
terraform {
required_providers {
vultr = {
source = "vultr/vultr"
version = "~> 2.27"
}
}
}
provider "vultr" {}
resource "vultr_container_registry" "registry" {
name = "container-registry"
region = "sjc"
plan = "start_up"
public = true  # true=public, false=private
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Repository
Manage and organize your software artifacts with Vultr's repository
system for efficient storage and retrieval.

Artifact
A centralized repository for storing and managing software packages,
container images, and other binary artifacts in your development
workflow.

Delete
Permanently removes the selected resource from your Vultr account.

How to Delete an Artifact from
Vultr Container Registry Repository
Introduction
Deleting an artifact from the Vultr Container Registry permanently removes a
specific version of a container image from a repository. This action helps
eliminate obsolete versions, ensuring that only relevant, up-to-date container
images remain in the repository.
Follow this guide to delete an artifact from the container registry repository on
your Vultr account using the Vultr API.
1. Send a GET  request to the List Container Registries endpoint and note
the target registry's ID.
```bash
$ curl "https://api.vultr.com/v2/registries" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Repositories endpoint to list all the
available repositories and note the target repository image.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
repositories" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a GET  request to the List Artifacts endpoint to list all the available
artifacts and note the target artifact's digest.

```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
repository/{repository-image}/artifacts" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
4. Send a DELETE request to the Delete Artifact endpoint to delete the target
artifact.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
repository/{repository-image}/artifact/{artifact-digest}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"

Retrieve
Retrieves information about a specific resource from the Vultr API.
```

How to Retrieve Artifact Details
from Vultr Container Registry
Repository
Introduction
An artifact refers to a specific version of a container image stored within a
repository in the Vultr Container Registry. It represents the packaged and
deployable unit of the image, containing metadata such as its digest, tags, and
associated push/pull times. By retrieving this data, you can gain insights into
the artifact's version, usage patterns, and storage, helping you manage and
optimize your container images more effectively.
Follow this guide to retrieve artifact details from the container registry
repository on your Vultr account using the Vultr API.
1. Send a GET  request to the List Container Registries endpoint and note
the target registry's ID.
```bash
$ curl "https://api.vultr.com/v2/registries" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Repositories endpoint to list all the
available repositories and note the target repository image.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
repositories" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a GET request to the List Artifacts endpoint to list all the available
artifacts and note the target artifact's digest.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
repository/{repository-image}/artifacts" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
4. Send a GET request to the Read Artifact endpoint to retrieve the target
artifact's details.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
repository/{repository-image}/artifact/{artifact-digest}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```

Delete
Permanently removes the selected resource from your Vultr account.

How to Delete a Repository from
Vultr Container Registry
Introduction
Deleting a Repository from the Vultr Container Registry frees up storage space
and removes outdated or unnecessary images. This process helps streamline
management and ensures that your registry contains only relevant and up-to-date resources. By keeping your repositories organized, you can maintain an
efficient and clutter-free container registry.
Follow this guide to delete a repository from your container registry on your
Vultr account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products and click Container Registry.
2. Click your target registry to open its management page.
3. Click Repositories to view all the available repositories.
4. Locate the target repository.
5. Click the delete icon to delete the target repository.
6. Check the Yes, destroy this Repository box in the confirmation prompt,
and click Destroy Repository to permanently delete the target
repository.

Vultr API
1. Send a GET  request to the List Container Registries endpoint and note
the target registry's ID.
```bash
$ curl "https://api.vultr.com/v2/registries" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Repositories endpoint to list all the
available repositories and note the target repository image.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
repositories" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a DELETE  request to the Delete Repository endpoint to delete the
target repository.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
repository/{repository-image}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all the available registries in your Vultr account and note the target
registry's ID.

```bash
$ vultr-cli container-registry list
```
2. List all the available repositories in your registry and note the target
repository image.
```bash
$ vultr-cli container-registry repository list <registry-id>
```
3. Delete the target repository.
```bash
$ vultr-cli container-registry repository delete <registry-id> --image-name <repository-image>

Retrieve
Retrieves information about a specific resource from the Vultr API.
```

How to Retrieve Repository Details
from Vultr Container Registry
Introduction
A repository in the Vultr Container Registry stores container images pushed via
OCI-compliant container engines like Docker or Podman. Each repository acts as
a logical storage unit, organizing images under unique names for streamlined
management and deployment. Retrieving repository details exposes metadata
such as the repository name, description, and pull count, providing visibility into
usage patterns and storage utilization.
Follow this guide to retrieve repository details from your container registry on
your Vultr account using the Vultr Console, API or CLI.
Vultr Console
1. Navigate to Products and click Container Registry.
2. Click your target registry to open its management page.
3. Click Repositories to view all the available repositories.
4. Locate the target repository and retrieve its details, including the
description, pull count, and artifact count.
Vultr API
1. Send a GET request to the List Container Registries endpoint and note
the target registry's ID.

```bash
$ curl "https://api.vultr.com/v2/registries" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Repositories endpoint to list all the
available repositories and note the target repository image.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
repositories" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a GET  request to the Read Repository endpoint to retrieve details of
the target repository.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
repository/{repository-image}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all the available registries in your Vultr account and note the target
registry's ID.
```bash
$ vultr-cli container-registry list
```
2. List all the available repositories in your registry and note the target
repository image.

```bash
$ vultr-cli container-registry repository list <registry-id>
```
3. Retrieve details of the target repository.
```bash
$ vultr-cli container-registry get <registry-id> --image-name "<repository-image>"
```

Update
Modify your servers configuration to adjust resources, change operating
systems, or enable features like backups and DDoS protection.

How to Update a Repository in
Vultr Container Registry
Introduction
Managing multiple repositories in the Vultr Container Registry with similar
names is easier when each has a clear, distinct description. Updating a
repository's description adds context to the stored container images, keeps the
details up to date, and improves discoverability within container workflows.
Follow this guide to update a repository's description in your container registry
on your Vultr account using the Vultr API or CLI.
Vultr API
1. Send a GET  request to the List Container Registries endpoint and note
the target registry's ID.
```bash
$ curl "https://api.vultr.com/v2/registries" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Repositories endpoint to list all the
available repositories and note the target repository image.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
repositories" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PUT  request to the Update Repository endpoint to update the
target repository's description.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
repository/{repository-image}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "description" : "{description}"
    }'
```
Vultr CLI
1. List all the available registries in your Vultr account and note the target
registry's ID.
```bash
$ vultr-cli container-registry list
```
2. List all the available repositories in your registry and note the target
repository image.
```bash
$ vultr-cli container-registry repository list <registry-id>
```
3. Update the target repository's description.
```bash
$ vultr-cli container-registry repository update <registry-id> --image-name "<repository-image>" --description
"<description>"

Robot
Manage and control Vultr's Robot API for automated infrastructure
management and operations.
```

Delete
Permanently removes the selected resource from your Vultr account.

How to Delete a Robot Account
from Vultr Container Registry
Introduction
Deleting a robot account from the Vultr Container Registry removes its access to
repositories, ensuring that outdated credentials do not remain active. This
improves security by minimizing exposure and reducing the risk of unauthorized
access. Removing unused robot accounts also streamlines container registry
management, keeping it clean and organized.
Follow this guide to delete a robot account from your container registry on your
Vultr account using the Vultr API.
1. Send a GET  request to the List Container Registries endpoint and note
the target registry's ID.
```bash
$ curl "https://api.vultr.com/v2/registries" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Robots endpoint to list all the available
robots and note the target robot's name.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
robots" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Note

Robot account names contain special characters like $ and + , which
must be URL-encoded before making API requests to prevent errors. You
can either manually replace $ with %24 and + with %2B in the endpoint
or export the robot name as a variable, avoiding the need for manual
encoding.
3. Send a DELETE request to the Delete Robot endpoint to delete the target
robot account.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
robot/{robot-name}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"

Retrieve
Retrieves information about a specific resource from your Vultr account.
```

How to Retrieve a Robot Account
Details from Vultr Container
Registry
Introduction
A robot account in the Vultr Container Registry is an automatically generated
account designed for automated interactions with repositories. These accounts
operate within a defined namespace and come with pre-configured permissions,
such as pulling images from repositories. They are commonly used in CI/CD
pipelines, automation scripts, and containerized deployments, ensuring secure,
non-interactive access without exposing user credentials.
Follow this guide to retrieve robot account details from your container registry
on your Vultr account using the Vultr API.
1. Send a GET  request to the List Container Registries endpoint and note
the target registry's ID.
```bash
$ curl "https://api.vultr.com/v2/registries" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Robots endpoint to list all the available
robots and note the target robot's name.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
robots" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Note
Robot account names contain special characters like $ and + , which
must be URL-encoded before making API requests to prevent errors. You
can either manually replace $ with %24 and + with %2B in the endpoint
or export the robot name as a variable, avoiding the need for manual
encoding.
3. Send a GET request to the Read Robot endpoint to retrieve the target
robot details.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
robot/{robot-name}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```

Update
Modify your servers configuration, resources, or settings to adapt to
changing requirements.

How to Update a Robot Account in
Vultr Container Registry
Introduction
A robot account in the Vultr Container Registry automates access control for
repositories. Updating a robot account lets you change its description, adjust its
expiration duration, manage permissions, and enable or disable access. This
ensures that the account stays aligned with security and operational needs,
eliminating the need to create a new robot account.
Follow this guide to update a robot account in your container registry on your
Vultr account using the Vultr API.
1. Send a GET  request to the List Container Registries endpoint and note
the target registry's ID and name.
```bash
$ curl "https://api.vultr.com/v2/registries" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Robots endpoint to list all the available
robots and note the target robot's name.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
robots" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"

[!Note] Robot account names contain special characters like $ and
+ , which must be URL-encoded before making API requests to
prevent errors. You can either manually replace $ with %24 and +
with %2B in the endpoint or export the robot name as a variable,
avoiding the need for manual encoding.
```
3. Send a PUT request to the Update Robot endpoint to update target robot
details.
```bash
$ curl "https://api.vultr.com/v2/registry/{registry-id}/
robot/{robot-name}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
"description" : "{description}",
"disable" : false,
"duration" : 3600,
"permissions": [
{
"kind": "{level}",
"namespace": "{registry-name}",
"access": [
{
"action": "{action-type}",
"resource": "{resource-type}",
"effect": "{allow-or-deny}"
}
]
}
]
}'

Docker Hub Proxy
A caching proxy service that speeds up Docker image pulls by storing
frequently used images locally on your Vultr infrastructure.
```

How to Access Container Images on
Docker Hub Using Vultr Container
Registry
Introduction
To help users avoid Docker Hub's rate limits on unauthenticated container
image pulls, Vultr provides a public proxy cache through Vultr Container
Registry (VCR). This allows users to pull Docker Hub container images via VCR
without facing rate restrictions. By leveraging VCR, you can ensure consistent
access to container images without unexpected failures due to rate limits.
Pulling an Image via VCR
All public container images on Docker Hub can be accessed through VCR by
prefixing the image URL with the appropriate VCR regional endpoint. This
method provides a seamless experience for containerized applications, ensuring
availability and reducing pull failures caused by Docker Hub restrictions.
Access a container image hosted on Docker Hub via VCR.
```console
$ docker pull {region}.vultrcr.com/docker.io/{account}/
{repository}
Below are some examples for pulling Docker Hub container images through
VCR.
• Container Image: alpine
Docker Hub
```

```console
$ docker pull alpine
VCR Docker Hub Proxy
```
```console
$ docker pull sjc.vultrcr.com/docker.io/alpine
• Container Image: tensorflow/tensorflow
Docker Hub
```
```console
$ docker pull tensorflow/tensorflow
VCR Docker Hub Proxy
```
```console
$ docker pull sjc.vultrcr.com/tensorflow/tensorflow
• Container Image: pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime
Docker Hub
```
```console
$ docker pull pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime
VCR Docker Hub Proxy
```
```console
$ docker pull sjc.vultrcr.com/pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime
```

The above examples use sjc.vultrcr.com as the prefix to proxy the requests
through the Silicon Valley region.
Choosing the Best Regional Endpoint
Use the regional VCR URL closest to your deployment to optimize network
performance and ensure reliable access to container images. This helps reduce
delays and potential throttling when pulling images from remote locations.
Additionally, using a geographically closer registry can significantly reduce
network congestion and improve deployment speed, making it ideal for high-performance workloads and large-scale containerized applications.
• Available VCR Regional Endpoints:
- New Jersey: ewr.vultrcr.com
- Singapore: sgp.vultrcr.com
- Silicon Valley: sjc.vultrcr.com
- Amsterdam: ams.vultrcr.com
- Bangalore: blr.vultrcr.com
- Chicago: ord.vultrcr.com
- Frankfurt: fra.vultrcr.com
- Los Angeles: lax.vultrcr.com
- London: lhr.vultrcr.com
- Tokyo: nrt.vultrcr.com
- Sydney: syd.vultrcr.com
- Seattle: sea.vultrcr.com
Additional Considerations
• Private Registries: If you need to store and pull private container
images, consider setting up authentication with Vultr Container Registry.
• Automated Deployments: You can integrate VCR with CI/CD pipelines to
ensure smooth automated deployments without interruptions due to
Docker Hub rate limits.

• Security Best Practices: Always verify image sources before deploying
them in production environments to maintain security and compliance.

FAQ
Frequently asked questions and answers about Vultr products, services,
and platform features.

registry using the API? 88
011 What is the default storage limit on the free plan? 88
012 Can I roll back to previous versions of a container image? 89
013 What are the available plans for Vultr container registry? 89
014 How do I manage repositories in a Vultr container registry?
89

Frequently Asked Questions (FAQs)
About Vultr Container Registry
Introduction
These are the frequently asked questions for Vultr Container Registry (VCR).
What is Vultr container registry and how
does it simplify container image
management?
Vultr Container Registry is a managed storage and distribution service for Open
Container Initiative (OCI) images. It simplifies container image management by
offering a secure, scalable platform where users can store, push, pull, and
manage container images. With built-in support for Docker and Kubernetes,
Vultr Container Registry integrates seamlessly into existing containerized
workflows, enabling easier image versioning, repository management, and
automated deployments without needing to manage the infrastructure behind
the registry.
What platforms are supported by Vultr
container registry?
Vultr Container Registry supports any platform that utilizes Open Container
Initiative (OCI) images, such as Docker, Kubernetes, and other container-based
environments.

How do I authenticate to Vultr container
registry from a docker client?
You can authenticate using Docker commands available in the Overview tab of
your registry in the Vultr Console. These commands include auto-generated
login commands, which will require your username and API key.
What happens if I exceed the storage limit
in my Vultr container registry?
If you exceed your registry storage limit, new container images cannot be
pushed to the registry until you either free up space by deleting images or
upgrade to a higher storage plan.
Can I share my container images with
others using Vultr container registry?
Yes, you can share your container images by making your registry public in the
Settings tab. This will allow anyone with the registry URL to pull your container
images without needing authentication.
How do I upgrade my Vultr container
registry plan?
You can upgrade your plan by navigating to the Settings tab in your Vultr
Container Registry dashboard. Select the desired plan from the Plans drop-down
menu and click Update to apply the changes.

How long does it take to create a Vultr
container registry?
It typically takes about 2 minutes for the Vultr Container Registry deployment
process to complete. Once the process is finished, the registry will be available
in your account.
Is my data encrypted in Vultr container
registry?
Yes, all data in Vultr Container Registry is encrypted both in transit and at rest,
ensuring the security of your container images and other artifacts.
Can I automate image management in Vultr
container registry using the API?
Yes, Vultr provides a full set of API endpoints to create, update, delete, and
manage container registries and repositories programmatically. This allows for
automation of tasks like pushing images or managing repositories.
What is the default storage limit on the free
plan?
The free Start Up plan provides up to 10 GB of storage. You can upgrade to a
higher plan if your storage needs exceed this limit.

Can I roll back to previous versions of a
container image?
Yes, you can roll back to previous versions of a container image by using the
specific tag for the version you want to pull. Tags can be managed in the
Repositories tab of your Vultr Container Registry.
What are the available plans for Vultr
container registry?
Vultr offers four plans for Container Registry, each with different storage limits:
• Start Up: Free, with 10 GB (10,240 MB) of storage.
• Business: $5/month, with 20 GB (20,480 MB) of storage.
• Premium: $10/month, with 50 GB (51,200 MB) of storage.
• Enterprise: $20/month, with 1 TB (1,048,576 MB) of storage.
How do I manage repositories in a Vultr
container registry?
You can manage repositories within a Vultr Container Registry by navigating to
the Repositories tab in your registry dashboard. This tab allows you to:
• View all repositories and their associated tags.
• Check repository statistics such as creation date and the last push date.
• Delete or update repositories as needed.
• Use the provided commands to pull, push, or tag images.
You can also manage repositories using the Vultr CLI or API for more advanced
automation.
