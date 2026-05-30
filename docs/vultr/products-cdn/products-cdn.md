CDN
Content Delivery Network (CDN) service that accelerates content
distribution through global edge locations using different zone
configurations.

Pull Zone
A content delivery system that distributes your files across Vultr's global
network to improve load times and reduce bandwidth costs.

Provisioning
The process of setting up and configuring a new Vultr server or service to
make it ready for use.

How to Provision Vultr CDN Pull
Zones
Introduction
Vultr CDN Pull Zones streamline content delivery by automatically fetching
content from your origin server and distributing it globally across Vultr's edge
network, which spans 33 locations worldwide. This setup ensures that your
content is delivered quickly and reliably to users regardless of their location.
Additionally, Vultr CDN Pull Zones support custom domains, allowing you to
serve content under your own branded domain while leveraging the
performance and scalability of the CDN.
Follow this guide to provision Vultr CDN Pull Zones on your Vultr account, set up
custom domains, and optimize content delivery using the Vultr Console, API, or
CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Pull Zones.
2. Click Add CDN Pull Zone.
3. Provide a Label and an Origin URL.
4. Optional: Enable features such as Cross-Origin Resource Sharing
(CORS), Gzip, Block AI Bots, and Block Potentially Malicious Bots.
5. Optional: Provide a Custom Domain along with its Domain-validated
Certificate(SSL/TLS) and Secret Key files. These files are only required if the
Origin URL uses the HTTPS scheme.
6. Click Add CDN Pull Zone.

Vultr API
1. Send a POST  request to the Create CDN Pull Zones endpoint to create a
CDN Pull Zone subscription.
Note
When configuring a custom domain, for the HTTPS  origin scheme, you
must provide a Domain-validated SSL/TLS certificate and the
corresponding Private Key. However, for HTTP  origin scheme, these
certificates are not required.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "label": "{label}",
        "origin_scheme": "{http_or_https}",
        "origin_domain": "{origin-domain}",
        "vanity_domain": "{custom-vanity-domain}",
        "ssl_cert": "{BASE64_ENCODED_SSL_CERT_CONTENT}",
        "ssl_cert_key": "{BASE64_ENCODED_SSL_KEY_CONTENT}",
        "cors": false,
        "gzip": false,
        "block_ai": false,
        "block_bad_bots": false
    }'
```
2. Send a GET  request to the List CDN Pull Zones endpoint to list all the
available Vultr CDN Pull Zone subscriptions.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```

Vultr CLI
1. Create a CDN Pull Zone subscription.
```bash
$ vultr-cli cdn pull create \
--label "<label>" \
--scheme "<http_or_https>" \
--domain "<origin-domain>"
```
Run vultr-cli cdn pull create --help  to view additional options for enabling
features like Cross-Origin Resource Sharing (CORS), Gzip, Block AI
Bots, and Block Potentially Malicious Bots.
2. List all available CDN Pull Zone subscriptions.
```bash
$ vultr-cli cdn pull list
```

Features
Provides an overview of Vultrs key capabilities, services, and platform
advantages.

Block AI Bots
A security feature that protects your website by blocking automated bots
and malicious traffic while allowing legitimate users to access your
content.

How to Enable AI Bot Blocking for
Vultr CDN Pull Zones
Introduction
AI Bot Blocking in Vultr CDN Pull Zones helps protect your content by preventing
unwanted AI bots from accessing your site. This feature safeguards your site
from harmful traffic and ensures that your bandwidth is utilized efficiently by
real users only. By enabling AI Bot blocking, you can enhance security and
maintain optimal performance for your content delivery.
Follow this guide to enable the AI Bot blocking feature for Vultr CDN Pull Zones
on your Vultr account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Pull Zones.
2. Click your target CDN Pull Zone subscription to open its management
page.
3. Click Features.
4. Select block_ai and click Update Features.
Vultr API
1. Send a GET request to the List CDN Pull Zones endpoint and note the
target Pull Zone subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update CDN Pull Zone endpoint to enable AI
Bot blocking feature for your target Pull Zone subscription.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones/{pullzone-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "block_ai": true
    }'
```
Vultr CLI
1. List all available CDN Pull Zone subscriptions and note the target Pull Zone
subscription's ID.
```bash
$ vultr-cli cdn pull list
```
2. Enable AI Bot blocking feature for your target Pull Zone subscription.
```bash
$ vultr-cli cdn pull update <pullzone-id> --block-ai

Block Bad Bots
A security feature that automatically identifies and blocks malicious bot
traffic to protect your website from scraping, spam, and automated
attacks.
```

How to Enable Bad Bot Blocking for
Vultr CDN Pull Zones
Introduction
Bad Bot Blocking in Vultr CDN Pull Zones helps protect your site from unwanted
bots by filtering out unnecessary traffic. This feature ensures that only
legitimate users can access your content, enhancing your site’s security and
performance.
Follow this guide to enable the Bad Bot blocking feature for Vultr CDN Pull
Zones on your Vultr account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Pull Zones.
2. Click your target CDN Pull Zone subscription to open its management
page.
3. Click Features.
4. Select block_bad_bots and click Update Features.
Vultr API
1. Send a GET request to the List CDN Pull Zones endpoint and note the
target Pull Zone subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update CDN Pull Zone endpoint to enable Bad
Bot blocking feature for your target Pull Zone subscription.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones/{pullzone-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "block_bad_bots": true
    }'
```
Vultr CLI
1. List all available CDN Pull Zone subscriptions and note the target Pull Zone
subscription's ID.
```bash
$ vultr-cli cdn pull list
```
2. Enable Bad Bot blocking feature for your target Pull Zone subscription.
```bash
$ vultr-cli cdn pull update <pullzone-id> --block-bad-bots

CORS
Cross-Origin Resource Sharing (CORS) is a security feature that controls
how web resources on one domain can be requested from another
domain.
```

How to Enable CORS Protection for
Vultr CDN Pull Zones
Introduction
Cross-Origin Resource Sharing (CORS) Protection in Vultr CDN Pull Zones
provides you with the capability to manage which websites can access your
content. This feature helps secure your resources by allowing you to specify
approved domains and prevent unauthorized sites from making requests. By
implementing CORS protection, you ensure that your content is only shared
with trusted sources, enhancing both security and control over how your
content is distributed and accessed.
Follow this guide to enable the CORS protection feature for Vultr CDN Pull Zones
on your Vultr account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Pull Zones.
2. Click your target CDN Pull Zone subscription to open its management
page.
3. Click Features.
4. Select cors and click Update Features.
Vultr API
1. Send a GET request to the List CDN Pull Zones endpoint and note the
target Pull Zone subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update CDN Pull Zone endpoint to enable
cors protection feature for your target Pull Zone subscription.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones/{pullzone-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "cors": true
    }'
```
Vultr CLI
1. List all available CDN Pull Zone subscriptions and note the target Pull Zone
subscription's ID.
```bash
$ vultr-cli cdn pull list
```
2. Enable cors protection feature for your target Pull Zone subscription.
```bash
$ vultr-cli cdn pull update <pullzone-id> --cors

GZIP
A compression method that reduces file sizes to improve website loading
speed and bandwidth usage.
```

How to Enable GZIP Compression
for Vultr CDN Pull Zones
Introduction
GZIP Compression in Vultr CDN Pull Zones reduces the size of your content
before it is delivered to users. This feature enhances the efficiency of data
transfer, leading to faster load times and improved overall site performance. By
compressing your content with GZIP, you ensure that your users experience
quicker access to your site, optimizing both bandwidth usage and user
satisfaction.
Follow this guide to enable the GZIP compression feature for Vultr CDN Pull
Zones on your Vultr account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Pull Zones.
2. Click your target CDN Pull Zone subscription to open its management
page.
3. Click Features.
4. Select gzip and click Update Features.
Vultr API
1. Send a GET request to the List CDN Pull Zones endpoint and note the
target Pull Zone subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update CDN Pull Zone endpoint to enable
gzip compression feature for your target Pull Zone subscription.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones/{pullzone-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "gzip": true
    }'
```
Vultr CLI
1. List all available CDN Pull Zones subscriptions and note the target Pull
Zone subscription's ID.
```bash
$ vultr-cli cdn pull list
```
2. Enable gzip compression feature for your target Pull Zone subscription.
```bash
$ vultr-cli cdn pull update <pullzone-id> --gzip
```

Management
Centralized tools and settings for managing your Vultr account,
infrastructure, and resources.

Active Regions
A geographical overview of Vultrs operational data center locations where
cloud services are currently available.

How to Manage Active Regions for
Vultr CDN Pull Zones
Introduction
Active Regions in Vultr CDN function as dedicated Pull Zones that dynamically
cache and distribute content across selected regions for optimal delivery. With
32 global locations to choose from, you can ensure that your content is
efficiently delivered to users around the world. By updating the active regions,
you can improve performance and tailor content distribution to better serve
different geographic areas.
Follow this guide to update the active regions for a Vultr CDN Pull Zone
subscription on your Vultr account using the Vultr Console or API.
Vultr Console
1. Navigate to Products, click CDN, and then click Pull Zones.
2. Click your target CDN Pull Zone subscription to open its management
page.
3. Click Regions.
4. Select any region in which you want a Pull Zone.
5. Deselect any region in which you do not want a Pull Zone.
Vultr API
1. Send a GET request to the List CDN Pull Zones endpoint and note the
target Pull Zone subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Regions endpoint and note your target
region ID.
```bash
$ curl "https://api.vultr.com/v2/regions" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PUT  request to the Update CDN Pull Zone endpoint to update the
Pull Zone regions.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones/{pullzone-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "regions": [
            "{region_1_id}",
            "{region_2_id}",
            "{region_3_id}"
        ]
    }'
```

CDN Info
Provides information about Vultrs Content Delivery Network (CDN) service
for distributing content globally with low latency.

How to Retrieve CDN Information
for Vultr CDN Pull Zones
Introduction
Vultr CDN simplifies content access by providing a unique CDN URL that routes
requests through Vultr's global network. This ensures that your content is
delivered quickly and efficiently from the nearest edge location, optimizing
performance and reducing latency. By using this CDN URL, you can enhance the
speed and reliability of content delivery to users around the world.
Follow this guide to retrieve the Vultr CDN URL on your Vultr account using the
Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Pull Zones.
2. Click your target CDN Pull Zone subscription to open its management
page.
3. Click Overview.
4. Under CDN Information, locate CDN URL, and copy it for further use.
Vultr API
1. Send a GET request to the List CDN Pull Zones endpoint and note the
target Pull Zone subscription's CDN URL.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available CDN Pull Zone subscriptions and note the target Pull Zone
subscription's CDN URL.
```bash
$ vultr-cli cdn pull list
```

Custom Domain
Configure a personalized domain name for your Vultr application to
create a professional, branded web presence.

How to Configure Custom Domain
for Vultr CDN Pull Zones
Introduction
Custom domain functionality in Vultr CDN Pull Zones allows you to serve your
content using your own domain name, providing a branded experience and
enhancing your site's credibility. By setting up a custom domain, you can ensure
that your content is accessed through a personalized URL, which can improve
user trust and engagement. This feature enables you to integrate your content
delivery seamlessly with your existing domain infrastructure.
Note
To use a custom domain (or vanity domain) with your Vultr CDN Pull Zone, you
need to create a CNAME DNS record for your domain through your domain
provider. This CNAME record should point to the default CDN domain that is
automatically generated when you create your Vultr CDN Pull Zone
subscription. After setting up the CNAME record, make sure that the DNS
changes have propagated successfully before configuring your custom
domain in the Vultr CDN settings.
Follow this guide to configure a custom domain for Vultr CDN Pull Zones on your
Vultr account using the Vultr Console or API.
Vultr Console
1. Navigate to Products, click CDN, and then click Pull Zones.
2. Click your target CDN Pull Zone subscription to open its management
page.
3. Click Custom Domain.
4. Provide the Custom Domain.

5. Upload Domain-validated Certificate(SSL/TLS) and Private Key files if
the Origin URL uses HTTPS origin scheme.
6. Click Update Custom Domain.
Vultr API
1. Send a GET  request to the List CDN Pull Zones endpoint and note the
target Pull Zone subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update CDN Pull Zone endpoint to update the
custom domain.
Note
The API request below is for configuring a custom domain with an HTTPS
origin scheme. For HTTPS , you are required to provide a Domain-validated SSL/TLS certificate and the corresponding Private Key. For
, these certificates are not needed.
```http
$ curl "https://api.vultr.com/v2/cdns/pull-zones/{pullzone-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "vanity_domain": "{custom_vanity_domain}",
        "ssl_cert": "{BASE64_ENCODED_SSL_CERT_CONTENT}",
        "ssl_cert_key": "{BASE64_ENCODED_SSL_KEY_CONTENT}"
    }'
```

Monitor
A system for tracking server performance metrics, setting up alerts, and
visualizing resource usage across your Vultr infrastructure.

How to Monitor Vultr CDN Pull
Zones
Introduction
Vultr CDN's Monitoring Tools offer comprehensive real-time insights into traffic
metrics, allowing you to closely track the performance of content delivery
across your global network. These tools enable you to monitor various aspects
of content distribution, analyze traffic patterns, and identify trends that can help
optimize your CDN usage. By leveraging these insights, you can enhance
performance, address potential issues proactively, and ensure efficient content
delivery to users worldwide.
Follow this guide to view and analyze the Vultr CDN Pull Zone metrics on your
Vultr account using the Vultr Console.
1. Navigate to Products, click CDN, and then click Pull Zones.
2. Click your target CDN Pull Zone subscription to open its management
page.
3. Click Usage Graphs to view the traffic metrics.
4. Under Network Monitors, select a time Range (Last 24 hours, Last
Week, or Last Month) from the drop down menu, and choose a region from
the list of active regions available for your CDN Pull Zone subscription.
5. Analyze the Usage Graphs:
- Hit Ratio: Measures the percentage of requests served from the
cache versus those fetched from the origin. A higher hit ratio
indicates better caching efficiency.
- Server Traffic: Displays the amount of data transferred through the
CDN, helping you track bandwidth usage.

Delete
Permanently remove this resource from your Vultr account.

How to Delete Vultr CDN Pull Zones
Introduction
Deleting a Vultr CDN Pull Zone subscription is a straightforward process that
removes all associated caching and distribution configurations for your content.
This action will terminate the CDN Pull Zone subscription, stopping the delivery
and caching of your content across Vultr's global network. By deleting the Pull
Zone, you will clear all related cached data and configurations, effectively
halting any further distribution and access through the CDN.
Follow this guide to delete a Vultr CDN Pull Zone subscription from your Vultr
account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Pull Zones.
2. Click your target CDN Pull Zone subscription to open its management
page.
3. Click the delete icon in the top-right corner of the management page.
4. Check the Yes, destroy this CDN box in the confirmation prompt, and
click Delete CDN to permanently delete the target CDN Pull Zone
subscription.
Vultr API
1. Send a GET request to the List CDN Pull Zones endpoint and note the
target Pull Zone subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete CDN Pull Zone endpoint to delete
the target Pull Zone subscription.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones/{pullzone-id}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available CDN Pull Zone subscriptions and note the target Pull Zone
subscription's ID.
```bash
$ vultr-cli cdn pull list
```
2. Delete the target Pull Zone subscription.
```bash
$ vultr-cli cdn pull delete <pullzone-id>
```

Purge
A feature that allows you to clear cached content from Vultrs CDN to
ensure visitors receive the most up-to-date version of your files.

How to Purge Vultr CDN Pull Zones
Introduction
Purging a Vultr CDN Pull Zone subscription is a crucial operation that forces the
removal of cached content across all edge locations, ensuring that subsequent
requests fetch the latest version directly from the origin server. This process is
essential for content updates, preventing stale data from being served to users.
When a purge is initiated, the CDN instructs all proxy servers to discard stored
files and revalidate them on the next request, temporarily increasing origin
traffic as new assets are retrieved.
Note
Purging a Vultr CDN Pull Zone subscription can only be performed once every
six hours. The process may take a few extra seconds to complete.
Follow this guide to purge Vultr CDN Pull Zones from your Vultr account using
the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Pull Zones.
2. Click your target CDN Pull Zone subscription to open its management
page.
3. Click Purge CDN in the top-right corner of the management page.
4. Check the Yes, Purge this CDN box in the confirmation prompt, and click
Purge CDN to initiate the purging process.

Vultr API
1. Send a GET  request to the List CDN Pull Zones endpoint and note the
target Pull Zone subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Purge CDN Pull Zone endpoint to purge the
target Pull Zone subscription.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones/{pullzone-id}/purge" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available CDN Pull Zone subscriptions and note the target Pull Zone
subscription's ID.
```bash
$ vultr-cli cdn pull list
```
2. Purge the target Pull Zone subscription.
```bash
$ vultr-cli cdn pull purge <pullzone-id>
```

Update
Modify your servers configuration, including hostname, tags, user data,
firewall groups, and other settings.

How to Update Vultr CDN Pull
Zones
Introduction
Updating the label of a Vultr CDN Pull Zone is a straightforward process that
enables you to better organize and manage your CDN configuration. This
process enhances the clarity of your CDN management and ensures your Pull
Zones are consistently aligned with your workflow.
Follow this guide to update the label of a Vultr CDN Pull Zone subscription on
your Vultr account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Pull Zones.
2. Click your target CDN Pull Zone subscription to open its management
page.
3. Click Overview.
4. Under CDN Information, locate the Name field.
5. Click the current name of the Pull Zone subscription and enter a new,
appropriate name.
6. Click the check-mark icon to save the changes.
Vultr API
1. Send a GET request to the List CDN Pull Zones endpoint and note the
target Pull Zone subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update CDN Pull Zone endpoint to update the
target Pull Zone subscription's label.
```bash
$ curl "https://api.vultr.com/v2/cdns/pull-zones/{pullzone-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "label": "{updated_label}"
    }'
```
Vultr CLI
1. List all available CDN Pull Zone subscriptions and note the target Pull Zone
subscription's ID.
```bash
$ vultr-cli cdn pull list
```
2. Update the target Pull Zone subscription's label.
```bash
$ vultr-cli cdn pull update <pullzone-id> --label
"<updated_label>"
```

FAQ
A collection of frequently asked questions and answers about Vultr
services and features.

61
011 How do Vultr CDN Pull Zones impact my website’s SEO? 61
012 How can I manage Vultr CDN Pull Zones using the Vultr CLI
and API? 62

Frequently Asked Questions (FAQs)
About Vultr CDN Pull Zone
Introduction
These are the frequently asked questions for Vultr CDN Pull Zones.
What is a Vultr CDN Pull Zone, and how does
it work?
A Vultr CDN Pull Zone automatically retrieves and caches content from your
origin server (e.g., your website) and serves it to users from the nearest point of
presence (POP). This reduces load times by delivering content from a location
closest to the user rather than your origin server.
How do I configure my origin server for a
Vultr CDN Pull Zone?
To configure your origin server, simply provide your server's URL when creating
the Pull Zone in the Vultr Console. The CDN will automatically pull content from
this URL and distribute it across its global network.
Can I use a custom domain with a Vultr CDN
Pull Zone?
Yes, you can use a custom domain with a Vultr CDN Pull Zone. You will need to
create a CNAME record pointing to your Vultr CDN URL and upload your SSL

certificates through the "Custom Domain" tab in the Vultr CDN management
interface.
How often does the Vultr CDN Pull Zone
cache update?
The Vultr CDN Pull Zone automatically updates its cache every 24 hours if no
requests are made to the origin server. You can also manually purge the cache
at any time to fetch the latest content from your origin server.
What performance features can I enable on
a Vultr CDN Pull Zone?
Vultr CDN Pull Zones allow you to enable various performance features,
including Gzip compression to reduce file sizes, CORS policies to share
resources across domains, and bot-blocking features to protect your content
from unauthorized access.
How can I monitor the performance of my
Vultr CDN Pull Zone?
You can monitor your Vultr CDN Pull Zone’s performance by accessing the
Overview tab in the Vultr CDN management interface. This tab provides real-time data on CDN activity, server traffic, hit ratios, and the usage of different
regions.

Can I use multiple Vultr CDN Pull Zones with
the same origin server?
Yes, you can create multiple Vultr CDN Pull Zones for the same origin server.
This can be useful for segmenting traffic, testing configurations, or applying
different performance settings to different types of content.
How do I refresh the content cached in my
Vultr CDN Pull Zone?
To refresh the cached content, you can manually purge the cache by clicking
the "Purge CDN" button in the Vultr CDN management page. This will clear the
existing cache and force the CDN to fetch the latest content from your origin
server.
What should I consider when choosing Vultr
CDN locations?
When choosing Vultr CDN locations, consider your audience's geographical
distribution. Enable regions closest to your users to reduce latency and improve
load times. Also, review the region usage rates to understand the costs
associated with different locations.
How do Vultr CDN Pull Zones impact my
website’s SEO?
Vultr CDN Pull Zones can positively impact your website’s SEO by improving
load times, which is a key factor in search engine rankings. Faster content

delivery can lead to better user experiences, potentially lowering bounce rates
and increasing dwell time on your site.
How can I manage Vultr CDN Pull Zones
using the Vultr CLI and API?
You can manage Vultr CDN Pull Zones using the Vultr CLI and API by accessing
commands and endpoints specifically designed for Pull Zones. These tools allow
you to create, update, delete, and configure Pull Zones, and enabling
performance features directly from the command line or through API requests.

Push Zone
Manage and configure Vultr Push Zones to efficiently distribute content to
edge servers for improved website performance and reduced origin load.

Provisioning
The process of setting up and configuring a new server or service to
make it ready for use.

How to Provision Vultr CDN Push
Zones
Introduction
Vultr CDN Push Zones allow you to directly upload your content to the CDN,
which is then stored on Vultr's edge servers for rapid delivery to users around
the world. With 32 global locations available, you can ensure that your content
is served quickly and efficiently from the nearest edge server. Additionally, Push
Zones support custom domain functionality, enabling you to serve content
under your own branded domain while leveraging the performance and
scalability of Vultr’s CDN.
Follow this guide to provision Vultr CDN Push Zones on your Vultr account using
the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Push Zones.
2. Click Add CDN Push Zone.
3. Provide a Label.
4. Optional: Enable features such as Cross-Origin Resource Sharing
(CORS), Gzip, Block AI Bots, and Block Potentially Malicious Bots.
5. Optional: Provide a Custom Domain along with its Domain-validated
Certificate(SSL/TLS) and Secret Key files.
6. Click Add CDN Push Zone.
Vultr API
1. Send a POST request to the Create CDN Push Zones endpoint to create a
CDN Push Zone subscription.

```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "label": "{label}",
        "vanity_domain": "{custom-vanity-domain}",
        "ssl_cert": "{BASE64_ENCODED_SSL_CERT_CONTENT}",
        "ssl_cert_key": "{BASE64_ENCODED_SSL_KEY_CONTENT}",
        "cors": false,
        "gzip": false,
        "block_ai": false,
        "block_bad_bots": false
    }'
```
2. Send a GET  request to the List CDN Push Zones endpoint to list all the
available Vultr CDN Push Zone subscriptions.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. Create a CDN Push Zone subscription.
```bash
$ vultr-cli cdn push create --label "<label>"
```
Run vultr-cli cdn push create --help  to view additional options for enabling
features like Cross-Origin Resource Sharing (CORS), Gzip, Block AI
Bots, and Block Potentially Malicious Bots.
2. List all available CDN Push Zone subscriptions.

```bash
$ vultr-cli cdn push list
```

Features
A comprehensive overview of Vultrs platform capabilities and service
offerings.

Block AI Bots
A security feature that helps protect your website from automated bots
and AI crawlers by implementing specialized blocking techniques.

How to Enable AI Bot Blocking for
Vultr CDN Push Zones
Introduction
AI Bot Blocking in Vultr CDN Push Zones helps protect your content by
preventing unwanted AI bots from accessing your site. This feature ensures that
your bandwidth is used efficiently by real users, safeguarding your site from
harmful traffic and potential abuse. By enabling AI Bot blocking, you maintain
optimal performance and security for your content delivery.
Follow this guide to enable the AI Bot blocking feature for Vultr CDN Push Zones
on your Vultr account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Push Zones.
2. Click your target CDN Push Zone subscription to open its management
page.
3. Click Features.
4. Select block_ai and click Update Features.
Vultr API
1. Send a GET request to the List CDN Push Zones endpoint and note the
target Push Zone subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update CDN Push Zone endpoint to enable AI
Bot blocking feature for your target Push Zone subscription.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones/{pushzone-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "block_ai": true
    }'
```
Vultr CLI
1. List all available CDN Push Zone subscriptions and note the target Push
Zone subscription's ID.
```bash
$ vultr-cli cdn push list
```
2. Enable AI Bot blocking feature for your target Push Zone subscription.
```bash
$ vultr-cli cdn push update <pushzone-id> --block-ai

Block Bad Bots
A security feature that prevents malicious automated traffic from
accessing your website by identifying and blocking harmful bot activity.
```

How to Enable Bad Bot Blocking for
Vultr CDN Push Zones
Introduction
Bad Bot Blocking in Vultr CDN Push Zones helps protect your site by blocking
unwanted bots from accessing your content. This feature reduces unnecessary
traffic and ensures that only legitimate users can interact with your content,
enhancing the security and efficiency of your site. By enabling Bad Bot blocking,
you safeguard your resources and maintain a smoother experience for genuine
visitors.
Follow this guide to enable the Bad Bot blocking feature for Vultr CDN Push
Zones on your Vultr account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Push Zones.
2. Click your target CDN Push Zone subscription to open its management
page.
3. Click Features.
4. Select block_bad_bots and click Update Features.
Vultr API
1. Send a GET request to the List CDN Push Zones endpoint and note the
target Push Zone subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update CDN Push Zone endpoint to enable
Bad Bot blocking feature for your target Push Zone subscription.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones/{pushzone-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "block_bad_bots": true
    }'
```
Vultr CLI
1. List all available CDN Push Zone subscriptions and note the target Push
Zone subscription's ID.
```bash
$ vultr-cli cdn push list
```
2. Enable Bad Bot blocking feature for your target Push Zone subscription.
```bash
$ vultr-cli cdn push update <pushzone-id> --block-bad-bots

CORS
Cross-Origin Resource Sharing (CORS) is a security feature that controls
how web resources on one domain can be requested from another
domain.
```

How to Enable CORS Protection for
Vultr CDN Push Zones
Introduction
CORS Protection in Vultr CDN Push Zones allows you to manage and control
which websites can access your content. This feature enhances the security of
your resources by preventing unauthorized sites from making requests,
ensuring that your content is only shared with approved and trusted domains.
By configuring CORS protection, you maintain control over how your content is
accessed and used across the web.
Follow this guide to enable the CORS protection feature for Vultr CDN Push
Zones on your Vultr account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Push Zones.
2. Click your target CDN Push Zone subscription to open its management
page.
3. Click Features.
4. Select cors and click Update Features.
Vultr API
1. Send a GET request to the List CDN Push Zones endpoint and note the
target Push Zone subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update CDN Push Zone endpoint to enable
cors protection feature for your target Push Zone subscription.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones/{pushzone-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "cors": true
    }'
```
Vultr CLI
1. List all available CDN Push Zone subscriptions and note the target Push
Zone subscription's ID.
```bash
$ vultr-cli cdn push list
```
2. Enable cors protection feature for your target Push Zone subscription.
```bash
$ vultr-cli cdn push update <pushzone-id> --cors

GZIP
A compression method that reduces file sizes to improve website loading
speeds and bandwidth usage.
```

How to Enable GZIP Compression
for Vultr CDN Push Zones
Introduction
GZIP Compression in Vultr CDN Push Zones reduces the size of your content
before it is delivered to users. By compressing your data, this feature enhances
the efficiency of data transfer, leading to faster load times and improved overall
site performance. Enabling GZIP compression helps optimize bandwidth usage
and ensures a quicker, more responsive experience for your users.
Follow this guide to enable the GZIP compression feature for Vultr CDN Push
Zones on your Vultr account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Push Zones.
2. Click your target CDN Push Zone subscription to open its management
page.
3. Click Features.
4. Select gzip and click Update Features.
Vultr API
1. Send a GET request to the List CDN Push Zones endpoint and note the
target Push Zone subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update CDN Push Zone endpoint to enable
gzip compression feature for your target Push Zone subscription.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones/{pushzone-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "gzip": true
    }'
```
Vultr CLI
1. List all available CDN Push Zone subscriptions and note the target Push
Zone subscription's ID.
```bash
$ vultr-cli cdn push list
```
2. Enable gzip compression feature for your target Push Zone subscription.
```bash
$ vultr-cli cdn push update <pushzone-id> --gzip
```

Management
Tools and features for managing your Vultr account, resources, and
infrastructure.

Monitor
Track server performance metrics, set alerts, and visualize resource
usage through Vultrs integrated monitoring system.

How to Monitor Vultr CDN Push
Zones
Introduction
Vultr CDN's Monitoring Tools provide real-time insights into traffic metrics,
allowing you to closely track the performance of content delivery across your
network. These tools enable you to monitor key performance indicators, analyze
traffic patterns, and identify trends that can help optimize your CDN usage. By
utilizing these insights, you can make informed decisions to improve content
delivery efficiency and address any issues proactively.
Follow this guide to view and analyze the Vultr CDN Push Zone metrics on your
Vultr account using the Vultr Console.
1. Navigate to Products, click CDN, and then click Push Zones.
2. Click your target CDN Push Zone subscription to open its management
page.
3. Click Usage Graphs to view the traffic metrics.
4. Under Network Monitors, select a time Range (Last 24 hours, Last
Week, or Last Month) from the drop down menu, and choose a region from
the list of active regions available for your CDN Push Zone subscription.
5. Analyze the Usage Graphs:
- Hit Ratio: Measures the percentage of requests served from the
cache versus those fetched from the origin. A higher hit ratio
indicates better caching efficiency.
- Server Traffic: Displays the amount of data transferred through the
CDN, helping you track bandwidth usage.

Active Regions
A list of geographical regions where Vultr services are currently available
for deployment.

How to Manage Active Regions for
Vultr CDN Push Zones
Introduction
Active Regions in Vultr CDN Push Zones allow you to specify the regions where
your content is stored and delivered. With 32 global locations to choose from,
this feature ensures that your data is readily available and served quickly from
multiple edge servers, enhancing performance and reducing latency for users in
those regions. By updating the active regions, you can optimize content
delivery and improve the user experience across various geographic areas.
Follow this guide to update the active regions for a Vultr CDN Push Zone
subscription on your Vultr account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Push Zones.
2. Click your target CDN Push Zone subscription to open its management
page.
3. Click Regions.
4. Select any region in which you want a Push Zone.
5. Deselect any region in which you do not want a Push Zone.
Vultr API
1. Send a GET request to the List CDN Push Zones endpoint and note the
target Push Zone subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the List Regions endpoint and note your target
region ID.
```bash
$ curl "https://api.vultr.com/v2/regions" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a PUT  request to the Update CDN Push Zone endpoint to update
the Push Zone regions.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones/{pushzone-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "regions": [
            "{region_1_id}",
            "{region_2_id}",
            "{region_3_id}"
        ]
    }'
```
Vultr CLI
1. List all available CDN Push Zone subscriptions and note the target Push
Zone subscription's ID.
```bash
$ vultr-cli cdn push list
```
2. List all Vultr regions and note your target region ID.
```bash
$ vultr-cli regions list
```
3. Update the regions for the target Push Zone subscription.
```bash
$ vultr-cli cdn push update <pushzone-id> --regions
"<region_1_id>,<region_2_id>,<region_3_id>"
```

CDN Info
Provides information about Vultrs Content Delivery Network (CDN) service
for accelerating content distribution globally.

How to Retrieve CDN Information
for Vultr CDN Push Zones
Introduction
Vultr CDN simplifies access to your distributed content by providing a unique
CDN URL. This URL routes requests through Vultr's global network of 32
locations, ensuring that your content is delivered quickly and efficiently from
the nearest edge server. By using this CDN URL, you optimize content delivery
performance and reduce latency for users around the world.
Follow this guide to retrieve the Vultr CDN URL on your Vultr account using the
Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Push Zones.
2. Click your target CDN Push Zone subscription to open its management
page.
3. Click Overview.
4. Under CDN Information, locate CDN URL, and copy it for further use.
Vultr API
1. Send a GET request to the List CDN Push Zones endpoint and note the
target Push Zone subscription's CDN URL.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available CDN Push Zone subscriptions and note the target Push
Zone subscription's CDN URL.
```bash
$ vultr-cli cdn push list

Files
A storage service for organizing and managing your files within the Vultr
platform.
```

How to Upload Files to Vultr CDN
Push Zones
Introduction
Uploading Files to Vultr CDN Push Zones enables you to directly transfer and
store your content within the CDN infrastructure. Once your files are uploaded,
they are distributed and cached across multiple edge servers within the Push
Zones. This ensures that your content is delivered quickly and reliably to users
from various locations worldwide. By utilizing this feature, you enhance the
efficiency and performance of your content delivery, providing a better user
experience through reduced load times and consistent availability.
Follow this guide to upload files to Vultr CDN Push Zones on your Vultr account
using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Push Zones.
2. Click your target CDN Push Zone subscription to open its management
page.
3. Click Files.
4. Click Upload File.
5. Choose a File and provide a File Name.
6. Click Upload File.
7. To delete a file, click on the Delete File icon.
8. Check the Yes, destroy this file box in the confirmation prompt, and click
Delete File to permanently delete the uploaded file.

Vultr API
1. Send a GET  request to the List CDN Push Zones endpoint and note the
target Push Zone subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a POST  request to the Create CDN Push Zone File Upload
endpoint to generate an upload endpoint for the target CDN Push Zone
subscription.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones/{pushzone-id}/files" \
-X POST \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "name": "{filename.ext}",
        "size": {file_size_bytes}
    }'
```
3. Send a POST  request to the upload endpoint URL returned in the API
response. Pass all inputs as form-data fields with the exact same keys and
values. Additionally, add a field named file , which contains the file to be
uploaded. This will successfully upload the file to the target CDN Push Zone
subscription.
```bash
$ curl "{upload_endpoint_URL}" \
-X POST \
-F "acl=public-read" \
-F "key={CDN_file_path}" \

-F "X-Amz-Credential={X_Amz_Credential}" \
-F "X-Amz-Algorithm={X_Amz_Algorithm}" \
-F "X-Amz-Date={X_Amz_Date}" \
-F "Policy={policy_string}" \
-F "X-Amz-Signature={X_Amz_Signature}" \
-F "file={filename.ext}"
```
4. Send a GET  request to the List CDN Push Zone Files endpoint to list all
available files in the target Push Zone subscription.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones/{pushzone-id}/files" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
5. Send a DELETE  request to the Delete CDN Push Zone File endpoint to
delete a file from the target Push Zone subscription.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones/{pushzone-id}/files/{filename.ext}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available CDN Push Zone subscriptions and note the target Push
Zone subscription's ID.
```bash
$ vultr-cli cdn push list
```
2. Create a CDN Push Zone upload endpoint.

```bash
$ vultr-cli cdn push create-endpoint <pushzone-id> --name
"<filename.ext>" --size <file_size_bytes>
```
Note
The Vultr CLI supports creating a CDN Push Zone upload endpoint. To
complete the upload, use the details from the response to push the file
to the target Push Zone subscription via an HTTP client like cURL or
another appropriate method.
3. List all available files in the target Push Zone subscription.
```bash
$ vultr-cli cdn push list-files <pushzone-id>
```
4. Delete a file from the target Push Zone subscription.
```bash
$ vultr-cli cdn push delete-file <pushzone-id> <filename.ext>
```

Delete
Permanently removes the selected resource from your Vultr account.

How to Delete Vultr CDN Push
Zones
Introduction
Deleting a Vultr CDN Push Zone subscription is a straightforward process that
removes the associated caching and distribution configurations for your
content. This action will terminate the CDN subscription, clearing any cached
data and stopping the distribution of your content through Vultr's network. By
deleting the Push Zones, you effectively discontinue the CDN's role in serving
and caching your content.
Follow this guide to delete the Vultr CDN Push Zone subscription from your Vultr
account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Push Zones.
2. Click your target CDN Push Zone subscription to open its management
page.
3. Click the delete icon in the top-right corner of the management page.
4. Check the Yes, destroy this CDN box in the confirmation prompt, and
click Delete CDN to permanently delete the target CDN Push Zone
subscription.
Vultr API
1. Send a GET request to the List CDN Push Zones endpoint and note the
target Push Zone subscription's ID.

```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete CDN Push Zone endpoint to delete
the target Push Zone subscription.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones/{pushzone-id}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all available CDN Push Zone subscriptions and note the target Push
Zone subscription's ID.
```bash
$ vultr-cli cdn push list
```
2. Delete the target Push Zone subscription.
```bash
$ vultr-cli cdn push delete <pushzone-id>
```

Custom Domain
Configure a personalized web address for your Vultr application instead of
using the default domain.

How to Manage Custom Domain for
Vultr CDN Push Zones
Introduction
Custom domain functionality in Vultr CDN Push Zones allows you to serve your
content through a domain name of your choice, providing a consistent and
branded experience for your users. By configuring a custom domain, you can
enhance your content delivery with a personalized URL, improving trust and
recognition for your brand. This feature ensures that your content is delivered
efficiently while maintaining a seamless integration with your existing domain
setup.
Note
To use a custom domain (or vanity domain) with your Vultr CDN Push Zone,
you need to create a CNAME DNS record for your domain through your domain
provider. This CNAME record should point to the default CDN domain that is
automatically generated when you create your Vultr CDN Push Zone
subscription. After setting up the CNAME record, make sure that the DNS
changes have propagated successfully before configuring your custom
domain in the Vultr CDN settings.
Follow this guide to configure a custom domain for Vultr CDN Push Zones on
your Vultr account using the Vultr Console or API.
Vultr Console
1. Navigate to Products, click CDN, and then click Push Zones.
2. Click your target CDN Push Zone subscription to open its management
page.
3. Click Custom Domain.

4. Provide the Custom Domain and Domain-validated Certificate(SSL/
TLS) and Private Key files.
5. Click Update Custom Domain.
Vultr API
1. Send a GET  request to the List CDN Push Zones endpoint and note the
target Push Zone subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update CDN Push Zone endpoint to update
the custom domain.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones/{pushzone-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "vanity_domain": "{custom_vanity_domain}",
        "ssl_cert": "BASE64_ENCODED_SSL_CERT_CONTENT",
        "ssl_cert_key": "BASE64_ENCODED_SSL_KEY_CONTENT"
    }'
```

Update
Modify your servers configuration, operating system, or resources to
meet changing requirements.

How to Update Vultr CDN Push
Zones
Introduction
Updating the label of a Vultr CDN Push Zone is a straightforward process that
enables you to better organize and manage your CDN configuration. This
process enhances the clarity of your CDN management and ensures your Push
Zones are consistently aligned with your workflow.
Follow this guide to update the label of a Vultr CDN Push Zone subscription on
your Vultr account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click CDN, and then click Push Zones.
2. Click your target CDN Push Zone subscription to open its management
page.
3. Click Overview.
4. Under CDN Information, locate the Name field.
5. Click the current name of the Push Zone subscription and enter a new,
appropriate name.
6. Click the check-mark icon to save the changes.
Vultr API
1. Send a GET request to the List CDN Push Zones endpoint and note the
target Push Zone subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PUT  request to the Update CDN Push Zone endpoint to update
the target Push Zone subscription's label.
```bash
$ curl "https://api.vultr.com/v2/cdns/push-zones/{pushzone-id}" \
-X PUT \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "label": "{updated_label}"
    }'
```
Vultr CLI
1. List all available CDN Push Zone subscriptions and note the target Push
Zone subscription's ID.
```bash
$ vultr-cli cdn push list
```
2. Update the target Push Zone subscription's label.
```bash
$ vultr-cli cdn push update <pushzone-id> --label
"<updated_label>"
```

FAQ
A collection of commonly asked questions and answers about Vultr
services and features.

and API? 124

Frequently Asked Questions About
Vultr CDN Push Zone
Introduction
These are the frequently asked questions for Vultr CDN Push Zones.
What is a Vultr CDN Push Zone, and how
does it work?
A Vultr CDN Push Zone allows you to manually upload and cache large static
files, such as images, videos, and software packages, directly to the CDN
storage. These files are then distributed and served from multiple points of
presence (POPs) across the globe, ensuring fast delivery to users.
When should I use a Vultr CDN Push Zone
instead of a Pull Zone?
A Push Zone is ideal for delivering large files, typically over 100 MB, that don’t
change frequently and need to be distributed across many locations. Unlike Pull
Zones, where content is automatically retrieved from your origin server, Push
Zones are best for pre-uploaded content that doesn’t rely on an origin server.

How do I upload files to a Vultr CDN Push
Zone?
To upload files to a Push Zone, navigate to the Vultr CDN management page,
click on Manage CDN, and go to the Files tab. From there, you can manually
upload files using the Upload File option. Once uploaded, the files will be
cached and distributed across Vultr's CDN locations.
Can I use a custom domain with a Vultr CDN
Push Zone?
Yes, you can use a custom domain with your Vultr CDN Push Zone. To do this,
you will need to set up a CNAME record in your DNS that points to the Vultr CDN
URL, and then configure the custom domain and SSL certificates in the "Custom
Domain" tab of the Vultr CDN management interface.
How are files distributed across the CDN in a
Push Zone?
Once you upload files to a Vultr CDN Push Zone, they are automatically cached
and distributed across multiple Vultr POPs. This ensures that users accessing
your content are served from the nearest location, reducing latency and
improving load times.
How can I manage and monitor my Vultr
CDN Push Zone?
You can manage and monitor your Push Zone through the Vultr CDN
management interface. This includes viewing file counts, monitoring usage

statistics, and checking active regions. The interface also provides tools for
uploading, deleting, and managing your cached files.
How do I update files that are already
uploaded to a Push Zone?
To update files in a Push Zone, you simply upload the new version of the file
with the same filename. The CDN will replace the old version with the new one
and propagate the update across all cached locations.
What should I consider when uploading
large files to a Push Zone?
When uploading large files, consider the time it will take for the files to be
propagated across all Vultr CDN locations. Ensure that your file names are
unique to avoid conflicts and that your internet connection is stable to prevent
upload interruptions. Additionally, review the bandwidth usage and costs
associated with delivering large files from multiple regions.
How can I manage Vultr CDN Push Zones
using the Vultr CLI and API?
To manage Vultr CDN Push Zones using the Vultr CLI and API, you can use
commands and endpoints that support uploading files, configuring CDN
settings, and monitoring zone performance. The CLI and API allow for efficient
management of file uploads, cache management, and customization of Push
Zones to ensure optimal content delivery across multiple regions.
