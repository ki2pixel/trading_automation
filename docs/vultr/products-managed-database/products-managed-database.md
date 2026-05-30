Managed Database
Fully managed database service that handles setup, maintenance, and
scaling of popular database engines so you can focus on your
applications.

MySQL
A comprehensive guide to setting up, managing, and troubleshooting
MySQL database servers on Vultr's platform.

Provisioning
A guide explaining how to set up and configure Vultr Managed Databases
for MySQL

How to Provision Vultr Managed
Databases for MySQL
Introduction
Vultr Managed Databases for MySQL is a highly available, scalable, and secure
relational database system that offers speed and reliability. You can integrate a
Vultr Managed Databases for MySQL cluster in modern applications and
programming languages such as Python, PHP, and Node.js, while choosing from
CPU-optimized, memory-optimized and general-purpose server types. In
addition, you can create database users, configure trusted sources, and
download SSL certificates to access the cluster and integrate it in existing
applications.
Follow this guide to provision Vultr Managed Databases for MySQL using the
Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Databases.
2. Click Add Managed Database.
3. Select MySQL as the database engine and note the MySQL version.
4. Select the Server Type drop-down and select your desired backend server
type.
5. Click Plan and select the server specifications.
6. Click the Number of Failover Replica Nodes drop-down and select the
number of failover replica nodes to add to your cluster.
7. Select your desired server location.
8. Optional: Click the VPC drop-down and select a VPC network to attach to
the cluster.
9. Enter a descriptive label in the Label field.
10. Review the selected plan and cost estimates.

11. Click Deploy Now to provision the Vultr Managed Databases for MySQL
cluster.
Vultr API
1. Send a GET  request to the List Regions endpoint and note your target
Vultr region ID.
```bash
$ curl "https://api.vultr.com/v2/regions" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Managed Database Plans endpoint to
view all available database engines and plans in your target Vultr region.
```bash
$ curl "https://api.vultr.com/v2/databases/plans?
region=<region-id>" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Create Database endpoint to provision a Vultr
Managed Databases for MySQL cluster, specifying your target server plan,
database engine, and Vultr region.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "database_engine" : "mysql",
        "database_engine_version" : "<version>",
        "plan" : "<server-plan>",
        "region" : "<region-id>",

        "label" : "<label>"
    }'
```
Visit the Create Database endpoint to view additional attributes to apply
on your Vultr Managed Databases for MySQL provisioning request.
4. Send a GET  request to the List Managed Databases endpoint to view all
Vultr Managed Databases for MySQL clusters in your account.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json"
```
Vultr CLI
1. List all Vultr regions and note your target region ID.
```bash
$ vultr-cli regions list
```
2. List all available Vultr Managed Databases plans and note your target plan.
```bash
$ vultr-cli database plan list
```
3. Provision a Vultr Managed Databases for MySQL cluster, specifying your
target plan, database engine version, and Vultr region.
```bash
$ vultr-cli database create \
--database-engine mysql \
--database-engine-version <version> \
--plan <server-plan> \

--region <region-id> \
--label <label>
```
Run vultr-cli database create --help  to view additional options to apply to
your Vultr Managed Databases for MySQL provisioning request.
4. List all Vultr Managed Databases clusters in your account.
```bash
$ vultr-cli database list --summarize
```
Terraform
1. Ensure the Vultr Terraform provider is configured in your Terraform project.
2. Define the Managed Database for MySQL in your Terraform configuration
file.
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
resource "vultr_database" "mysql" {
database_engine = "mysql"
database_engine_version = "8"
region = "ewr"  # e.g., ewr, ams, sgp
plan = "vultr-dbaas-startup-cc-1-55-2"
label = "mysql-cluster-1"
```
    # Optional
    # vpc_id       = "<vpc-id>"
    # trusted_ips  = ["192.0.2.1", "192.0.2.2"]

}
output "mysql_host" { value = vultr_database.mysql.host }
output "mysql_port" { value = vultr_database.mysql.port }
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Management
Tools and features for managing your Vultr resources, infrastructure, and
account settings.

Connection
Establish a secure connection to your Vultr resources for management
and data transfer.

Connection Details
How to view and manage connection credentials for accessing your Vultr
Managed MySQL databases

How to Manage Connection Details
for Vultr Managed Databases for
MySQL
Introduction
Managed database connection details consist of host, port, username,
password, default database, connection strings, and SSL certificates. These
credentials allow you to connect to the managed databases from your favorite
database client or modern programming language libraries. These include
MySQL command line client (mysql ), MySQL Connector/Python (mysql-connector-python ), Go MySQL Driver (go-sql-driver/mysql ), and PHP Data Objects (PDO ).
Follow this guide to manage connection details for Vultr Managed Databases for
MySQL using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Navigate to Connection Details under Overview.
4. Click Copy Connection String.
5. Click Copy MySQL URL.
6. Click Download Signed Certificate and save the certificate.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .

```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Get Managed Database endpoint and specify
a database ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Visit the Get Managed Database endpoint to view additional attributes
to add to your request.
3. Copy the host , port , user , password , dbname  values and use them to
connect to the database from your favorite client.
Vultr CLI
1. List all database instances and note the database ID. For instance,
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c .
```bash
$ vultr-cli database list --summarize
```
2. Retrieve connection details by specifying the database ID and copy the
credentials.
```bash
$ vultr-cli database get database_id
```
Run vultr-cli database get --help to view all options.
Terraform
1. If you manage the database with Terraform, you can output connection
details from the resource.
# Assuming a managed database resource exists
resource "vultr_database" "mysql" {
database_engine = "mysql"
database_engine_version = "8"
region = "ewr"
plan = "vultr-dbaas-startup-cc-1-55-2"
label = "mysql-cluster-1"
}
output "mysql_host" { value = vultr_database.mysql.host }
output "mysql_port" { value = vultr_database.mysql.port }
output "mysql_user" { value = vultr_database.mysql.user }
output "mysql_dbname" { value =
vultr_database.mysql.dbname }
# output "mysql_password" { value =
vultr_database.mysql.password  sensitive = true }
2. Apply the configuration and view the outputs with terraform output .

Trusted Sources
A security feature that restricts database access by allowing only
specified IP addresses to connect to your Vultr Managed MySQL database
instance.

How to Manage Trusted Sources for
Vultr Managed Databases for
MySQL
Introduction
Trusted sources allow you to restrict access to your managed databases by
specifying the list of IP addresses that can securely connect to the database
instance. This security mechanism reduces the risk of unauthorized access by
preventing DDoS and brute-force attacks. Trusted sources work on top of other
security measures like user access control.
Follow this guide to manage trusted sources for Vultr Managed Databases for
MySQL using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Navigate to Trusted Sources under Overview and click Edit.
4. Specify a list of the IP addresses of the servers that you want to allow to
connect to the database and click Save.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .

```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Managed Database endpoint to add
the IP addresses of the servers that you want to allow to connect to the
database in array format and specify the database ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "trusted_ips" :
["192.0.2.1","192.0.2.2","192.0.2.3"]
    }'
```
Visit the Update Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. Add the IP addresses of the servers that you want to allow to connect to
the database (For instance, 192.0.2.1,192.0.2.2,192.0.2.3 ) and specify the
database ID.

```bash
$ vultr-cli database update database_id \
--trusted-ips "192.0.2.1,192.0.2.2,192.0.2.3"
```
Run vultr-cli database update --help to view all options.
Terraform
1. Open your Terraform configuration for the existing Managed Database for
MySQL resource.
2. Add or update the trusted_ips  argument with the approved source IP
addresses.
```hcl
resource "vultr_database" "mysql" {
```
    # ...existing fields (database_engine, region, plan,
label, etc.)
trusted_ips = [
"192.0.2.1",
"192.0.2.2",
"192.0.2.3"
]
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

VPC Networks
A guide for setting up and managing Virtual Private Cloud networks to
secure communications with Vultr Managed MySQL Databases.

How to Manage VPC Networks for
Vultr Managed Databases for
MySQL
Introduction
Vultr Virtual Private Cloud (VPC) networks offer the flexibility of choosing your
own IP range and subnets to secure internal network communications.
Attaching a virtual isolated VPC network to a managed database allows you to
create hybrid connections that enforce traffic rules to your applications. VPCs
protect database resources from the public internet.
Follow this guide to manage Vultr VPC Networks for Vultr Managed Databases
for MySQL with Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Navigate to VPC Network under Overview.
4. Select a network from the list and click Update.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. List all the VPC networks by sending a GET  request to the List VPC
Networks endpoint and note the ID. For example, 778dd77c-a581-43a8-94e6-75b6ceb4354a .
```bash
$ curl "https://api.vultr.com/v2/vpcs" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PUT  request to the Update Managed Database endpoint to
attach the VPC network to the database by specifying the database ID and
the VPC network ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "vpc_id" : "vpc_network_id"
    }'
```
4. Detach a VPC network from the database by sending a PUT  request to the
Update Managed Database endpoint and specify a database ID and an
empty VPC ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "vpc_id" : "vpc_network_id"
    }'
```
Visit the Update Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. List all VPC networks and note the VPC ID. For instance, 778dd77c-a581-43a8-94e6-75b6ceb4354a .
```bash
$ vultr-cli vpc list
```
3. Attach the VPC network by specifying the database ID and the VPC ID.
```bash
$ vultr-cli database update database_id \
--vpc-id <vpc_id>
```
Run vultr-cli database update --help to view all options.
Terraform
1. Open your Terraform configuration for the existing Managed Database for
MySQL resource.
2. Attach a VPC by setting the vpc_id  argument. To detach, set vpc_id = null .

```hcl
resource "vultr_database" "mysql" {
```
    # ...existing fields (database_engine, region, plan,
label, etc.)
vpc_id = var.vpc_id  # e.g., "778dd77c-a581-43a8-94e6-75b6ceb4354a"
}
TERRAFORM
# Detach VPC
resource "vultr_database" "mysql" {
    # ...existing fields
vpc_id = null
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Settings
Configure account-wide preferences, security settings, and manage your
Vultr profile information.

Global SQL Modes
A guide explaining how to configure and manage global SQL mode
settings for Vultr Managed MySQL databases.

How to Manage Global SQL Modes
for Vultr Managed Databases for
MySQL
Introduction
SQL modes define the default data validation check that MySQL performs to
match the application requirement. For instance, the global NO_ZERO_DATE mode
instructs MySQL only to allow legal dates and restrict invalid values like
0000-00-00 . Each managed database can have its own set of SQL modes. Always
match the managed databases' SQL modes with the development servers.
Follow this guide to manage global SQL modes for Vultr Managed Database for
MySQL using Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Click Settings and select MySQL Configuration.
4. Then, navigate to Global SQL Modes. Add or remove any mode as
required
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID (For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 ) and the active SQL modes.

```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Managed Database endpoint and
specify the database ID to update the SQL modes.
```bash
$ curl "https://api.vultr.com/v2/databases/datase_id" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "mysql_sql_modes" : [
            "ANSI",
            "ERROR_FOR_DIVISION_BY_ZERO",
            "NO_ENGINE_SUBSTITUTION",
            "NO_ZERO_DATE",
            "NO_ZERO_IN_DATE",
            "STRICT_ALL_TABLES",
            "ONLY_FULL_GROUP_BY"
        ],
        "mysql_require_primary_key":true
    }'
```
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. Specify a database ID to add a new SQL mode to the database. For
instance, ONLY_FULL_GROUP_BY .

```bash
$ vultr-cli database update database_id \
--mysql-sql-modes
"ANSI,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,NO_ZE
RO_DATE,NO_ZERO_IN_DATE,STRICT_ALL_TABLES,ONLY_FULL_GROUP_BY"
\
--mysql-require-primary-key true
```
Terraform
1. Open your Terraform configuration for the existing Managed Database for
MySQL resource.
2. Add or update the mysql_sql_modes and mysql_require_primary_key arguments.
```hcl
resource "vultr_database" "mysql" {
```
# ...existing fields (database_engine, region, plan,
label, etc.)
mysql_sql_modes = [
"ANSI",
"ERROR_FOR_DIVISION_BY_ZERO",
"NO_ENGINE_SUBSTITUTION",
"NO_ZERO_DATE",
"NO_ZERO_IN_DATE",
"STRICT_ALL_TABLES",
"ONLY_FULL_GROUP_BY"
]
mysql_require_primary_key = true
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Slow Query Logging
A guide for configuring and managing slow query logging to identify
performance issues in Vultr Managed MySQL databases.

How to Manage Slow Query
Logging for Vultr Managed
Databases for MySQL
Introduction
Slow Query Logging instructs MySQL to store SQL statements that take long to
execute. The log allows you to identify and optimize such queries to improve
your application's performance. Optimizing queries reduces the CPU and
memory usage causing your database to run more efficiently. Running faster
queries also lead to a more responsive and enjoyable user experience.
Follow this guide to manage slow query logging for Vultr Managed Databases
for MySQL using Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Click Settings and select MySQL Configuration.
4. Then, navigate to Slow Query Logging.
5. Turn the feature to YES or NO and click Apply Changes.
6. If you turn the feature to YES specify a Long Query Time value in
seconds. The minimum value is 10 seconds.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID (For example,

43b4c774-5dff-4ac0-a01f-78a23c2205b5 ) and the active mysql_slow_query_log
status.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Managed Database endpoint and
specify the database ID to change the mysql_slow_query_log  status.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "mysql_slow_query_log": false
    }'
```
Vultr CLI
1. List all database instances and note the database ID. For instance,
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c .
```bash
$ vultr-cli database list --summarize
```
2. Run the following command and specify a database ID to update
 and mysql-long-query-time .
mysql-slow-query-log
```bash
$ vultr-cli database update database_id \
--mysql-slow-query-log true \
--mysql-long-query-time 20
```

Terraform
1. Open your Terraform configuration for the existing Managed Database for
MySQL resource.
2. Add or update the mysql_slow_query_log  and mysql_long_query_time  arguments.
```hcl
resource "vultr_database" "mysql" {
```
    # ...existing fields (database_engine, region, plan,
label, etc.)
mysql_slow_query_log = true
mysql_long_query_time = 20
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Database Users
A guide explaining how to create, modify, and manage user accounts for
Vultr Managed MySQL databases.

How to Manage Users for Vultr
Managed Databases for MySQL
Introduction
Database users are accounts that connect and query managed databases,
usually by specifying a username and a password. These accounts provide
access control and prevent unauthorized access to your database. After
creating a database user, you can define their privileges on the database level
to fine-tune the database security.
Follow this guide to manage database users for Vultr Managed Databases for
MySQL using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Navigate to Users & Databases and click Add New User.
4. Enter the username, select password encryption, define a strong password,
and click Create New User.
5. Click Delete User to remove the user from the database or click Reset
Password to change the user's password.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .

```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Create Database User endpoint specifying
the database ID and the user credentials (username , password , and
).
encryption
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/
users" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "username" : "john_doe",
        "password" : "example_password",
        "encryption" : "caching_sha2_password"
    }'
```
Visit the Create Database User endpoint to view additional attributes to
add to your request.
3. List the user details by sending a GET  request to the Get Database User
endpoint and specify the database ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/
users" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
4. Send a DELETE  request to the **Delete Database User* endpoint specifying
the database ID and the username  to delete a user.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/users/
username" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all database instances and note the database ID. For instance,
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c .
```bash
$ vultr-cli database list --summarize
```
2. Add a new user by specifying a database ID, username , password  and
encryption  method.
```bash
$ vultr-cli database user create database_id \
--username john_doe \
--password example_password \
--encryption caching_sha2_password
```
3. List all database users by specifying a database ID.
```bash
$ vultr-cli database user list database_id
```
4. Delete a user from the database by specifying a database ID and a
username .
```bash
$ vultr-cli database user delete database_id username
```
Run vultr-cli database user --help to view all options.

Terraform
1. Ensure the Vultr Terraform provider is configured.
2. Create a database user with Terraform.
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
```
# Existing database assumed
variable "database_id" { type = string }
resource "vultr_database_user" "john" {
database_id = var.database_id
username = "john_doe"
password = "example_password"
encryption = "caching_sha2_password"
}
3. To delete the user, remove the resource block or run:
```bash
$ terraform destroy -target vultr_database_user.john

Delete Databases
Learn how to permanently delete a Vultr Managed Database for MySQL
instance when its no longer needed.
```

How to Delete Vultr Managed
Databases for MySQL
Introduction
Deleting Vultr Managed Databases for MySQL removes the instance from your
account and stops further charges. Only perform this operation after backing up
the database because the operation deletes all logical databases, tables, and
objects associated with the managed database.
Follow this guide to delete Vultr Managed Databases for MySQL using the Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Click Settings and select Delete Managed Database.
4. Click Destroy Database Instance to remove the database.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete Managed Database endpoint and
specify the database ID to delete the database instance.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Visit the Delete Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c .
```bash
$ vultr-cli database list --summarize
```
2. Delete the database instance by specifying a database ID.
```bash
$ vultr-cli database delete database_id
```
Run vultr-cli database delete --help to view all options.
Terraform
1. Open your Terraform configuration and locate the Managed Database for
MySQL resource.
2. Remove the resource block or destroy it with Terraform.

```hcl
resource "vultr_database" "mysql" {
label = "mysql-cluster-1"
database_engine = "mysql"
database_engine_version = "8"
region = "ewr"
plan = "vultr-dbaas-startup-cc-1-55-2"
}
```
# To delete, either remove this block from configuration
# or run: terraform destroy -target vultr_database.mysql
3. Apply and observe the following output:
Apply complete! Resources: 0 added, 0 changed, 1 destroyed.

Logical Databases
A guide for creating and managing logical databases within your Vultr
Managed MySQL database instance.

How to Manage Logical Databases
for Vultr Managed Databases for
MySQL
Introduction
Logical databases provide a structured collection of data creating a workspace
for tables that in turn consist of columns and rows. A single database can store
dozens or even hundreds of tables. For instance, in an e-commerce website, a
database can store products , categories , sales , and payments tables.
Follow this guide to manage logical databases for Vultr Managed Databases for
MySQL using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Navigate to User and Databases and click Add New Database.
4. Enter the Database Name (For example, sample_company_db ) and click Add
Database.
5. Click Destroy Database to delete the database.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .

```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Create Logical Database endpoint specifying
the name of the logical database and the database ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/dbs" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "name" : "sample_company_db"
    }'
```
3. Send a GET  request to the List Logical Databases endpoint specifying
the database ID to list the logical databases.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/dbs" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
4. Send a DELETE  request to the Delete Logical Database endpoint
specifying the ID and the logical database name  to delete the logical
database.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/dbs/
logical_database_name" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Visit the Create Logical Database endpoint to view additional attributes
to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. Create a logical database by specifying the name (For example,
sample_company_db ) and the database ID.
```bash
$ vultr-cli database db create database_id --name
sample_company_db
```
3. List all logical databases by specifying a database ID.
```bash
$ vultr-cli database db list database_id
```
Run vultr-cli database db --help to view all options.
Terraform
1. Ensure the Vultr Terraform provider is configured.
2. Create a logical database with Terraform.
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
```
# Existing database assumed
variable "database_id" { type = string }
resource "vultr_database_db" "app" {
database_id = var.database_id
name = "sample_company_db"
}
3. To delete the logical database, remove the resource block or run:
```bash
$ terraform destroy -target vultr_database_db.app

Monitor Databases
Learn how to monitor Vultr Managed Databases for MySQL to track
resource usage, detect performance issues, and make informed scaling
decisions.
```

How to Monitor Vultr Managed
Databases for MySQL
Introduction
Monitoring Vultr Managed Databases for MySQL allows you to view the monthly
charges, vCPU, memory, disk, and network usage. Checking your managed
database stats provides insight that can help you scale your database, detect
performance issues, establish robust backup schedules, and more.
Follow this guide to monitor Vultr Managed Databases for MySQL using Vultr
Console, API, and CLI.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. View the database instance summary by clicking Overview.
4. Click Usage Graphs to view vCPU usage.
5. View the Disk Operations and Network.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Get Database Usage Information endpoint
and specify the database ID to retrieve the database instance usage
information. The information includes disk, memory, and vCPU usage.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/
usage" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Visit the Get Database Usage Information endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. List the database usage information by specifying a database ID.
```bash
$ vultr-cli database usage get database_id
```
Run vultr-cli database usage --help to view all options.

Resize Databases
Learn how to increase or decrease the resources allocated to your Vultr
Managed MySQL database.

How to Resize Vultr Managed
Databases for MySQL
Introduction
Resizing Vultr Managed Databases for MySQL allows you to scale your database
resources as your data grows. Scaling up is useful if your current database plan
can't handle your workload. Upsizing your managed database cluster adds more
CPUs, RAM, storage, and replica nodes to provide a better experience to your
end-users.
Follow this guide to resize Vultr Managed Databases for MySQL using Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Navigate to Settings and click Change Plan.
4. Review the active plan, select a new plan, set replica nodes, and click
Save.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Managed Database endpoint to
change the database plan and specify the database ID and the new plan
(For instance, vultr-dbaas-business-cc-1-55-2 ).
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "plan" : "vultr-dbaas-startup-cc-1-55-2"
    }'
```
Visit the Update Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. Update the database plan by specifying a database ID and a new plan (For
instance, vultr-dbaas-business-cc-1-55-2 ).
```bash
$ vultr-cli database update database_id \
--plan vultr-dbaas-business-cc-1-55-2
```
Run vultr-cli database update --help to view all options.
Terraform
1. Open your Terraform configuration and locate the Managed Database for
MySQL resource.
2. Update the plan argument with the new database plan ID.
```hcl
resource "vultr_database" "mysql" {
label = "mysql-cluster-1"
database_engine = "mysql"
database_engine_version = "8"
region = "ewr"
plan = "vultr-dbaas-business-cc-1-55-2" # Updated plan
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Upgrade Databases
Learn how to schedule and manage maintenance windows for your Vultr
Managed MySQL databases to minimize disruption to your applications.

How to Manage Upgrade Window
for Vultr Managed Databases for
MySQL
Introduction
Managing the Upgrade window for Vultr Managed Databases for MySQL allows
you to set a suitable day and time when your managed database upgrades to
the newest version. Upgrading improves security, fixes bugs, and downloads
new features. You should set the upgrade schedule when your database
application is less busy to avoid downtime for the end-users.
Follow this guide to manage the upgrade window for Vultr Managed Databases
for MySQL using Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Click Settings then Upgrade Window.
4. Select the day of the week and the time and click Apply Changes.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Managed Database endpoint to
change the maintenance day of the week (maintenance_dow ) and time
( maintenance_time ) for the database and specify the database ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "maintenance_dow" : "sunday",
        "maintenance_time" : "01:00"
    }'
```
Visit the Update Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. Update the maintenance day of the week and time by specifying the
database ID.
```bash
$ vultr-cli database update database_id \
--maintenance-dow sunday \
--maintenance-time 01:00
```
Run vultr-cli database update --help to view all options.
Terraform
1. Open your Terraform configuration for the existing Managed Database for
MySQL resource.
2. Add or update the maintenance_dow  and maintenance_time  arguments.
```hcl
resource "vultr_database" "mysql" {
```
    # ...existing fields (database_engine, region, plan,
label, etc.)
maintenance_dow = "sunday"
maintenance_time = "01:00"
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

FAQ
Answers to common questions about Vultr Managed Databases for MySQL
features, capabilities, and limitations.

CLI? 83
014 What versions of MySQL are available? 83
015 Can I set the SQL mode for MySQL? 83

016 What MySQL database properties can I configure? 84

Frequently Asked Questions (FAQs)
About Vultr Managed Databases
for MySQL
Introduction
These are the frequently asked questions for Vultr Managed Databases for
MySQL.
What MySQL storage engines are available?
Vultr Managed Databases for MySQL only supports the InnoDB storage engine.
What are Replica Nodes?
Replica nodes are copies of the primary node in a Vultr Managed Databases for
MySQL cluster. You can create replica nodes during provisioning, or click Add
Read Only Replica Node in the Actions section within the Overview tab in
your cluster's management page.
What type of Replica Nodes are attached to
a Vultr Managed Databases for MySQL
cluster?
The attached replica nodes are failover nodes used to ensure high availability
and recovery of your database cluster in case the primary node fails. Failover

replica nodes are read-only while the primary node performs the write
operations in your cluster to ensure data consistency across all replicas.
Can I create Replica Nodes in a Vultr
location that's different from my cluster
location?
Yes, you can create read-only replica nodes in other Vultr locations, different
from your Vultr Managed Databases for MySQL cluster location. Click Add
Read-Only Replica Node to create a new replica node and specify the target
Vultr location.
How many Replica Nodes can I attach to a
Vultr Managed Databases for MySQL
cluster?
You can attach up-to 3 replica nodes to a Vultr Managed Databases for MySQL
cluster.
How do I scale my database cluster?
Navigate to the Settings tab and click Change Plan on the left navigation
menu in your cluster's management page to scale your cluster up. You cannot
scale your cluster down, but you can migrate or fork it to a new, smaller cluster.

How do I create an admin (superuser) or
root-level account?
You cannot create superuser accounts for managed databases. You can only
create standard user accounts in your cluster. Navigate to the Users &
Databases tab to create a new user.
Can I use multiple primary (write) nodes?
A cluster can only have one primary node, but you can assign multiple replica
(read-only) nodes.
Do I need to use primary keys for my
tables?
Yes, you must use primary keys for all database tables, which is enforced
through the database configuration.
Is the database backed up?
Yes, Vultr Managed Databases for MySQL are automatically backed up. In
addition, all server plans other than Hobbyist offer user-initiated recovery,
forking, and point-in-time backups to restore a cluster incase of any failures.
Navigate to the Actions section within the Overview tab in your Vultr Managed
Databases for MySQL management page to fork a database cluster, and restore
data from backups.
Vultr Managed Databases for MySQL offer point-in-time recovery history, and
the duration available depends on your node plan.
• Premium: 30 days

• Business: 14 days
• Startup: 2 days
• Hobbyist: None
How do I find my node plan?
• You can deploy managed databases in several node plans, which are a
shorthand way of identifying the available size and number of nodes. We
offer Hobbyist, Startup, Business, and Premium node plans.
• After you deploy a managed database, look in the General Information
section of your cluster's information page. The Node Plan appears below
the Monthly Price. The plan name format is Vultr-Dbaas-[plan type]-[other
internal information] .
• The node plan determines what backup and recovery options are available.
Can I deploy managed databases with the
Vultr API or Vultr CLI?
Yes, you can use the Vultr API or Vultr CLI to provision a managed database for
MySQL.
What versions of MySQL are available?
Vultr's managed database clusters use the latest MySQL version.
Can I set the SQL mode for MySQL?
Yes. MySQL can operate in different SQL modes. You can apply these modes in
the database server's Settings tab through the Vultr Console. See the MySQL
documentation to learn more about SQL modes.

Notes about MySQL Modes:
• The ANSI (Combination Mode) SQL mode includes the following SQL
modes: REAL_AS_FLOAT, PIPES_AS_CONCAT, ANSI_QUOTES,
IGNORE_SPACE, and ONLY_FULL_GROUP_BY.
• You can toggle some modes individually, but if ANSI (Combination Mode) is
enabled, that setting will take precedence. For example, if you want to
disable ONLY_FULL_GROUP_BY, you will also need to disable ANSI
(Combination Mode) because it is a part of that mode bundle.
• According to the MySQL documentation, TRADITIONAL (Combination Mode)
includes the following SQL modes: STRICT_TRANS_TABLES,
STRICT_ALL_TABLES, NO_ZERO_IN_DATE, NO_ZERO_DATE,
ERROR_FOR_DIVISION_BY_ZERO, and NO_ENGINE_SUBSTITUTION.
• We do not support the NO_BACKSLASH_ESCAPES or
PAD_CHAR_TO_FULL_LENGTH SQL modes at this time.
Some features that you cannot set globally can be enabled per session. For
example, you cannot set binlog_row_value_options = partial_json globally, but you
can set it per session using the following command:
SQL
SET SESSION binlog_row_value_options = partial_json;
What MySQL database properties can I
configure?
You cannot change MySQL database properties or use the root user for cluster
stability. However, you can view the database properties with the SHOW VARIABLES;
SQL query.

PostgreSQL
A powerful, open-source relational database system available on Vultr
with provisioning, management options, and troubleshooting support.

Provisioning
A guide explaining how to set up and configure a new PostgreSQL
database instance in Vultrs Managed Database service.

How to Provision Vultr Managed
Databases for PostgreSQL
Introduction
Vultr Managed Databases for PostgreSQL is a highly available and scalable
relational database solution that supports modern features like vectors, JSON,
and geometric data types. PostgreSQL integrates with modern programming
languages like PHP, Python, and Go, making it an ideal choice for developing
web applications and application programming interfaces (APIs). PostgreSQL
databases are available in major global Vultr locations and you can choose from
CPU-optimized, memory-optimized, and general-purpose server types.
Follow this guide to provision Vultr Managed Databases for PostgreSQL using
the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Databases.
2. Click Add Managed Database.
3. Select PostgreSQL as the database engine.
4. Click the version drop-down and select your target PostgreSQL version.
5. Click the Server Type drop-down and select your desired server type.
6. Click the Plan drop-down and select the server specifications.
7. Click the Number of Failover Replica Nodes drop-down and select the
number of failover replica nodes to ensure high-availability incase the
primary node fails.
8. Select your target server location.
9. Optional: click the VPC drop-down and select a VPC network if available on
your account.
10. Enter a descriptive label in the Label field to identify your Vultr Managed
Databases for PostgreSQL.

11. Review the plan, and cost estimates summary.
12. Click Deploy Now to provision the Vultr Managed Databases for
PostgreSQL cluster.
Vultr API
1. Send a GET  request to the List Regions endpoint and note your target
Vultr region ID.
```bash
$ curl "https://api.vultr.com/v2/regions" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Managed Database Plans endpoint to
view all available database engines and plans in your target Vultr region.
```bash
$ curl "https://api.vultr.com/v2/databases/plans?
region=<region-id>" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Create Database endpoint to provision a Vultr
Managed Databases for PostgreSQL cluster with your database engine,
version, plan and target Vultr region.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "database_engine" : "pg",
        "database_engine_version" : "<version>",
        "plan" : "<server-plan>",
        "region" : "<region-id>",

        "label" : "<label>"
    }'
```
Visit the Create Database endpoint to view additional attributes to apply
to your request Vultr Managed Databases for PostgreSQL provisioning
request.
4. Send a GET  request to the List Managed Databases endpoint to list all
Vultr Managed Databases in your account.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json"
```
Vultr CLI
1. List all Vultr regions and note your target region ID.
```bash
$ vultr-cli regions list
```
2. List all available database plans and note your target plan.
```bash
$ vultr-cli database plan list
```
3. Provision a Vultr Managed Databases for PostgreSQL cluster with your
target plan and region.
```bash
$ vultr-cli database create \
--database-engine pg \
--database-engine-version <version> \

--plan <server-plan> \
--region <region-id> \
--label <label>
```
Run vultr-cli database create --help  to view all available options to apply to
your Vultr Managed Databases for PostgreSQL provisioning request.
4. List all Vultr Managed Databases in your account.
```bash
$ vultr-cli database list
```
Terraform
1. Ensure the Vultr Terraform provider is configured in your Terraform project.
2. Define the Managed Database for PostgreSQL in your Terraform
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
resource "vultr_database" "pg" {
database_engine = "pg"
database_engine_version = "16"
region = "ewr"  # e.g., ewr, ams, sgp
plan = "vultr-dbaas-startup-cc-1-55-2"
label = "pg-cluster-1"
```
    # Optional
    # vpc_id      = "<vpc-id>"

    # trusted_ips = ["192.0.2.1", "192.0.2.2"]
}
output "pg_host" { value = vultr_database.pg.host }
output "pg_port" { value = vultr_database.pg.port }
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Management
Tools and features for managing your Vultr infrastructure, including
access controls, monitoring, and resource administration.

Connection
Establish and manage connections to your Vultr resources through
various networking protocols and authentication methods.

Connection Details
How to find and use the connection credentials needed to access your
Vultr Managed PostgreSQL database

How to Retrieve Connection Details
for Vultr Managed Databases for
PostgreSQL
Introduction
Managed database connection details consist of host, port, username,
password, default database, connection strings, and SSL certificates. These
credentials allow you to connect to the managed databases from your favorite
database client or modern programming language libraries. These include the
terminal-based front-end to PostgreSQL (psql ), PostgreSQL adapter for Python
( Psycopg ), Go PostgreSQL driver (github.com/lib/pq ), and PostgreSQL Driver for
PHP ( pg_connect ).
Follow this guide to manage connection details for Vultr Managed Databases for
PostgreSQL using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Navigate to Connection Details under Overview.
4. Click Copy Connection String.
5. Click Copy PostgreSQL URL.
6. Click Download Signed Certificate and save the certificate.

Vultr API
1. List all the database instances by sending a GET  request to the List
Managed Databases endpoint and note the database ID. For example,
.
43b4c774-5dff-4ac0-a01f-78a23c2205b5
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Get Managed Database endpoint and specify
a database ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Visit the Get Managed Database endpoint to view additional attributes
to add to your request.
3. Copy the host , port , user , password , and dbname  values.
Vultr CLI
1. List all database instances and note the database ID. For instance,
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c .
```bash
$ vultr-cli database list --summarize
```
2. Retrieve connection details by specifying the database ID.

```bash
$ vultr-cli database get database_id
```
Run vultr-cli database get --help to view all options.
Terraform
1. If you manage the database with Terraform, you can output connection
details from the resource.
# Assuming a managed database resource exists
resource "vultr_database" "pg" {
database_engine = "pg"
database_engine_version = "16"
region = "ewr"
plan = "vultr-dbaas-startup-cc-1-55-2"
label = "pg-cluster-1"
}
output "pg_host" { value = vultr_database.pg.host }
output "pg_port" { value = vultr_database.pg.port }
output "pg_user" { value = vultr_database.pg.user }
output "pg_dbname" { value = vultr_database.pg.dbname }
# output "pg_password" { value = vultr_database.pg.password
sensitive = true }
2. Apply the configuration and view the outputs with terraform output .

Connection Pools
Learn how to create, configure, and manage connection pools to optimize
database performance for Vultr Managed PostgreSQL databases.

How to Manage Connection Pools
for Vultr Managed Databases for
PostgreSQL
Introduction
Connection pools provide a cache of reusable database connections to improve
database response time. The cache allows your PostgreSQL server to serve
many HTTP requests with fewer database connections. Connection pools reduce
latency by reducing the number of times the PostgreSQL server creates new
connections leading to better end-user experience.
Follow this guide to manage connection pools for Vultr Managed Databases for
PostgreSQL using the Vultr Console, API, and CLI.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target managed database instance.
3. Navigate to Connection Pools and click Add New Connection Pool.
4. Enter the details and click Create Pool.
5. Click Edit to change the connection pool details or Delete Pool to remove
the pool from the database.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .

```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Create Connection Pool endpoint to create a
connection pool and specify the database ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database-id/
connection-pools" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "name" : "sample-pool",
        "database" : "defaultdb",
        "username" : "vultradmin",
        "mode" : "transaction",
        "size" : 10
    }'
```
3. Send a GET  request to the List Connection Pools endpoint to list all the
connection pools.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/
connection-pools" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
4. Send a PUT  request to the Update Connection Pool endpoint and specify
the database ID and the pool name  to update.
```bash
$ curl "https://api.vultr.com/v2/databases/database-id/
connection-pools/pool-name" \

-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
"mode" : "session"
}'
```
5. Send a DELETE request to the Delete Connection Pool endpoint and
specify a database ID and a pool name to remove the pool from the
database.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/
connection-pools/pool_name" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"

Trusted Sources
Learn how to configure IP-based access restrictions for your Vultr
Managed PostgreSQL databases to enhance security.
```

How to Manage Trusted Sources for
Vultr Managed Databases for
PostgreSQL
Introduction
Trusted sources allow you to restrict access to your managed databases by
specifying the list of IP addresses that can securely connect to the database
instance. This security mechanism reduces the risk of unauthorized access by
preventing DDoS and brute-force attacks. Trusted sources work on top of other
security measures like user access control.
Follow this guide to manage trusted sources for Vultr Managed Databases for
PostgreSQL using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target managed database instance.
3. Navigate to Trusted Sources under Overview and click Edit.
4. Specify a list of the IP addresses of the servers that you want to allow to
connect to the database and click Save.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .

```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Managed Database endpoint to
define the IP addresses of the servers that you want to allow to connect to
the database in array format and specify the database ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "trusted_ips" :
["192.0.2.1","192.0.2.2","192.0.2.3"]
    }'
```
Visit the Update Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. Define the IP addresses of the servers that you want to allow to connect to
the database (For instance, 192.0.2.1,192.0.2.2,192.0.2.3 ) and specify the
database ID.

```bash
$ vultr-cli database update database_id \
--trusted-ips "192.0.2.1,192.0.2.2,192.0.2.3"
```
Run vultr-cli database update --help to view all options.
Terraform
1. Open your Terraform configuration for the existing Managed Database for
PostgreSQL resource.
2. Add or update the trusted_ips  argument with the approved source IP
addresses.
```hcl
resource "vultr_database" "pg" {
```
    # ...existing fields (database_engine, region, plan,
label, etc.)
trusted_ips = [
"192.0.2.1",
"192.0.2.2",
"192.0.2.3"
]
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

VPC Networks
A guide for setting up and managing Virtual Private Cloud networks to
secure internal communications for Vultr Managed PostgreSQL databases.

How to Manage VPC Networks for
Vultr Managed Databases for
PostgreSQL
Introduction
Vultr Virtual Private Cloud (VPC) networks offer the flexibility of choosing your
own IP range and subnets to secure internal network communications.
Attaching a virtual isolated VPC network to a managed database allows you to
create hybrid connections that enforce traffic rules to your applications. VPCs
protect database resources from the public internet.
Follow this guide to manage Vultr VPC Networks for Vultr Managed Databases
for PostgreSQL with Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Navigate to VPC Network under Overview.
4. Select a network from the list and click Update.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. List all the VPC networks by sending a GET  request to the List VPC
Networks endpoint and note the ID. For example, 778dd77c-a581-43a8-94e6-75b6ceb4354a .
```bash
$ curl "https://api.vultr.com/v2/vpcs" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PUT  request to the Update Managed Database endpoint to
attach the VPC network to the database by specifying the database ID and
the VPC network ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "vpc_id" : "vpc_network_id"
    }'
```
4. Detach a VPC network from the database by sending a PUT  request to the
Update Managed Database endpoint and specify a database ID and an
empty VPC ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "vpc_id" : "vpc_network_id"
    }'
```
Visit the Update Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. List all VPC networks and note the VPC ID. For instance, 778dd77c-a581-43a8-94e6-75b6ceb4354a .
```bash
$ vultr-cli vpc list
```
3. Attach the VPC network by specifying the database ID and the VPC ID.
```bash
$ vultr-cli database update database_id \
--vpc-id <vpc_id>
```
Run vultr-cli database update --help to view all options.
Terraform
1. Open your Terraform configuration for the existing Managed Database for
PostgreSQL resource.
2. Attach a VPC by setting the vpc_id  argument. To detach, set vpc_id = null .

```hcl
resource "vultr_database" "pg" {
```
    # ...existing fields (database_engine, region, plan,
label, etc.)
vpc_id = var.vpc_id  # e.g., "778dd77c-a581-43a8-94e6-75b6ceb4354a"
}
TERRAFORM
# Detach VPC
resource "vultr_database" "pg" {
    # ...existing fields
vpc_id = null
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Best Practices
Essential guidelines for establishing secure and efficient connections to
Vultr Managed PostgreSQL databases.

Best Practices on Connecting to
Vultr Managed Databases for
PostgreSQL
Introduction
Connecting to a Vultr Managed Databases for PostgreSQL becomes more
efficient when you use connection pools. A pool maintains a set of reusable
database connections, allowing applications to handle more requests without
repeatedly creating and closing new connections. With proper configuration,
connection pools improve performance, lower query response times, and ensure
resources are used effectively.
This guide explains best practices for configuring and managing connection
pools, including the importance of dedicated pools per server, the different pool
modes, and key configuration parameters.
Why Use Connection Pools
Every time an application opens a new PostgreSQL connection, the database
performs setup tasks such as authentication and resource allocation. These
operations introduce overhead and can significantly slow performance,
especially under heavy application load.
A connection pool avoids this overhead by keeping a group of connections open
and ready to use. When an application needs a connection, it borrows one from
the pool and returns it when finished. This reuse allows queries to run faster,
helps the system scale smoothly, and ensures resources are used efficiently.
• Improved Performance: Queries run faster because connections are
already established, reducing the time spent on setup.

• Resource Efficiency: The database uses fewer resources since
connections are reused instead of repeatedly opened and closed.
• Scalability: Applications can serve more users and handle higher traffic
without overwhelming the database.
• Simplified Management: The pool automatically handles connection
allocation and cleanup, reducing complexity in your application code.
Dedicated Pools Per Server
Each server or application instance that connects to your Vultr PostgreSQL
database should use its own dedicated connection pool. This approach provides:
• Isolation: Assigning a separate pool to each server prevents one server
from consuming most of the available connections. This ensures that other
servers and applications continue to run smoothly without unexpected
slowdowns.
• Predictability: With individual pools, you can size each one based on the
specific workload of its server. For example, a heavily used web server may
require a larger pool than a background worker.
• Scalability: Dedicated pools make it easier to tune connection limits as
you scale horizontally. Adding more application servers becomes
straightforward because each one brings its own pool instead of competing
for a shared pool.
• Fair Resource Allocation: When every server has its own pool,
connections are distributed evenly. This avoids contention and ensures that
all servers receive the database resources they need.
For example, if you run three application servers against the same database,
configure a separate pool for each. This setup keeps the environment stable,
predictable, and ready to grow.

Connection Pool Modes
When you create a connection pool, you must choose a mode that controls how
connections are allocated and reused. Each mode offers different trade-offs in
terms of performance, predictability, and flexibility:
• Session Mode (Recommended)
- Each client gets a dedicated connection for the duration of its session.
- Best for most applications since it balances efficiency with predictable
behavior.
- This mode works best for most use cases and is recommended if you
are unsure which option to select.
• Transaction Mode
- A connection is assigned only for the duration of a transaction.
- After the transaction completes, the connection is returned to the
pool.
- This mode fits workloads with many short-lived transactions that don't
rely on session state.
• Statement Mode
- In this mode, the pool assigns a connection for a single SQL statement
and immediately returns it after execution.
- This delivers the highest level of connection reuse but may break
multi-statement transactions or features that depend on session
variables.
- Use this mode only when handling simple, independent queries that
don't require session context.
Note
If you are unsure which mode to use, go with Session Mode. It provides the
most predictable behavior and works well for the majority of applications.

Pool Configuration Parameters
When creating a connection pool in the Vultr Console or via the API, you must
define several key parameters that control how the pool behaves:
• Pool Name: A unique identifier for the pool.
• Database: The logical database within your PostgreSQL instance that the
pool connects to.
• User: The database user associated with the pool.
• Pool Mode: Determines how connections are allocated (session ,
transaction , or statement ). Select the mode that best fits your application
workload.
• Size: The maximum number of active connections in the pool. Tune this
based on your application's concurrency requirements and server capacity.
For detailed, step-by-step instructions on creating a connection pool using the
Vultr Console or the Vultr API, refer to the Vultr PostgreSQL Connection Pools
Documentation.
Conclusion
You successfully learned how to optimize connections to your Vultr Managed
Databases for PostgreSQL using connection pools. By reusing connections, you
reduced overhead, improved query performance, and used resources more
efficiently. Dedicated pools per server kept workloads isolated, predictable, and
scalable. Selecting the right pool mode and tuning configuration parameters
ensured consistent and reliable performance.

Settings
Configure account-wide preferences, manage API keys, and control
security settings for your Vultr environment.

Configuration Options
Customize PostgreSQL database settings and parameters through the
Vultr control panel.

How to Manage Vultr Managed
Database for PostgreSQL
Configuration Options
Introduction
PostgreSQL configuration options allow you to fine-tune database settings that
affect performance, resource usage, security, logging, and more.
Follow this guide to manage Vultr Managed Database for PostgreSQL
configuration options with Vultr Console.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Navigate to Settings and click Advanced Configuration.
4. Select a configuration parameter, add a value, and click Submit.
5. Edit the configuration parameter value by clicking Edit.

Database Users
Learn how to create, modify, and manage user accounts for your Vultr
Managed PostgreSQL databases.

How to Manage Users for Vultr
Managed Databases for
PostgreSQL
Introduction
Database users are accounts that connect and query managed databases,
usually by specifying a username and a password. These accounts provide
access control and prevent unauthorized access to your database. After
creating a database user, you can define their privileges on the database level
to fine-tune the database security.
Follow this guide to manage database users for Vultr Managed Databases for
PostgreSQL using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Navigate to Users & Databases and click Add New User.
4. Enter the username, define a strong password, and click Create New
User.
5. Click Delete User to remove the user from the database or click Reset
Password to change the user's password.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .

```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Create Database User endpoint specifying
the database ID and the user credentials (username  and password ).
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/
users" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "username" : "john_doe",
        "password" : "example_password"
    }'
```
3. List the user details by sending a GET  request to the Get Database User
endpoint and specify the database ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/
users" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
4. Send a DELETE  request to the Delete Database User endpoint specifying
the database ID and the username  to delete a user.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/users/
username" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Visit the Delete Database User endpoint to view additional attributes to
add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. Add a new user by specifying a database ID and database credentials
( username and password ).
```bash
$ vultr-cli database user create database_id \
--username john_doe \
--password example_password
```
3. List all database users by specifying a database ID.
```bash
$ vultr-cli database user list database_id
```
4. Delete a user from the database by specifying a database ID and a
.
username
```bash
$ vultr-cli database user delete database_id username
```
Run vultr-cli database user --help to view all options.

Terraform
1. Ensure the Vultr Terraform provider is configured.
2. Create a database user with Terraform.
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
```
# Existing database assumed
variable "database_id" { type = string }
resource "vultr_database_user" "john" {
database_id = var.database_id
username = "john_doe"
password = "example_password"
}
3. To delete the user, remove the resource block or run:
```bash
$ terraform destroy -target vultr_database_user.john

Delete Databases
A guide explaining how to permanently delete PostgreSQL databases
from your Vultr Managed Database service.
```

How to Delete Vultr Managed
Databases for PostgreSQL
Introduction
Deleting Vultr Managed Databases for PostgreSQL removes the instance from
your account and stops further charges. Only perform this operation after
backing up the database because the operation deletes all logical databases,
tables, and objects associated with the managed database.
Follow this guide to delete Vultr Managed Databases for PostgreSQL using the
Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Click Settings and select Delete Managed Database.
4. Click Destroy Database Instance to remove the database.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete Managed Database endpoint and
specify the database ID to delete the instance.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Visit the Delete Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c .
```bash
$ vultr-cli database list --summarize
```
2. Delete the database by specifying a database ID.
```bash
$ vultr-cli database delete database_id
```
Run vultr-cli database delete --help to view all options.
Terraform
1. Open your Terraform configuration and locate the Managed Database for
PostgreSQL resource.
2. Remove the resource block or destroy it with Terraform.

```hcl
resource "vultr_database" "pg" {
label = "pg-cluster-1"
database_engine = "pg"
database_engine_version = "16"
region = "ewr"
plan = "vultr-dbaas-startup-cc-1-55-2"
}
```
# To delete, either remove this block from configuration
# or run: terraform destroy -target vultr_database.pg
3. Apply and observe the following output:
Apply complete! Resources: 0 added, 0 changed, 1 destroyed.

Logical Databases
A guide for creating and managing logical databases within your Vultr
Managed PostgreSQL database service.

How to Manage Logical Databases
for Vultr Managed Databases for
PostgreSQL
Introduction
Logical databases provide a structured collection of data creating a workspace
for tables that in turn consist of columns and rows. A single database can store
dozens or even hundreds of tables. For instance, in an e-commerce website, a
database can store products , categories , sales , and payments tables.
Follow this guide to manage logical databases for Vultr Managed Databases for
PostgreSQL using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Navigate to Users and Databases and click Add New Database.
4. Enter the Database Name (For example, sample_company_db ) and click Add
Database.
5. Click Destroy Database to delete the database.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .

```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Create Logical Database endpoint specifying
the name of the logical database and the database ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/dbs" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "name" : "sample_company_db"
    }'
```
Visit the Create Logical Database endpoint to view additional attributes
to add to your request.
3. Send a GET  request to the List Logical Databases endpoint specifying
the database ID to list the logical databases.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/dbs" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
4. Send a DELETE  request to the Delete Logical Database endpoint
specifying the ID and the logical database name  to delete the logical
database.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/dbs/
logical_database_name" \

-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all database instances and note the database ID. For instance,
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c .
```bash
$ vultr-cli database list --summarize
```
2. Create a logical database by specifying the database name (For example,
sample_company_db ) and the database ID.
```bash
$ vultr-cli database db create database_id --name
database_name
```
3. List all logical databases by specifying a database ID.
```bash
$ vultr-cli database db list database_id
```
Run vultr-cli database db --help to view all options.
Terraform
1. Ensure the Vultr Terraform provider is configured.
2. Create a logical database with Terraform.
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
```
# Existing database assumed
variable "database_id" { type = string }
resource "vultr_database_db" "app" {
database_id = var.database_id
name = "sample_company_db"
}
3. To delete the logical database, remove the resource block or run:
```bash
$ terraform destroy -target vultr_database_db.app

Monitor Databases
Learn how to monitor performance metrics and resource usage for your
Vultr Managed PostgreSQL databases.
```

How to Monitor Vultr Managed
Databases for PostgreSQL
Introduction
Monitoring Vultr Managed Databases for PostgreSQL allows you to view monthly
charges vCPU, memory, disk, and network usage. Checking your managed
database stats provides insight that can help you scale your database, detect
performance issues, establish robust backup schedules and more.
Follow this guide to monitor Vultr Managed Databases for PostgreSQL using
Vultr Console, API, and CLI.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. View the database instance summary.
4. Click Usage Graphs to view vCPU usage.
5. View the Disk Operations and Network.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Get Database Usage Information endpoint
and specify the database ID to retrieve the database instance usage
information. The information includes disk, memory, and vCPU usage.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/
usage" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Visit the Get Database Usage Information endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. List the database usage information by specifying a database ID.
```bash
$ vultr-cli database usage get database_id
```
Run vultr-cli database usage --help to view all options.

Resize Databases
Learn how to adjust the size and resources of your Vultr database
instances to meet changing performance needs.

How to Resize Vultr Managed
Databases for PostgreSQL
Introduction
Resizing Vultr Managed Databases for PostgreSQL allows you to scale your
database resources as your data grows. Scaling up is useful if your current
database plan can't handle your workload. Upsizing your managed database
cluster adds more CPUs, RAM, storage, and replica nodes to provide a better
experience to your end-users.
Follow this guide to resize Vultr Managed Databases for PostgreSQL using Vultr
Console, API, and CLI.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Navigate to Settings and click Change Plan. Review the active plan,
select a new plan, set replica nodes, and click Save.

Vultr API
1. List all the database instances by sending a GET  request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Managed Database endpoint to
change the database plan and specify the database ID and the new plan
(For instance, vultr-dbaas-business-cc-1-55-2 ).
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "plan" : "vultr-dbaas-business-cc-1-55-2"
    }'
```
Visit the Update Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. Update the database plan by specifying a database ID and a new plan (For
instance, vultr-dbaas-business-cc-1-55-2 ).
```bash
$ vultr-cli database update database_id \
--plan vultr-dbaas-business-cc-1-55-2
```
Run vultr-cli database update --help to view all options.

Upgrade Databases
Learn how to schedule and manage database version upgrades for your
Vultr Managed PostgreSQL databases.

How to Manage Upgrade Window
for Vultr Managed Databases for
PostgreSQL
Introduction
Managing the Upgrade window for Vultr Managed Databases for PostgreSQL
allows you to set a suitable day and time when your managed database
upgrades to the newest version. Upgrading improves security, fixes bugs, and
downloads new features. You should set the upgrade schedule when your
database application is less busy to avoid downtime for the end-users.
Follow this guide to manage upgrade window for Vultr Managed Databases for
PostgreSQL using Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Click Settings and Upgrade Window.
4. Select the day of the week and the time and click Apply Changes.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Managed Database endpoint to
change the maintenance day of the week (maintenance_dow ) and time
( maintenance_time ) for the database and specify the database ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "maintenance_dow" : "sunday",
        "maintenance_time" : "01:00"
    }'
```
Visit the Update Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. Update the maintenance day of the week and time by specifying the
database ID.
```bash
$ vultr-cli database update database_id \
--maintenance-dow sunday \
--maintenance-time 01:00
```
Run vultr-cli database update --help to view all options.
Terraform
1. Open your Terraform configuration for the existing Managed Database for
PostgreSQL resource.
2. Add or update the maintenance_dow  and maintenance_time  arguments.
```hcl
resource "vultr_database" "pg" {
```
    # ...existing fields (database_engine, region, plan,
label, etc.)
maintenance_dow = "sunday"
maintenance_time = "01:00"
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

PgBouncer
A connection pooling tool for PostgreSQL that improves performance by
managing and reusing database connections.

PgBouncer on Vultr Managed
Databases for PostgreSQL
Introduction
PgBouncer is a high-performance connection pooler for PostgreSQL that helps
optimize database connections, especially in high-traffic environments. It sits
between client applications and the PostgreSQL database, reducing the
overhead of creating and destroying connections by pooling them. This allows
multiple clients to share a smaller number of database connections,
significantly improving the efficiency of resource usage and reducing latency.
It supports different pooling modes, including session pooling, transaction
pooling, and statement pooling, each offering different trade-offs in terms of
connection reuse. It is lightweight and designed to have minimal memory and
CPU overhead, making it well-suited for systems where the number of client
connections to the database can vary significantly.
Different Modes of Pooling
• Session Pooling: A client connection is assigned a PostgreSQL backend
connection for the entire duration of the client session. Once the client
connects, the same backend connection is maintained for the entire
session, even if the client executes multiple queries. This method is ideal
for applications that maintain long-lived connections, where reusing a
connection for the entire session can improve performance.
• Transaction Pooling: Each database connection is assigned to a client
only for the duration of a single transaction. Once the transaction is
completed, the backend connection is returned to the pool and can be
reused by another client. This method is useful for applications that
perform many short-lived transactions, as it allows for maximum

connection reuse without the overhead of maintaining an open connection
for the entire session.
• Statement Pooling: Allows a client to borrow a backend connection only
for the duration of a single query (statement). After the statement is
executed, the backend connection is returned to the pool, and the client
can reuse a different connection for subsequent queries. This method
provides the highest level of connection reuse and is suitable for
applications with many lightweight queries that don't require maintaining
any session or transaction state.
PgBouncer With Vultr Managed Databases
for PostgreSQL
• Vultr Managed Databases for PostgreSQL comes with PgBouncer pre-enabled and configured, allowing users to easily create connection
pools to optimize database connections, extension-level configuration
for PgBouncer cannot be modified. This built-in connection pooling
functionality helps enhance performance by reducing the overhead of
creating and closing database connections, which is particularly beneficial
in environments with high query volumes.
• By default, 3 connections are reserved for management with any
subscription plan of Vultr Managed Databases for PostgreSQL. Each
subscription plan has a fixed upper limit on the number of
connections. For example, the base plan includes a total of 100
connections, with 3 reserved, leaving 97 available for client connections, in
situations where more number of connections are required the users have
to upgrade their subscription plan.
• When a request is sent to the default port of the database, it is handled
directly by PostgreSQL. However, if a request is directed to one of the
connection pool ports, it is routed through PgBouncer. To connect to
PostgreSQL via PgBouncer, users must utilize the port specified on the
connection pool page.

More Resources
• Provision Vultr Managed Databases for PostgreSQL.
• Manage Connection Pools for Vultr Managed Databases for PostgreSQL.
• Learn More About PgBouncer.

FAQ
Frequently asked questions and answers about Vultr Managed Databases
for PostgreSQL service features and functionality.

Frequently Asked Questions (FAQs)
About Vultr Managed Databases
for PostgreSQL
Introduction
These are the frequently asked questions for Vultr Managed Databases for
PostgreSQL.
Is the Vultr Managed Databases for
PostgreSQL cluster backed up?
Yes, Vultr Managed Databases for PostgreSQL are automatically backed up. In
addition, all server plans other than Hobbyist offer user-initiated recovery,
forking, and point-in-time backups to restore a cluster incase of any failures.
Navigate to the Actions section within the Overview tab in your Vultr Managed
Databases for PostgreSQL management page to fork a database cluster, and
restore data from backups.
Vultr Managed Databases for PostgreSQL offer point-in-time recovery history,
and the duration available depends on your node plan.
• Premium: 30 days
• Business: 14 days
• Startup: 2 days
• Hobbyist: None

What are Replica Nodes?
Replica nodes are copies of the primary node in a Vultr Managed Databases for
PostgreSQL cluster. You can create replica nodes during provisioning, or click
Add Read Only Replica Node in the Actions section within the Overview
tab in your cluster's management page.
What type of Replica Nodes are attached to
a Vultr Managed Databases for PostgreSQL
cluster?
The attached replica nodes are failover nodes used to ensure high availability
and recovery of your database cluster in case the primary node fails. Failover
replicas are read-only while the primary node performs the write operations in
your cluster to ensure data consistency across all replicas.
Can I create replica nodes in a Vultr location
that's different from my cluster location?
Yes, you can create read-only replica nodes in other Vultr locations, different
from your Vultr Managed Databases for PostgreSQL cluster location. Click Add
Read-Only Replica Node to create a new replica node and specify the target
Vultr location.

How many Replica Nodes can I attach to a
Vultr Managed Databases for PostgreSQL
cluster?
You can attach up to 3 replica nodes to a Vultr Managed Databases for
PostgreSQL cluster.
How can I find my node plan?
• Click Overview within your Vultr Managed Databases for PostgreSQL
cluster's management page
• Find the General Information section within the Overview tab of your
cluster's management page and note the Node Plan value. The Vultr
Managed Databases for PostgreSQL node plan uses a
Vultr-Dbaas-[plan type]-[other internal information] format. For example,
vultr-dbaas-premium-cc-1-55-2 .
Can I deploy managed databases using the
Vultr API or Vultr CLI?
Yes, you can deploy managed databases for PostgreSQL using the Vultr Console,
Vultr API, or Vultr CLI.
How do I scale my database cluster?
Navigate to the Settings tab and click Change Plan to upgrade your cluster.
Verify the Current Plan information, select your target plan, and click Save.

Can I create admin (superuser) or root-level
accounts?
You cannot create superuser accounts for managed databases. You can only
create standard user accounts in your cluster. Navigate to the Users &
Databases tab to create a new user.
Can I use multiple primary (write) nodes?
No, you can only use one primary node at a time. However, you can use
multiple replica-nodes in a cluster. A replica node may be elected incase the
primary node fails.
Do I need to use primary keys for my
tables?
Yes, you must use primary keys for all database tables, which is enforced
through the database configuration.
What PostgreSQL versions are available?
Vultr Managed Databases for PostgreSQL support multiple PostgreSQL versions
from 13 to the latest version.

How do I enable extensions for a PostgreSQL
database?
Connect to your Vultr Managed Databases cluster using psql  and follow the
steps below to enable extensions.
1. View the available extensions.
SQL
SELECT * FROM pg_available_extensions;
2. Enable a new extension.
SQL
CREATE EXTENSION extension_name;
3. Remove an extension.
SQL
DROP EXTENSION extension_name;

Valkey
A Redis-compatible, in-memory data structure store for caching,
messaging, and database applications on Vultr's platform.

Provisioning
A guide explaining how to set up and configure Vultr Managed Databases
for Valkey

How to Provision Vultr Managed
Databases for Valkey
Introduction
Vultr Managed Databases for Valkey is a highly-available Redis®-compatible in-memory database with flexible data structures. You can use the NoSQL
database as a cache, streaming engine, and message broker. You can provision
a CPU or memory-optimized database cluster around the globe in any Vultr
location. Vultr Managed Databases for Valkey support trusted sources and SSL
certificates for security.
Follow this guide to provision Vultr Managed Databases for Valkey using the
Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and click Databases.
2. Click Add Managed Database.
3. Choose Vultr Managed Database for Valkey as the database engine.
4. Select the Server Type and Plan.
5. Click the Number of Failover Replica Nodes drop-down and select the
number of failover replica nodes to provide automatic failover incase
the primary node fails, ensuring continuous service availability.
6. Choose a server location.
7. Select a VPC Network.
8. Enter a database label, review the monthly and hourly cost estimates, and
click Deploy Now.

Vultr API
1. Send a GET  request to the List Managed Database Plans endpoint to
view all available plans.
```bash
$ curl "https://api.vultr.com/v2/databases/plans" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Create Database endpoint to create a new
database instance.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "database_engine" : "valkey",
        "database_engine_version" : "7",
        "plan" : "vultr-dbaas-startup-occ-mo-2-26-16",
        "region" : "jnb",
        "label" : "Remote-Valkey-Db"
    }'
```
Visit the Create Database endpoint to view additional attributes to add to
your request.
3. Send a GET  request to the List Managed Databases endpoint to list all
database instances.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \

-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json"
```
Vultr CLI
1. List the available database plans.
```bash
$ vultr-cli database plan list
```
2. Create a new database instance.
```bash
$ vultr-cli database create \
--database-engine valkey \
--database-engine-version 7 \
--plan vultr-dbaas-startup-occ-mo-2-26-16 \
--region jnb \
--vpc-id 24ab6b57-845b-4354-a243-9bcafb4bd505 \
--label Remote-Valkey-Db
```
3. List all database instances.
```bash
$ vultr-cli database list --summarize
```
Run vultr-cli database create --help to view all options.
Terraform
1. Ensure the Vultr Terraform provider is configured in your Terraform project.
2. Define the Managed Database for Valkey (Redis-compatible) in your
Terraform configuration file.

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
resource "vultr_database" "valkey" {
database_engine = "valkey"
database_engine_version = "7"
region = "jnb"  # e.g., ewr, ams, sgp,
jnb
plan = "vultr-dbaas-startup-occ-mo-2-26-16"
label = "valkey-db-1"
```
    # Optional
    # vpc_id      = "<vpc-id>"
    # trusted_ips = ["192.0.2.1", "192.0.2.2"]
}
output "valkey_host" { value = vultr_database.valkey.host }
output "valkey_port" { value = vultr_database.valkey.port }
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Management
Tools and features for managing your Vultr infrastructure, including
access controls, monitoring, and resource administration.

Connection
Establish and manage connections to your Vultr resources for secure
access and data transfer.

Connection Details
Accessing and managing essential connection credentials needed to
connect to your Vultr Managed Database for Valkey instance

How to Manage Connection Details
for Vultr Managed Database for
Valkey
Introduction
Managed database connection details consist of host, port, username,
password, default database, connection strings, and SSL certificates. These
credentials allow you to connect to the managed databases from your favorite
database client or modern programming language libraries. These include
redis-cli , the Redis® command line interface, Redis® Python library (redis-py ),
Redis® Go client (go-redis), and Redis® client library for PHP (PhpRedis ).
Follow this guide to manage connection details for Vultr Managed Database for
Valkey using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Navigate to Connection Details under Overview.
4. Click Copy Connection String.
5. Click Copy URL.
6. Click Download Signed Certificate.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .

```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Get Managed Database endpoint and specify
a database ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Visit the Get Managed Database endpoint to view additional attributes
to add to your request.
3. Copy the host , port , user , and password values.
Vultr CLI
1. List all database instances and note the database ID. For instance,
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c .
```bash
$ vultr-cli database list --summarize
```
2. Retrieve connection details by specifying the database ID.
```bash
$ vultr-cli database get database_id
```
Run vultr-cli database get --help to view all options.

Terraform
1. If you manage the database with Terraform, you can output connection
details from the resource.
# Assuming a managed database resource exists
resource "vultr_database" "valkey" {
database_engine = "valkey"
database_engine_version = "7"
region = "jnb"
plan = "vultr-dbaas-startup-occ-mo-2-26-16"
label = "valkey-db-1"
}
output "valkey_host" { value = vultr_database.valkey.host }
output "valkey_port" { value = vultr_database.valkey.port }
output "valkey_user" { value = vultr_database.valkey.user }
# output "valkey_password" { value =
vultr_database.valkey.password  sensitive = true }
2. Apply the configuration and view the outputs with terraform output .

Trusted Sources
A security feature that restricts database access to specified IP addresses
to prevent unauthorized connections

How to Manage Trusted Sources for
Vultr Managed Database for Valkey
Introduction
Trusted sources allow you to restrict access to your managed databases by
specifying the list of IP addresses that can securely connect to the database
instance. This security mechanism reduces the risk of unauthorized access by
preventing DDoS and brute-force attacks. Trusted sources work on top of other
security measures like user access control.
Follow this guide to manage Trusted Sources for Vultr Managed Database for
Valkey using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Navigate to Trusted Sources under Overview and click Edit.
4. Add a list of the IP addresses of the servers that you want to allow to
connect to the database and click Save.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Managed Database endpoint, specify
the database ID and define the IP addresses of the servers that you want
to allow to connect to the database in array format.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "trusted_ips" :
["192.0.2.1","192.0.2.2","192.0.2.3"]
    }'
```
Visit the Update Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. Define the IP addresses of the servers that you want to allow to connect to
the database (For instance, 192.0.2.1,192.0.2.2,192.0.2.3 ) and specify the
database ID.
```bash
$ vultr-cli database update database_id \
--trusted-ips "192.0.2.1,192.0.2.2,192.0.2.3"
```
Run vultr-cli database update --help to view all options.
Terraform
1. Open your Terraform configuration for the existing Managed Database for
Valkey resource.
2. Add or update the trusted_ips  argument with the approved source IP
addresses.
```hcl
resource "vultr_database" "valkey" {
```
    # ...existing fields (database_engine, region, plan,
label, etc.)
trusted_ips = [
"192.0.2.1",
"192.0.2.2",
"192.0.2.3"
]
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

VPC Networks
A guide for creating and managing private network connections between
your Vultr Managed Database for Valkey and other resources using Virtual
Private Cloud (VPC) networks.

How to Manage VPC Networks for
Vultr Managed Database for Valkey
Introduction
Vultr Virtual Private Cloud (VPC) networks offer the flexibility of choosing your
own IP range and subnets to secure internal network communications.
Attaching a virtual isolated VPC network to a managed database allows you to
create hybrid connections that enforce traffic rules to your applications. VPCs
protect database resources from the public internet.
Follow this guide to manage Networks for Vultr Managed Database for Valkey
with Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Navigate to VPC Network under Overview.
4. Select a VPC network from the list and click Update.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. List all the VPC networks by sending a GET  request to the List VPC
networks endpoint and note the VPC ID. For example, 778dd77c-a581-43a8-94e6-75b6ceb4354a .
```bash
$ curl "https://api.vultr.com/v2/vpcs" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PUT  request to the Update Managed Database endpoint
endpoint to attach the VPC network to the database by specifying the
database ID and the VPC ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "vpc_id" : "vpc_network_id"
    }'
```
4. Detach a VPC network from the database by sending a PUT  request to the
Update Managed Database endpoint and specify a database ID and an
empty VPC ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "vpc_id" : ""
    }'
```
Visit the Update Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. List all VPC networks and note the VPC ID. For instance, 778dd77c-a581-43a8-94e6-75b6ceb4354a .
```bash
$ vultr-cli vpc list
```
3. Attach the VPC network by specifying the database ID and the VPC ID.
```bash
$ vultr-cli database update database_id \
--vpc-id <vpc_id>
```
Run vultr-cli database update --help to view all options.
Terraform
1. Open your Terraform configuration for the existing Managed Database for
Valkey resource.
2. Attach a VPC by setting the vpc_id  argument. To detach, set vpc_id = null .

```hcl
resource "vultr_database" "valkey" {
```
    # ...existing fields (database_engine, region, plan,
label, etc.)
vpc_id = var.vpc_id  # e.g., "778dd77c-a581-43a8-94e6-75b6ceb4354a"
}
TERRAFORM
# Detach VPC
resource "vultr_database" "valkey" {
    # ...existing fields
vpc_id = null
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Settings
Configure account-wide preferences, security settings, and manage API
access for your Vultr account.

Change Eviction Policy
Learn how to modify the eviction policy for your Vultr Managed Database
for Valkey to control memory usage and data persistence.

How to Manage Eviction Policy for
Vultr Managed Database for Valkey
Introduction
An eviction policy is an algorithm that determine the keys to remove when the
database reaches the maximum memory limit. By default, Vultr sets noeviction
eviction policy. Eviction aims to make room for new data and to prevent
unexpected behavior from your applications, always choose a large database
plan that can handle your data. Follow this guide to manage Vultr Managed
Database for Valkey eviction policy.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Navigate to Settings then Eviction Policies.
4. Choose your preferred eviction policy and click Save.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Managed Database endpoint
specifying the database ID to change the eviction policy.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "eviction_policy" : "volatile-lru"
    }'
```
Visit the Update Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. Install and configure the Vultr CLI.
2. List all database instances and note the database ID. For instance,
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c .
```bash
$ vultr-cli database list --summarize
```
3. Run the following command to change the eviction policy and specify the
database ID.
```bash
$ vultr-cli database update database_id \
--eviction-policy "volatile-lru"
```
Run vultr-cli database update --help to view all options.

Terraform
1. Open your Terraform configuration for the existing Managed Database for
Valkey resource.
2. Add or update the eviction_policy argument to set the data eviction policy.
```hcl
resource "vultr_database" "valkey" {
```
# ...existing fields (database_engine, region, plan,
label, etc.)
eviction_policy = "volatile-lru"
}
3. Apply and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Database Users
Learn how to create, modify, and manage user accounts for your Vultr
Managed Database for Valkey instance.

How to Manage Database Users for
Vultr Managed Database for Valkey
Introduction
Database users are accounts that connect and query managed databases,
usually by specifying a username and a password. These accounts provide
access control and prevent unauthorized access to your database. After
creating a database user, you can define their privileges on the database level
to fine-tune the database security.
Follow this guide to manage database users for Vultr Managed Databases for
Valkey using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Navigate to Users and click Add New User.
4. Enter the username, define a strong password, and click Create New
User.
5. Click Delete User to remove the user from the database or click Reset
Password to change the user's password.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .

```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the **Create Database User* endpoint specifying
the database ID and the user credentials (username  and password ).
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/
users" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "username" : "john_doe",
        "password" : "example_password"
    }'
```
Visit the Create Database User endpoint to view additional attributes to
add to your request.
3. List the user details by sending a GET  request to the Get Database User
endpoint and specify the database ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/
users" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
4. Send a DELETE  request to the Delete Database User endpoint specifying
the database ID and the username  to delete a user.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/users/
username" \

-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all database instances and note the database ID. For instance,
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c .
```bash
$ vultr-cli database list --summarize
```
2. Add a new user by specifying a database ID, username , and password .
```bash
$ vultr-cli database user create database_id \
--username john_doe \
--password example_password
```
3. List all database users by specifying a database ID.
```bash
$ vultr-cli database user list database_id
```
4. Delete a user from the database by specifying a database ID and a
.
username
```bash
$ vultr-cli database user delete database_id username
```
Run vultr-cli database user --help to view all options.

Terraform
1. Ensure the Vultr Terraform provider is configured.
2. Create a database user with Terraform.
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
```
# Existing database assumed
variable "database_id" { type = string }
resource "vultr_database_user" "john" {
database_id = var.database_id
username = "john_doe"
password = "example_password"
}
3. To delete the user, remove the resource block or run:
```bash
$ terraform destroy -target vultr_database_user.john

Delete Databases
Learn how to permanently delete a Vultr Managed Database for Valkey
instance and its data.
```

How to Delete Vultr Managed
Database for Valkey
Introduction
Deleting Vultr Managed Database for Valkey removes the instance from your
account and stops further charges. Only perform this operation after backing up
the database because the operation deletes all keys associated with the
managed databases.
Follow this guide to delete Vultr Managed Database for Valkey using the Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Click Settings and select Delete Managed Database.
4. Click Destroy Database Instance to remove the database.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete Managed Database endpoint and
specify the database ID to delete the database.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Visit the Delete Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c .
```bash
$ vultr-cli database list --summarize
```
2. Delete the database by specifying a database ID.
```bash
$ vultr-cli database delete database_id
```
Run vultr-cli database delete --help to view all options.
Terraform
1. Open your Terraform configuration and locate the Managed Database for
Valkey resource.
2. Remove the resource block or destroy it with Terraform.

```hcl
resource "vultr_database" "valkey" {
label = "valkey-db-1"
database_engine = "valkey"
database_engine_version = "7"
region = "jnb"
plan = "vultr-dbaas-startup-occ-mo-2-26-16"
}
```
# To delete, either remove this block from configuration
# or run: terraform destroy -target vultr_database.valkey
3. Apply and observe the following output:
Apply complete! Resources: 0 added, 0 changed, 1 destroyed.

Monitor Databases
Learn how to monitor your Vultr Managed Database for Valkey instance to
ensure optimal performance and availability.

How to Monitor Vultr Managed
Database for Valkey
Introduction
Monitoring Vultr Managed Database for Valkey allows you to view monthly
charges, vCPU, memory, and disk usage. Checking your managed database
stats provides insight that can help you scale your database, detect
performance issues, establish robust backup schedules, and more.
Follow this guide to monitor Vultr Managed Database for Valkey using Vultr
Console, API, and CLI.
Vultr Console
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. View the database instance summary.
4. Click Usage Graphs to view vCPU usage.
5. View the Network usage.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .

```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Get Database Usage Information endpoint
and specify the database ID to retrieve the database instance usage
information. The information includes disk, memory, and vCPU usage.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id/
usage" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Visit the Get Database Usage Information endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. List the database usage information by specifying a database ID.
```bash
$ vultr-cli database usage get database_id
```
Run vultr-cli database usage --help to view all options.

Resize Databases
A guide explaining how to increase or decrease the resources allocated to
your Vultr Managed Database instances

How to Resize Vultr Managed
Databases for Caching
Introduction
Resizing Vultr Managed Databases for Caching allows you to scale your
database resources as your data grows. Scaling a database up is useful if your
current plan can't handle your workload. Upsizing your managed database
cluster also adds more CPUs, RAM, storage, and replica nodes to provide a
better experience to your end-users.
Follow this guide to resize Vultr Managed Databases for Caching using Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Navigate to Settings and click Change Plan.
4. Review the active plan, select a new plan, set replica nodes, and click
Save.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Managed Database endpoint to
change the database plan and specify the database ID and the new plan
(For instance, vultr-dbaas-business-occ-mo-2-26-16 ).
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "plan" : "vultr-dbaas-business-occ-mo-2-26-16"
    }'
```
Visit the Update Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. Update the database plan by specifying a database ID and a new plan (For
instance, vultr-dbaas-business-occ-mo-2-26-16 ).
```bash
$ vultr-cli database update database_id \
--plan vultr-dbaas-business-occ-mo-2-26-16
```
Run vultr-cli database update --help to view all options.
Terraform
1. Open your Terraform configuration and locate the Managed Database for
Valkey resource.
2. Update the plan argument with the new database plan ID.
```hcl
resource "vultr_database" "valkey" {
label = "valkey-db-1"
database_engine = "valkey"
database_engine_version = "7"
region = "jnb"
plan = "vultr-dbaas-business-occ-mo-2-26-16" # Updated plan
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Upgrade Databases
Learn how to schedule and manage database version upgrades for your
Vultr Managed Database for Valkey instances.

How to Manage Upgrade Window
for Vultr Managed Database for
Valkey
Introduction
Managing the Upgrade window for Vultr Managed Database for Valkey allows
you to set a suitable day and time when your managed database upgrades to
the newest version. Upgrading improves security, fixes bugs, and downloads
new features. You should set the upgrade schedule when your database
application is less busy to avoid downtime for the end-users.
Follow this guide to manage the upgrade window for Vultr Managed Database
for Valkey using Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click the target database instance.
3. Click Settings then Upgrade Window.
4. Select the day of the week and the time and click Apply Changes.
Vultr API
1. List all the database instances by sending a GET request to the List
Managed Databases endpoint and note the database ID. For example,
43b4c774-5dff-4ac0-a01f-78a23c2205b5 .
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Managed Database endpoint to
change the maintenance day of the week (maintenance_dow ) and time
( maintenance_time ) for the database and specify the database ID.
```bash
$ curl "https://api.vultr.com/v2/databases/database_id" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "maintenance_dow" : "sunday",
        "maintenance_time" : "01:00"
    }'
```
Visit the Update Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. Update the maintenance day of the week and time by specifying the
database ID.
```bash
$ vultr-cli database update database_id \
--maintenance-dow sunday \
--maintenance-time 01:00
```
Run vultr-cli database update --help to view all options.
Terraform
1. Open your Terraform configuration for the existing Managed Database for
Valkey resource.
2. Add or update the maintenance_dow  and maintenance_time  arguments.
```hcl
resource "vultr_database" "valkey" {
```
    # ...existing fields (database_engine, region, plan,
label, etc.)
maintenance_dow = "sunday"
maintenance_time = "01:00"
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

FAQ
Frequently asked questions and answers about Vultrs Managed
Databases for Valkey caching service.

82
011 Can I use multiple primary (write) nodes? 82
012 How is memory allocated for a Vultr Managed Databases for
Caching? 238
013 Why is memory limited for Vultr Managed Databases for
Caching? 238

Frequently Asked Questions (FAQs)
About Vultr Managed Databases
for Valkey
Introduction
These are the frequently asked questions for Vultr Managed Databases for
Caching.
Is the database backed up?
• Yes, all Managed Databases are backed up for disaster recovery purposes.
You can use these backups to restore a cluster, which overwrites the
current cluster's data. You can also fork a cluster from the backup, which
creates a new cluster without modifying the existing cluster. You'll find
those options in the Actions section of your cluster's Overview tab.
• The databases do not have point-in-time recovery. When recovering or
forking a Vultr Managed Database for Caching, you can choose from a list
of periodic backups.
What are Replica Nodes?
Replica nodes are copies of the primary node in a Vultr Managed Databases for
Valkey cluster. You can create replica nodes during provisioning, or click Add
Read Only Replica Node in the Actions section within the Overview tab in
your cluster's management page.

What type of Replica Nodes are attached to
a Vultr Managed Databases for Valkey
cluster?
The attached replica nodes are failover nodes used to ensure high availability
and recovery of your database cluster in case the primary node fails. Failover
replicas are read-only while the primary node performs the write operations in
your cluster to ensure data consistency across all replicas.
Can I create replica nodes in a Vultr location
that's different from my cluster location?
Yes, you can create read-only replica nodes in other Vultr locations, different
from your Vultr Managed Databases for Valkey cluster location. Click Add
Read-Only Replica Node to create a new replica node and specify the target
Vultr location.
How many Replica Nodes can I attach to a
Vultr Managed Databases for Valkey cluster?
You can attach up-to 3 replica nodes to a Vultr Managed Databases for Valkey
cluster.
How do I find my node plan?
• You can deploy Managed Databases in several node plans, which are a
shorthand way of identifying the available size and number of nodes. We
offer Hobbyist, Startup, Business, and Premium node plans.

• After you deploy a Managed Database, look in the General Information
section of your cluster's information page. The Node Plan appears below
the Monthly Price. The plan name format is Vultr-Dbaas-[plan type]-[other
internal information] .
• The node plan determines what backup and recovery options are available.
See the previous section, "Is the database backed up?" for details.
Can I deploy managed databases with the
Vultr API or Vultr CLI?
Yes, you can deploy Vultr Managed Databases for Caching using the Vultr API or
Vultr CLI.
How do I scale my database cluster?
Use the Change Plan menu on the Settings tab to scale your cluster up. To
scale a cluster down, migrate or fork it to a new, smaller cluster.
How do I create an admin (superuser) or
root-level account?
You cannot create superuser accounts for managed databases. To create a
standard user account, use the Vultr Console.
Can I use multiple primary (write) nodes?
A cluster can only have one primary node, but you can configure multiple
replica (read-only) nodes.

How is memory allocated for a Vultr
Managed Databases for Caching?
Maximum memory for Vultr Managed Databases for Caching is set to 70% of the
available RAM (minus management overhead) plus 10% for the replication log.
Why is memory limited for Vultr Managed
Databases for Caching?
We reserve memory because the following situations can happen:
• When a new Vultr Managed Databases for Caching node connects to the
existing master, the master forks a copy of itself and sends current
memory contents to the other node.
• Similar forking is done when Vultr Managed Databases for Caching persists
its current state on disk. This happens every 10 minutes.
When Vultr Managed Databases for Caching creates a fork of itself, all the
memory pages of the new process are identical to the parent and don't
consume any extra memory. However, any changes in the parent process cause
memory to diverge and the real memory allocation to grow.

Apache Kafka®
A distributed event streaming platform for building real-time data
pipelines and applications with high-throughput, fault-tolerant
architecture.

Apache Kafka® Product Documentation
Provisioning
A guide explaining how to set up and deploy Vultr Managed Apache
Kafka® instances for your applications

How to Provision Vultr Managed
Apache Kafka®
Introduction
Vultr Managed Apache Kafka® is a highly available, scalable, and fully managed
data streaming platform that simplifies real-time data processing. Apache
Kafka® is designed to handle high-throughput data streams, making it ideal for
applications involving AI, machine learning, IoT, and microservices. With native
cloud integration, Vultr Managed Apache Kafka® seamlessly connects to
various data sources and consumers, enabling businesses to build powerful,
modern data architectures.
Follow this guide to provision Vultr Managed Apache Kafka® using the Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Click Add Managed Database.
3. Choose Apache Kafka® as the database engine.
4. Select the Server Type, Plan, and Brokers.
5. Choose a server location.
6. Select a VPC Network.
7. Enter a label.
8. Review the monthly and hourly cost estimates, and click Deploy Now.
Vultr API
1. Send a GET request to the List Managed Database Plans endpoint to
view all available plans.

```bash
$ curl "https://api.vultr.com/v2/databases/plans" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Create Database endpoint to create a new
database.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "database_engine" : "kafka",
        "database_engine_version" : "3.7",
        "plan" : "vultr-dbaas-startup-3x-occ-so-2-30-2",
        "region" : "atl",
        "label" : "remote-apache-kafka"
    }'
```
Visit the Create Database endpoint to view additional attributes to add to
your request.
3. Send a GET  request to the List Managed Databases endpoint to list all
databases.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json"
```
Vultr CLI
1. List the available database plans.

```bash
$ vultr-cli database plan list
```
2. Create a new Vultr Managed Apache Kafka® database.
```bash
$ vultr-cli database create --database-engine="kafka" --
database-engine-version="3.7" --region="atl" --plan="vultr-dbaas-startup-3x-occ-so-2-30-2" --label="remote-apache-kafka"
```
3. List all databases.
```bash
$ vultr-cli database list
```
Run vultr-cli database create --help to view all options.
Terraform
1. Ensure the Vultr Terraform provider is configured in your Terraform project.
2. Define the Managed Apache Kafka® database in your Terraform
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

resource "vultr_database" "kafka" {
database_engine = "kafka"
database_engine_version = "3.7"
region = "atl"  # e.g., ewr, ams, sgp,
atl
plan = "vultr-dbaas-startup-3x-occ-so-2-30-2"
label = "kafka-cluster-1"
```
    # Optional
    # vpc_id      = "<vpc-id>"
    # trusted_ips = ["192.0.2.1", "192.0.2.2"]
}
output "kafka_host" { value = vultr_database.kafka.host }
output "kafka_port" { value = vultr_database.kafka.port }
3. Apply the configuration and observe the following output:
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Management
Centralized tools and settings for administering your Vultr infrastructure,
accounts, and resources.

Connection
Establish and manage connections to your Vultr resources for secure
access and data transfer.

Connection Details
Learn how to find and use the connection information needed to connect
to your Vultr Managed Apache Kafka® instance.

How to Manage Connection Details
for Vultr Managed Apache Kafka®
Introduction
Vultr Managed Apache Kafka® allows customers to retrieve essential
information for connecting to their Kafka database. Users can easily access
details such as Host, Port, and SSL certificates to facilitate secure and reliable
connections. This user-friendly interface ensures customers have the necessary
information at their fingertips to configure their applications and services for
seamless integration with their Kafka environment.
Follow this guide to manage connection details for Vultr Managed Apache
Kafka® using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Select the target database.
3. Navigate to Connection Details under Overview.
4. Click Copy Connection String.
5. Click Copy URL.
6. Download Signed Certificate and save the certificate.
Vultr API
1. List all the databases by sending a GET request to the List Managed
Databases endpoint and note the target database's ID.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Get Managed Database endpoint and specify
the target database's ID.
```bash
$ curl "https://api.vultr.com/v2/databases/<database-id>" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Visit the Get Managed Database endpoint to view additional attributes
to add to your request.
3. Copy the host , port , user , and password values.
Vultr CLI
1. List all databases and note the target database's ID.
```bash
$ vultr-cli database list --summarize
```
2. Retrieve connection details by specifying the target database's ID.
```bash
$ vultr-cli database get database_id
```
Run vultr-cli database get --help to view all options.

Terraform
1. If you manage the database with Terraform, you can output connection
details from the resource.
# Assuming a managed database resource exists
resource "vultr_database" "kafka" {
database_engine = "kafka"
database_engine_version = "3.7"
region = "atl"
plan = "vultr-dbaas-startup-3x-occ-so-2-30-2"
label = "kafka-cluster-1"
}
output "kafka_host" { value = vultr_database.kafka.host }
output "kafka_port" { value = vultr_database.kafka.port }
output "kafka_user" { value = vultr_database.kafka.user }
# output "kafka_password" { value =
vultr_database.kafka.password  sensitive = true }
2. Apply the configuration and view the outputs with terraform output .

Trusted Sources
Learn how to configure and manage IP address-based access control for
your Vultr Managed Apache Kafka® database to enhance security.

How to Manage Trusted Sources for
Vultr Managed Apache Kafka®
Introduction
Vultr Managed Apache Kafka® allows customers to add IP addresses as trusted
sources for their Kafka database. Users can easily configure and manage a list
of approved IP addresses, enhancing security by controlling which sources can
access their data streams. This straightforward interface helps ensure that only
authorized connections are permitted, allowing customers to maintain a secure
environment while enabling seamless data flow.
Follow this guide to manage trusted sources for Vultr Managed Apache Kafka®
using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Select the target database.
3. Navigate to Trusted Sources under Overview and click Edit.
4. Specify a list of the IP addresses of the servers that you want to allow to
connect to the database and click Save.
Vultr API
1. List all the databases by sending a GET request to the List Managed
Databases endpoint and note the target database's ID.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Managed Database endpoint to
define the IP addresses of the servers that you want to allow to connect to
the database in array format and specify the target database's ID.
```bash
$ curl "https://api.vultr.com/v2/databases/<database-id>" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "trusted_ips" :
["192.0.2.1","192.0.2.2","192.0.2.3"]
    }'
```
Visit the Update Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all databases and note the target database's ID.
```bash
$ vultr-cli database list --summarize
```
2. Define the IP addresses of the servers that you want to allow to connect to
the database and specify the database's ID.
```bash
$ vultr-cli database update <database-id> \
--trusted-ips "192.0.2.1,192.0.2.2,192.0.2.3"
```
Run vultr-cli database update --help to view all options.
Terraform
1. Open your Terraform configuration for the existing Managed Apache
Kafka® resource.
2. Add or update the trusted_ips argument with the approved source IP
addresses.
```hcl
resource "vultr_database" "kafka" {
```
# ...existing fields (database_engine, region, plan,
label, etc.)
trusted_ips = [
"192.0.2.1",
"192.0.2.2",
"192.0.2.3"
]
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

VPC Networks
Learn how to attach, detach, and manage VPC networks for your Vultr
Managed Apache Kafka® subscription for secure communication.

How to Manage VPC Networks for
Vultr Managed Apache Kafka®
Introduction
Vultr Managed Apache Kafka® enables customers to attach or detach a VPC
network to their Kafka subscription. Users can easily configure their network
settings, allowing for secure and efficient communication between their Kafka
database and other resources within the VPC. This straightforward interface
provides customers with the flexibility to manage their network connections as
needed, ensuring optimal performance and security for their data streaming
operations.
Follow this guide to manage Vultr VPC Networks for Vultr Managed Apache
Kafka® with Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Select the target database.
3. Navigate to VPC Network under Overview.
4. Select a network from the list and click Update.
Vultr API
1. List all the databases by sending a GET request to the List Managed
Databases endpoint and note the target database's ID.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. List all the VPC networks by sending a GET  request to the List VPC
Networks endpoint and note the target network's ID.
```bash
$ curl "https://api.vultr.com/v2/vpcs" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PUT  request to the Update Managed Database endpoint to
attach the VPC network to the database by specifying the database ID and
the VPC network's ID.
```bash
$ curl "https://api.vultr.com/v2/databases/<database-id>" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "vpc_id" : "<vpc_network_id>"
    }'
```
4. Detach a VPC network from the database by sending a PUT  request to the
Update Managed Database endpoint and specify the database ID and
an empty VPC ID.
```bash
$ curl "https://api.vultr.com/v2/databases/<database-id>" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "vpc_id" : "<vpc_network_id>"
    }'
```
Visit the Update Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all database instances and note the database ID. For instance,
.
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c
```bash
$ vultr-cli database list --summarize
```
2. List all VPC networks and note the VPC ID. For instance, 778dd77c-a581-43a8-94e6-75b6ceb4354a .
```bash
$ vultr-cli vpc list
```
3. Attach the VPC network by specifying the database ID and the VPC ID.
```bash
$ vultr-cli database update database_id \
--vpc-id <vpc_id>
```
Run vultr-cli database update --help to view all options.
Terraform
1. Open your Terraform configuration for the existing Managed Apache
Kafka® resource.
2. Attach a VPC by setting the vpc_id  argument. To detach, set vpc_id = null .

```hcl
resource "vultr_database" "kafka" {
```
    # ...existing fields (database_engine, region, plan,
label, etc.)
vpc_id = var.vpc_id  # e.g., "778dd77c-a581-43a8-94e6-75b6ceb4354a"
}
TERRAFORM
# Detach VPC
resource "vultr_database" "kafka" {
    # ...existing fields
vpc_id = null
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Settings
Configure account-wide preferences, security settings, and manage API
access for your Vultr account.

Advanced Configuration
A guide for configuring advanced settings and parameters in Vultr
Managed Apache Kafka® deployments

How to Manage Advanced
Configurations for Vultr Managed
Apache Kafka®
Introduction
Vultr Managed Apache Kafka® allows customers to add and edit various
settings to optimize their Kafka database. Users can easily modify parameters
such as compression_type, auto_create_topics_enable, and many others to
tailor the configuration to their specific needs. This intuitive interface ensures
customers have full control over their Kafka environment, enabling them to
enhance performance and adjust functionalities as required for their data
streaming applications.
Follow this guide to manage advanced configurations for Vultr Managed Apache
Kafka® using the Vultr Console.
Vultr Console
1. Navigate to Products and select Databases.
2. Select the target database.
3. Navigate to Settings, and select Advanced Configurations.
4. Click Add Configuration Option.
5. select a Parameter, provide any additional value, and click Submit.
6. Edit the configuration parameter value by clicking Edit.
Vultr API
1. List all the databases by sending a GET request to the List Managed
Databases endpoint and note the target database's ID.

```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. List all available advanced options by sending a GET  request to the List
Advanced Options endpoint
```bash
$ curl "https://api.vultr.com/v2/databases/{database-id}/
advanced-options" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Enable advanced options by sending a PUT  request to the Update
Advanced Options endpoint
```bash
$ curl "https://api.vultr.com/v2/databases/{database-id}/
advanced-options" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "compression_type" : string,
}'
```
Visit the Advanced Options page to understand all available advanced
options.
Vultr CLI
1. List all database instances and note the database ID. For instance,
d6ac2a3c-92ea-43ef-8185-71a23e58ad8c .

```bash
$ vultr-cli database list --summarize
```
2. List all the advanced options enabled for the target database.
```bash
$ vultr-cli database advanced-option list <database-id>
```
3. Enable the advanced options for the target database.
```bash
$ vultr-cli database advanced-option update <database-id> --
compression-type <string>
```
Run vultr-cli database advanced-option update --help  to view and understand
all options for Vultr Managed Apache Kafka®.

Change Plan
Learn how to upgrade or downgrade your Vultr Managed Apache Kafka®
instance plan to adjust resources based on your needs.

How to Manage Plan for Vultr
Managed Apache Kafka®
Introduction
Vultr Managed Apache Kafka® allows customers to easily adjust their
subscription to meet growing needs. Users can upgrade their plan with a few
simple steps, ensuring they have access to additional resources and capabilities
as their data streaming requirements evolve. This user-friendly interface
facilitates seamless transitions between plans, enabling customers to scale
their Kafka database efficiently while maintaining optimal performance.
Follow this guide to manage plan for Vultr Managed Apache Kafka® using the
Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Select the target database.
3. Navigate to Settings, and select Change Plan.
4. Select a Server Type, a Plan, and number of Brokers.
5. Click Save to apply the changes.
Vultr API
1. List all the databases by sending a GET request to the List Managed
Databases endpoint and note the target database's ID.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Managed Database endpoint to
change the plan.
```bash
$ curl "https://api.vultr.com/v2/databases/<database-id>" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "plan" : "vultr-dbaas-business-3x-occ-so-2-200-4"
    }'
```
Visit the Update Managed Database endpoint to view additional
attributes to add to your request.
Vultr CLI
1. List all databases and note the target database's ID.
```bash
$ vultr-cli database list --summarize
```
2. Update the plan.
```bash
$ vultr-cli database update <database-id> \
--plan vultr-dbaas-business-cc-1-55-2
```
Run vultr-cli database update --help to view all options.

Terraform
1. Open your Terraform configuration and locate the Managed Apache Kafka®
resource.
2. Update the plan  argument of your existing Managed Apache Kafka®
resource, then re-apply.
```hcl
resource "vultr_database" "kafka" {
label = "kafka-cluster-1"
database_engine = "kafka"
database_engine_version = "3.7"
region = "atl"
plan = "vultr-dbaas-business-3x-occ-so-2-200-4" # Updated plan
}
```
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Datacenter Location
Learn how to change the datacenter location for your Vultr Managed
Apache Kafka® deployment

How to Change Datacenter
Locations for Vultr Managed
Apache Kafka®
Introduction
Vultr Managed Apache Kafka® enables customers to switch their Kafka
database to any of Vultr’s 33 global data center locations. Users can easily
select a new location to enhance performance and reduce latency based on
their operational needs. This straightforward interface allows for seamless
transitions between data centers, ensuring customers can optimize their data
streaming capabilities and maintain efficient connectivity across regions.
Follow this guide to change datacenter locations for Vultr Managed Apache
Kafka® using Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Select the target database.
3. Navigate to Settings, and select Datacenter Location.
4. Select a Data Center, and click Change Location.
Vultr API
1. List all the databases by sending a GET request to the List Managed
Databases endpoint and note the target database's ID.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Managed Database endpoint to
change the datacenter location.
```bash
$ curl "https://api.vultr.com/v2/databases/<database-id>" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "region" : "blr"
}'
```
Vultr CLI
1. List all databases and note the target database's ID.
```bash
$ vultr-cli database list --summarize
```
2. Change the datacenter location.
```bash
$ vultr-cli database update <database-id> --region="blr"
```
Run vultr-cli database update --help to view all options.
Terraform
1. Open your Terraform configuration and locate the Managed Apache Kafka®
resource.

2. Update the region on your Kafka resource and apply.
```hcl
resource "vultr_database" "kafka" {
label = "kafka-cluster-1"
database_engine = "kafka"
database_engine_version = "3.7"
region = "blr"  # New region
plan = "vultr-dbaas-business-3x-occ-so-2-200-4"
}
```
3. Apply and observe:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Delete Instance
A step-by-step guide for permanently removing a Vultr Managed Apache
Kafka® instance from your account.

How to Delete Vultr Managed
Apache Kafka®
Introduction
Vultr Managed Apache Kafka® allows customers to delete their Kafka
subscription when it is no longer needed. Users can easily navigate through the
interface to initiate the deletion process, ensuring a straightforward and
efficient experience. This feature ensures that customers can manage their
resources effectively, providing them with the flexibility to remove subscriptions
as their requirements change.
Follow this guide to delete Vultr Managed Apache Kafka® using the Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Select the target database.
3. Navigate to Settings, and select Delete Managed Database.
4. Click Destroy Database Instance.
5. Select the checkbox, and click Destroy Managed Database on the
confirmation prompt.
Vultr API
1. List all the databases by sending a GET request to the List Managed
Databases endpoint and note the target database's ID.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete Managed Database endpoint to
delete the database.
```bash
$ curl "https://api.vultr.com/v2/databases/<database-id>" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all databases and note the target database's ID.
```bash
$ vultr-cli database list --summarize
```
2. Delete the database.
```bash
$ vultr-cli database delete <database-id>
```
Run vultr-cli database delete --help to view all options.
Terraform
1. Open your Terraform configuration and locate the Managed Apache Kafka®
resource.
2. Remove the resource block or destroy it with Terraform.

```hcl
resource "vultr_database" "kafka" {
label = "kafka-cluster-1"
database_engine = "kafka"
database_engine_version = "3.7"
region = "atl"
plan = "vultr-dbaas-startup-3x-occ-so-2-30-2"
}
```
# To delete, either remove this block from configuration
# or run: terraform destroy -target vultr_database.kafka
3. Apply and observe the following output:
Apply complete! Resources: 0 added, 0 changed, 1 destroyed.

Upgrade Window
A scheduling feature that lets you control when system updates are
applied to your Managed Kafka instance.

How to Manage Upgrade Window
for Vultr Managed Apache Kafka®
Introduction
Vultr Managed Apache Kafka® allows customers to set and customize their
upgrade schedule by selecting the preferred day of the week and time. This
flexible interface gives users control over when system upgrades occur,
ensuring minimal disruption to their operations. Customers can easily adjust the
upgrade window to fit their workflow and ensure their Kafka database remains
up-to-date without impacting critical tasks.
Follow this guide to manage upgrade window for Vultr Managed Apache Kafka®
using the Vultr Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Select the target database.
3. Navigate to Settings, and select Upgrade Window.
4. Select a Day of the Week and a Start Time.
5. Click Apply Changes.
Vultr API
1. List all the databases by sending a GET request to the List Managed
Databases endpoint and note the target database's ID.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update Managed Database endpoint to
update the upgrade window.
```bash
$ curl "https://api.vultr.com/v2/databases/<database-id>" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "maintenance_dow" : "tuesday",
        "maintenance_time" : "13:00"
}'
```
Vultr CLI
1. List all databases and note the target database's ID.
```bash
$ vultr-cli database list --summarize
```
2. Update the maintenance day of the week and time.
```bash
$ vultr-cli database update <database-id> \
--maintenance-dow sunday \
--maintenance-time 01:00
```
Run vultr-cli database update --help to view all options.

Terraform
1. Open your Terraform configuration for the existing Managed Apache
Kafka® resource.
2. Add or update the maintenance_dow  and maintenance_time  arguments.
```hcl
resource "vultr_database" "kafka" {
```
    # ...existing fields (database_engine, region, plan,
label, etc.)
maintenance_dow = "sunday"
maintenance_time = "01:00"
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Quotas
A guide explaining how to set and manage resource limits for your Vultr
Managed Apache Kafka® clusters

How to Manage Quotas for Vultr
Managed Apache Kafka®
Introduction
Vultr Managed Apache Kafka® enables customers to create and manage quotas
for their Kafka database. Users can define parameters such as Client ID,
Consumer Byte Rate, Producer Byte Rate, and CPU Request Percentage to
control resource usage and ensure fair allocation among clients. This
straightforward interface helps customers monitor and adjust quotas as needed,
optimizing performance and maintaining stability in their data streaming
operations.
Follow this guide to manage Quotas for Vultr Managed Apache Kafka® with
Vultr Console, or CLI.
Vultr Console
1. Navigate to Products and select Databases.
2. Select the target database.
3. Navigate to Quotas to manage Quotas for Vultr Managed Apache Kafka®.
4. Click Add New Quota.
5. Provide values for Client ID, Consumer Byte Rate, Producer Byte
Rate, and CPU Request Percentage.
6. Select a User and click Add Quota.
Vultr CLI
1. List all databases and note the target database's ID.

```bash
$ vultr-cli database list --summarize
```
2. Create a database quota for the target database.
```bash
$ vultr-cli database quota create <database-id> --client-id
<string> --consumer-byte-rate <int> --producer-byte-rate
<int> --request-percentage <int> --user <string>
```
Run vultr-cli database quota create --help  to understand and view all options.
3. List and confirm the quota created.
```bash
$ vultr-cli database quota list <database-id>
```
4. Delete a quota for the target database.
```bash
$ vultr-cli database quota delete <database-id> <client-id>
<username>

Topics
A guide explaining how to create, view, and manage topics within your
Vultr Managed Apache Kafka® instance.
```

How to Manage Topics for Vultr
Managed Apache Kafka®
Introduction
Vultr Managed Apache Kafka® allows customers to create and manage topics
within their Kafka database. Users can easily define topic configurations,
including partitioning and replication settings, to suit their data streaming
needs. This straightforward interface enables efficient organization of data
streams, ensuring customers can scale their applications and optimize
performance while maintaining control over their topics.
Follow this guide to manage Topics for Vultr Managed Apache Kafka® with Vultr
Console, API, or CLI.
Vultr Console
1. Navigate to Products and select Databases.
2. Select the target database.
3. Navigate to Topics and Users to manage Quotas for Vultr Managed
Apache Kafka®.
4. Click Add New Topic.
5. Provide values for Topic Name, Partition Count, Replication Factor,
Retention Hours, and Retention Bytes. Click Add Topic.
Vultr API
1. List all the databases by sending a GET request to the List Managed
Databases endpoint and note the target database's ID.

```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Create Database Topic endpoint to create a
topic for your database.
```bash
$ curl "https://api.vultr.com/v2/databases/<database-id>/
topics" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "name" : "some_new_topic",
        "partitions" : 3,
        "replication" : 3,
        "retention_hours" : 160,
        "retention_bytes" : -1
}'
```
3. Send a GET  request to the List Database Topics endpoint to list all the
topics.
```bash
$ curl "https://api.vultr.com/v2/databases/<database-id>/
topics" \
    -X GET \
    -H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all databases and note the target database's ID.
```bash
$ vultr-cli database list --summarize
```
2. Create a database topic for the target database.
```bash
$  vultr-cli database topic create <database-id> --name
<string> --partitions <int> --retention-bytes <int> --
retention-hours <int>
```
Run vultr-cli database topic create --help  to understand and view all options.
3. List and confirm the topic created.
```bash
$ vultr-cli database topic list <database-id>
```
4. Delete a topic for the target database.
```bash
$ vultr-cli database topic delete <database-id> <topic-name>

Usage
Learn how to monitor and manage resource usage for your Vultr Managed
Apache Kafka® deployment
```

How to Manage Usage for Vultr
Managed Apache Kafka®
Introduction
Vultr Managed Apache Kafka® enables users to view key metrics for their
database, including General Usage, vCPU Usage, Disk Operations, and Network
activity. This clear and organized interface allows customers to track their
resource consumption over time, helping them optimize performance and
manage costs effectively. Users can easily access detailed usage statistics to
make informed decisions about scaling and resource allocation.
Follow this guide to manage usage for Vultr Managed Apache Kafka® with Vultr
Console, API, and CLI.
Vultr Console
1. Navigate to Products and select Databases.
2. Select the target database.
3. Navigate to Usage Graphs.
4. View the General Usage, vCPU Usage, Disk Operations, and Network.
Vultr API
1. List all the databases by sending a GET request to the List Managed
Databases endpoint and note the target database's ID.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Get Database Usage Information endpoint to
get the overall usage information of the target database.
```bash
$ curl "https://api.vultr.com/v2/databases/{database-id}/
usage" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all databases and note the target database's ID.
```bash
$ vultr-cli database list --summarize
```
2. Get the usage information of the target database.
```bash
$ vultr-cli database usage get <database-id>

Users
Learn how to create, modify, and manage user accounts for your Vultr
Managed Apache Kafka® deployment
```

How to Manage Users for Vultr
Managed Apache Kafka®
Introduction
Vultr Managed Apache Kafka® user management feature allows customers to
easily add or delete users from their Kafka instance and manage user
permissions. This intuitive interface streamlines access control, enabling
organizations to define roles and responsibilities for each user, ensuring secure
and efficient collaboration. With flexible permission settings, tailoring the user
experience to meet their operational needs while maintaining security
protocols.
Follow this guide to manage users for Vultr Managed Apache Kafka® with Vultr
Console, API, CLI, or Terraform.
Vultr Console
1. Navigate to Products and select Databases.
2. Select the target database.
3. Navigate to Topic & Users to manage Users for Vultr Managed Apache
Kafka®.
4. Click Add New User.
5. Provide values for Username, Permissions, and Password.
6. Click Create New User.
Vultr API
1. List all the databases by sending a GET request to the List Managed
Databases endpoint and note the target database's ID.

```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Create Database User endpoint to create a
new user for your database.
```bash
$ curl "https://api.vultr.com/v2/databases/<database-id>/
users" \
    -X POST \
    -H "Authorization: Bearer ${VULTR_API_KEY}" \
    -H "Content-Type: application/json" \
    --data '{
        "username": "user1",
        "password": "p@ssWord123#",
        "permission": "readwrite"
}'
```
3. Send a GET  request to the List Database Users endpoint to list all the
users.
```bash
$ curl "https://api.vultr.com/v2/databases/<database-id>/
users" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
4. Send a DELETE request to Delete Database User endpoint
```bash
$ curl "https://api.vultr.com/v2/databases/{database-id}/
users/{username}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```

Vultr CLI
1. List all databases and note the target database's ID.
```bash
$ vultr-cli database list --summarize
```
2. List all the users.
```bash
$ vultr-cli database user list <database-id>
```
3. Delete a user.
```bash
$ vultr-cli database user delete <database-id> <user-name>
```
Run vultr-cli database update --help to view all options.
Terraform
1. Ensure the Vultr Terraform provider is configured.
2. Create a Kafka user with Terraform.
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
```
# Existing database assumed
variable "database_id" { type = string }
resource "vultr_database_user" "kafka_user" {
database_id = var.database_id
username = "user1"
password = "p@ssWord123#"
permission = "readwrite"
}
3. To delete the user, remove the resource block or run:
```bash
$ terraform destroy -target vultr_database_user.kafka_user

Kafka Connect
A tool for integrating Apache Kafka with external systems through
connectors for data import and export
```

How to Use Kafka Connect with
Vultr Managed Apache Kafka®
Introduction
Kafka Connect is a key component that enables scalable and reliable data
integration in Vultr Managed Apache Kafka® cluster. You can use Kafka Connect
to move data in and out of topics in a Vultr Managed Apache Kafka®, providing
an efficient way to integrate multiple applications such as databases, Object
Storage, and Elasticsearch in your cluster.
Follow this guide to enable Kafka Connect in Vultr Managed Apache Kafka® and
create new connectors using the Vultr Console, Vultr API, or Terraform.
Vultr Console
1. Navigate to Products and click Databases.
2. Click your target Vultr Managed Apache Kafka® cluster to open its
management page.
3. Navigate to the Kafka Connect tab.
4. Verify the list of available connectors compatible with your cluster.
5. Choose your desired connector type:
- Sink: Read data from Kafka topics and push the data to external
sources such as search indexes, batch systems and databases for
processsing.
- Source: Pull data from external sources and publish the data to
specific Kafka topics in the cluster.
6. Click Add Connector.

7. Specify the connector label and specify the topics to link in your cluster.
8. Modify the default Config JSON parameters to include the connector
information, such as:
- Destination details.
- Output format.
- Queries.
- Protocols.
- Size specifications.
- Maximum timeout and retry information.
9. Remove any unused optional properties in the connector configuration.
10. Click Add Connector to create the connector.
11. Verify the list of active connectors in the cluster.
12. Click Connector Status to monitor the connector status.
- Verify the Connector State information.
- Click Refresh Status to refresh the connector information.
- Click Restart Connector to restart it.
- Click Pause Connector to pause the configuration.
- Click Resume Connector to resume a paused connector.
13. Click Edit Connector to modify the connector information.
14. Click Delete Connector to delete the connector.
Vultr API
1. Send a GET request to the List Managed Databases endpoint and note
the target database cluster's ID.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Database Available Connectors
endpoint, specifing the database ID to list all available connectors and note
the target connector class.
```bash
$ curl "https://api.vultr.com/v2/databases/{database-id}/
available-connectors" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a GET  request to the Get Database Connector Configuration Schema,
specifying the target database ID and connector class to get the default
connector configuration.
```bash
$ curl "https://api.vultr.com/v2/databases/{database-id}/
available-connectors/{connector-class}/configuration" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
4. Send a GET  request to the List Database Topics endpoint, specifying the
target database ID to list all topics and note your target topic's ID.
```bash
$ curl "https://api.vultr.com/v2/databases/<database-id>/
topics" \
    -X GET \
    -H "Authorization: Bearer ${VULTR_API_KEY}"
```
5. Send a POST  request to the Create Database Connector endpoint,
specifying the target database ID, connector class and topics to create a
new connector.

```bash
$ curl "https://api.vultr.com/v2/databases/{database-id}/
connectors" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
"name" : "<connector-name>",
"class" : "<connector-class>",
"topics" : "<topic>",
"config" : {
"{configuration property}": <value>,
"{configuration property}": "<value>",
"{configuration property}": "<value>"
}
}'
```
6. Send a GET request to the List Database Connectors endpoint,
specifying the target database ID to list all active connectors.
```bash
$ curl "https://api.vultr.com/v2/databases/{database-id}/
connectors" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
7. Send a PUT request to the Update Database Connector endpoint,
specifying the target database ID and the connector name to update its
configuration.
```bash
$ curl "https://api.vultr.com/v2/databases/{database-id}/
connectors/{connector-name}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
"topics" : "<topic>",
"config" : {

"{configuration property}": <value>,
"{configuration property}": "<value>",
"{configuration property}": "<value>"
}
}'
```
8. Send a GET request to the Get Database Connector Status endpoint,
specifyng the target database ID and the connector name to get its status
information.
```bash
$ curl "https://api.vultr.com/v2/databases/{database-id}/
connectors/{connector-name}/status" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
9. Send a POST request to the Pause Database Connector endpoint,
specifying the target database ID and the connector name to pause.
```bash
$ curl "https://api.vultr.com/v2/databases/{database-id}/
connectors/{connector-name}/pause" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
10. Send a POST request to the Resume Database Connector endpoint,
specifying the target database ID and the connector name to resume.
```bash
$ curl "https://api.vultr.com/v2/databases/{database-id}/
connectors/{connector-name}/resume" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
11. Send a POST request to the Restart Database Connector Task endpoint,
specifying the target database ID, and the connector task ID to restart.

```bash
$ curl "https://api.vultr.com/v2/databases/{database-id}/
connectors/{connector-name}/tasks/{task-id}/restart" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
12. Send a DELETE  request to the Delete Database Connector endpoint,
specifying the target database ID and the connector name to delete from
the cluster.
```bash
$ curl "https://api.vultr.com/v2/databases/{database-id}/
connectors/{connector-name}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Terraform
1. Open your Terraform configuration for the existing Managed Apache
Kafka® resource.
2. Enable Kafka Connect by setting enable_kafka_connect = true  on your Kafka
resource and apply.
```hcl
resource "vultr_database" "kafka" {
```
    # ...existing fields (database_engine, region, plan,
label, etc.)
enable_kafka_connect = true
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Schema Registry
A centralized repository for managing and validating schemas in Apache
Kafka® to ensure data compatibility and consistency

How to Enable Schema Registry for
Vultr Managed Apache Kafka®
Introduction
Vultr Managed Apache Kafka® includes built-in support for Schema Registry,
allowing customers to centrally manage and store schemas with ease. This
feature ensures data consistency and compatibility across Kafka topics as
workloads grow. With an intuitive interface, users can seamlessly register,
retrieve, and evolve schemas, helping maintain reliable data streaming
pipelines while supporting smooth application development and integration.
Follow this guide to enable Schema Registry for Vultr Managed Apache Kafka®
using the Vultr Console, API, or Terraform.
Note
Schema Registry for Vultr Managed Apache Kafka® is only available on
business plans or higher.
Vultr Console
1. Navigate to Products and select Databases.
2. Select the target database.
3. Navigate to Schema Registry, and click Enable Schema Registry.
4. Optional: Click Add Configuration Option to add advanced configuration
parameters.
5. Select a parameter and the boolean value according to preference.
- leader_eligibility: Determines whether a broker is eligible to become
a leader for partitions.

- retriable_errors_silenced: Controls whether retriable errors are
logged or suppressed.
- schema_reader_strict_mode: Applies to Kafka topics that involve
schema validation (usually with Kafka’s Schema Registry in Avro, JSON
Schema, or Protobuf setups).
Vultr API
1. List all the databases by sending a GET  request to the List Managed
Databases endpoint and note the target database's ID.
```bash
$ curl "https://api.vultr.com/v2/databases" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Enable Schema Registry by sending a PUT  request to the Update
Managed Database endpoint
```bash
$ curl "https://api.vultr.com/v2/databases/{database-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "enable_schema_registry": true
    }'
```
3. List all Schema Registry Advanced Options by sending a GET  request to the
List Schema Registry Advanced Options endpoint.
```bash
$ curl "https://api.vultr.com/v2/databases/{database-id}/
advanced-options/schema-registry" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
4. Enable the Schema Registry advanced options by sending a PUT  request to
the Update Schema Registry Advanced Options endpoint
```bash
$ curl "https://api.vultr.com/v2/databases/{database-id}/
advanced-options/schema-registry" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "leader_eligibility" : true,
        "retriable_errors_silenced" : true
    }'
```
Terraform
1. Open your Terraform configuration for the existing Managed Apache
Kafka® resource.
2. Enable Schema Registry by setting enable_schema_registry = true  on your
Kafka resource and apply.
```hcl
resource "vultr_database" "kafka" {
```
    # ...existing fields (database_engine, region, plan,
label, etc.)
enable_schema_registry = true
}
3. Apply the configuration and observe the following output:
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

FAQ
Essential information and answers to common questions about Vultrs
Managed Databases for Apache Kafka service.

Frequently Asked Questions (FAQs)
About Vultr Managed Databases
for Apache Kafka®
Introduction
These are the frequently asked questions for Vultr Managed Apache Kafka®.
Can I upgrade the plan for Vultr Managed
Apache Kafka® ?
You can upgrade the plan for Vultr Managed Apache Kafka® using the Vultr
Console, API, or CLI. However, downgrading is not supported, as reducing the
hard disk size could lead to potential data loss. Plan upgrades are seamless,
ensuring that your Kafka cluster has more resources without disrupting service.
Can I change the datacenter location for
Vultr Managed Apache Kafka® ?
Yes, it is possible to switch the datacenter location using the Vultr Console, API,
or CLI. However, please note that changing the datacenter location takes time,
as data from the current location must be transferred to the new one. This
process ensures your data is securely migrated, but may involve some
downtime during the transfer.

Can I specify a particular upgrade window
for Vultr Managed Apache Kafka® ?
Yes, you can specify a specific upgrade window using the Vultr Console, API, or
CLI. During maintenance, the DNS for the service will remain unchanged, but
the underlying IP address will be updated. New maintenance updates will be
automatically installed within a four-hour window starting from the designated
time you set. This process ensures minimal disruption to your services while
maintaining your system's performance and security.
Is Vultr Managed Apache Kafka® available
globally across all Vultr locations ?
Yes, Vultr Managed Apache Kafka® is available in 33 global locations around the
world and can be easily provisioned using the Vultr Console, API, or CLI. This
extensive network of locations ensures that you can deploy Kafka close to your
users for optimal performance and low latency, allowing you to meet your data
processing needs effectively.
Can I integrate Vultr Managed Apache
Kafka® with Vultr Serverless Inference for AI
deployments ?
Yes, you can integrate Vultr Managed Apache Kafka® with Vultr Serverless
Inference for AI deployments. This integration ensures that the Turnkey RAG
vector database is continuously updated with the latest data, allowing AI
models to generate real-time, accurate outputs without the need for manual
data uploads. This capability is crucial for businesses that depend on AI-driven
decision-making, as it streamlines data handling and enhances overall
operational efficiency.