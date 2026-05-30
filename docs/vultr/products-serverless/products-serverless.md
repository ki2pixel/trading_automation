Serverless
Deploy and scale AI inference workloads without managing infrastructure
using Vultr's serverless computing platform.

Inference
Deploy and manage AI inference workloads on Vultr's infrastructure with
optimized performance and scalability.

Provisioning
A process that prepares and configures a server or service for use after
initial deployment.

How to Provision Vultr Serverless
Inference
Introduction
Vultr Serverless Inference is an efficient AI model hosting service that provides
seamless scalability and reduced operational complexity for Generative AI
applications. With reliable performance across six continents, Vultr ensures
minimal latency for AI models while meeting stringent security and data
compliance requirements.
Follow this guide to provision a Vultr Serverless Inference subscription using the
Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click Serverless, and then click Inference.
2. Click Add Serverless Inference.
3. Provide a Label, acknowledge the list of supported models and the
charges note, and click Add Serverless Inference.
Vultr API
1. Send a POST request to the Create Serverless Inference endpoint to
create a Serverless Inference subscription.
```bash
$ curl "https://api.vultr.com/v2/inference" \
-X POST \

-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "label" : "example-inference"
    }'
```
2. Send a GET  request to the List Serverless Inference endpoint to list all
the available Serverless Inference subscriptions.
```bash
$ curl "https://api.vultr.com/v2/inference" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. Create a Serverless Inference subscription.
```bash
$ vultr-cli inference create --label example-inference
```
2. List all the available Serverless Inference subscriptions available.
```bash
$ vultr-cli inference list
```

Management
Tools and features for managing your Vultr infrastructure, including
access controls, monitoring, and account administration.

Usage
Track and analyze your resource consumption, billing details, and usage
patterns across your Vultr infrastructure.

Chat

How to Use the Chat Endpoint in
Vultr Serverless Inference
Introduction
Vultr Serverless Inference chat endpoint enables users to engage in chat
conversations with Large Language Models (LLMs). This service allows for real-time interaction, leveraging advanced AI capabilities to facilitate dynamic and
responsive communication. The endpoint also supports tool calling, letting
models invoke defined functions (for example, fetch live data or call an API)
during a conversation to produce data-driven responses. By integrating this
endpoint, users can enhance their applications with sophisticated
conversational AI, improving user experience and operational efficiency.
Follow this guide to utilize the chat endpoint on your Vultr account using the
Vultr Console or API.
Vultr Console
1. Navigate to Products, click Serverless, and then click Inference.
2. Click your target inference subscription to open its management page.
3. Open the Chat page.
4. Select a preferred model.
5. Provide Max Tokens value.
6. Send a message in the chat window.
7. Click History to view chat history.
8. Click New Conversation to create a chat window.

Vultr API
Chat with a Model Using the API
1. Send a GET  request to the List Serverless Inference endpoint and note
the target inference subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/inference" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Serverless Inference endpoint and note the
target inference subscription's API key.
```bash
$ curl "https://api.vultr.com/v2/inference/{inference-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a GET  request to the List Models endpoint and note the preferred
inference model's ID.
```bash
$ curl "https://api.vultrinference.com/v1/models" \
-X GET \
-H "Authorization: Bearer ${INFERENCE_API_KEY}"
```
4. Send a POST  request to the Create Chat Completion endpoint to chat
with the prefered Large Language Model.
```bash
$ curl "https://api.vultrinference.com/v1/chat/completions" \
-X POST \
-H "Authorization: Bearer ${INFERENCE_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
"model": "{model-id}",
"messages": [
{
"role": "user",
"content": "{user-input}"
}
],
"max_tokens": 512
}'
```
Visit the Create Chat Completion API page to view additional attributes
you can apply for greater control when interacting with the preferred
inference model.
Use Tool Calling with the Chat Endpoint
Note
Tool calling is currently supported only on the kimi-k2-instruct model.
1. Define your tools using the "tools" parameter in the request body.
2. Set "tool_choice" to "auto" , "required" or "none" to control when the model
triggers a tool call.
3. Send a POST request to the Create Chat Completion endpoint to send a
message that can trigger tool calls.
```bash
$ curl "https://api.vultrinference.com/v1/chat/completions" \
-X POST \
-H "Authorization: Bearer ${INFERENCE_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
"model": "kimi-k2-instruct",
"messages": [
{ "role": "user", "content": "Ask a question that

requires a tool response." }
],
"tools": [
{
"type": "function",
"function": {
"name": "function_name",
"description": "Briefly describe the
purpose of the function.",
"parameters": {
"type": "object",
"properties": {
"parameter_name": {
"type": "string",
"description": "Describe the
expected input parameter."
}
},
"required": ["parameter_name"]
}
}
}
],
"tool_choice": "auto"
}'
The model responds with a structured tool call such as:
{
"role": "assistant",
"tool_calls": [
{
"type": "function",
"function": {
"name": "function_name",
"arguments": "{\"parameter_name\": \"example_value\"}"
}
}
]
}
You can execute this function locally or via API, then send the output back
to the model in a second request.

For a complete implementation example, see How to Use Tool Calling
with Vultr Serverless Inference.

Prompt
```

How to Use the Prompt Endpoint in
Vultr Serverless Inference
Introduction
Vultr Serverless Inference prompt endpoint allows users to send a single prompt
to an AI model for generating responses. This service supports interactive and
dynamic AI interactions, enabling users to obtain specific outputs based on their
prompts and integrate these responses into their applications effectively. By
using this feature, you can enhance your application's responsiveness and
adaptability to user inputs, providing more personalized and relevant outputs.
Follow this guide to utilize the prompt endpoint on your Vultr account using the
Vultr Console.
1. Navigate to Products, click Serverless, and then click Inference.
2. Click your target inference subscription to open its management page.
3. Open the Prompt page.
4. Select a preferred model.
5. Provide values for Max Tokens, Seed, Temperature, Top-k and Top-p.
6. Provide a prompt and click on Prompt.
7. Click Reset to provide a new prompt.

Text-to-Speech

Text-to-Speech Product Documentation
Text-to-Speech Product Documentation
How to Use the Text-to-Speech
Endpoint in Vultr Serverless
Inference
Introduction
Vultr Serverless Inference text-to-speech endpoint converts text into spoken
audio using advanced AI models. This service enables users to integrate high-quality, natural-sounding speech synthesis into their applications, enhancing
accessibility and user engagement through seamless audio output. By
leveraging this feature, you can provide an auditory experience that is both
clear and engaging, making your applications more user-friendly and inclusive.
Follow this guide to utilize the text-to-speech endpoint on your Vultr account
using the Vultr Console or API.
Vultr Console
1. Navigate to Products, click Serverless, and then click Inference.
2. Click your target inference subscription to open its management page.
3. Open the Text-to-Speech page.
4. Select a preferred model.
5. Select a preferred voice.
6. Provide an input and click on Prompt.
7. Click Reset to provide a new input.

Text-to-Speech Product Documentation
Vultr API
1. Send a GET  request to the List Serverless Inference endpoint and note
the target inference subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/inference" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Serverless Inference endpoint and note the
target inference subscription's API key.
```bash
$ curl "https://api.vultr.com/v2/inference/{inference-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a GET  request to the List Audio Models endpoint and note the
preferred audio inference model's ID.
```bash
$ curl "https://api.vultrinference.com/v1/audio/models" \
-X GET \
-H "Authorization: Bearer ${INFERENCE_API_KEY}"
```
4. Send a GET  request to the List Audio Voices endpoint and note the
preferred voice for the chosen model.
```bash
$ curl "https://api.vultrinference.com/v1/audio/voices" \
-X GET \
-H "Authorization: Bearer ${INFERENCE_API_KEY}"

Text-to-Speech Product Documentation
```
5. Send a POST  request to the Create Speech endpoint to generate speech
from the input text.
```bash
$ curl "https://api.vultrinference.com/v1/audio/speech" \
-X POST \
-H "Authorization: Bearer ${INFERENCE_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "model": "{model-id}",
        "input": "{user-input}",
        "voice": "{selected-voice}"
    }' \
    --output "{output-path}/output.wav"

Connection
Establish connectivity between your Vultr resources and external
networks or services.
```

How to Retrieve the API Key for
Vultr Serverless Inference
Introduction
To utilize the Vultr Serverless Inference subscription, users must obtain an API
key. This key is essential for secure access to the inference capabilities,
enabling efficient integration and management of AI workloads. Having the API
key ensures that your interactions with the Vultr Serverless Inference
subscription are both authenticated and authorized.
Follow this guide to retrieve the API key for Serverless Inference subscription on
your Vultr account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click Serverless, and then click Inference.
2. Click your target inference subscription to open its management page.
3. In the overview page, copy the API Key. API key is necessary to send any
request to the inference endpoints.
Vultr API
1. Send a GET request to the List Serverless Inference endpoint and note
the target inference subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/inference" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Serverless Inference endpoint and note the
target inference subscription's API key.
```bash
$ curl "https://api.vultr.com/v2/inference/{inference-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all the inference subscriptions available and note the target inference
subscription's ID.
```bash
$ vultr-cli inference list
```
2. Get the API key from the target subscription.
```bash
$ vultr-cli inference get <inference-id>
```

Delete
Permanently removes the selected resource from your Vultr account.

How to Delete Vultr Serverless
Inference
Introduction
Deleting the Vultr Serverless Inference subscription involves removing the
entire inference subscription from your account. This process is important for
managing resource allocation and avoiding unnecessary costs. Ensuring that
unused subscriptions are properly deleted helps maintain an efficient and cost-effective cloud environment.
Follow this guide to delete the Serverless Inference subscription on your Vultr
account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click Serverless, and then click Inference.
2. Click your target inference subscription to open its management page.
3. Click delete icon on the top right of the management page.
4. Click Close Serverless Inference Subscription in the confirmation
prompt to permanently delete the target inference subscription.
Vultr API
1. Send a GET request to the List Serverless Inference endpoint and note
the target inference subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/inference" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a DELETE  request to the Delete Serverless Inference endpoint to
delete the target inference subscription.
```bash
$ curl "https://api.vultr.com/v2/inference/{inference-id}" \
-X DELETE \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all the inference subscriptions available and note the target inference
subscription's ID.
```bash
$ vultr-cli inference list
```
2. Delete the target inference subscription.
```bash
$ vultr-cli inference delete <inference-id>
```

Monitor
A system for tracking server performance metrics, resource utilization,
and setting up alerts for your Vultr infrastructure.

How to Monitor Vultr Serverless
Inference
Introduction
Monitoring the Vultr Serverless Inference subscription is essential for
maintaining the performance and cost-efficiency of your AI deployments. By
tracking the usage of various AI workloads, such as "Prompt, Chat, Text-to-Speech" and "RAG Chat Completion," you can gain valuable insights into
resource consumption, optimize performance, and prevent potential
bottlenecks. This proactive monitoring ensures that your AI applications run
smoothly, delivering consistent and reliable results while keeping operational
costs under control.
Follow this guide to monitor the usage of Serverless Inference on your Vultr
account using the Vultr Console, API, or CLI.
Vultr Console
1. Navigate to Products, click Serverless, and then click Inference.
2. Click your target inference subscription to open its management page.
3. Open the Usage page.
4. View the usage statistics for all inference endpoints.
Vultr API
1. Send a GET request to the List Serverless Inference endpoint and note
the target inference subscription's ID.

```bash
$ curl "https://api.vultr.com/v2/inference" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Serverless Inference Usage Information
endpoint to retrieve usage details about all inference endpoints.
```bash
$ curl "https://api.vultr.com/v2/inference/{inference-id}/
usage" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
Vultr CLI
1. List all the inference subscriptions available and note the target inference
subscription's ID.
```bash
$ vultr-cli inference list
```
2. Get the target inference subscription's usage.
```bash
$ vultr-cli inference usage get <inference-id>

Health Checks
A monitoring feature that regularly tests your services to verify theyre
operational and can automatically restart failing instances.
```

How to Monitor Health Checks for
Vultr Serverless Inference
Introduction
Health Checks on Vultr Serverless Inference ensures that your deployments
remain operational and responsive. By periodically checking its status, you can
proactively detect potential issues and maintain seamless AI performance.
Follow this guide to check the status of Serverless Inference subscription using
the Vultr API.
1. Send a GET  request to the List Serverless Inference endpoint and note
the target inference subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/inference" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Serverless Inference endpoint and note the
target inference subscription's API key.
```bash
$ curl "https://api.vultr.com/v2/inference/{inference-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a GET  request to the Health Check endpoint to view the current
status of the target inference subscription.
```bash
$ curl "https://api.vultrinference.com/v1/health" \
-X GET \
-H "Authorization: Bearer ${INFERENCE_API_KEY}"
```

Update
Modify your servers configuration or settings to apply changes or
improvements.

How to Update Vultr Serverless
Inference
Introduction
Updating a Serverless Inference subscription changes its label without affecting
the underlying deployment. This helps streamline resource organization and
improves clarity when managing multiple inference subscriptions.
Follow this guide to update a Serverless Inference subscription using the Vultr
API or CLI.
Vultr API
1. Send a GET  request to the List Serverless Inference endpoint and note
the target inference subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/inference" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a PATCH  request to the Update Serverless Inference endpoint to
update the label of the target inference subscription.
```bash
$ curl "https://api.vultr.com/v2/inference/{inference-id}" \
-X PATCH \
-H "Authorization: Bearer ${VULTR_API_KEY}" \
-H "Content-Type: application/json" \
--data '{

"label" : "example-inference-updated"
}'
```
Vultr CLI
1. List all the inference subscriptions available and note the target inference
subscription's ID.
```bash
$ vultr-cli inference list
```
2. Update the label of the target inference subscription.
```bash
$ vultr-cli inference update <inference-ID> --label example-inference-updated
```

FAQ
Frequently asked questions and answers about Vultrs products, services,
and platform features.

Frequently Asked Questions (FAQs)
About Vultr Serverless Inference
Introduction
These are the frequently asked questions for Vultr Serverless Inference.
Can I run inference workloads for models
other than large language models on Vultr
Serverless Inference?
Vultr Serverless Inference supports a growing catalog of production-ready
models across multiple categories, including large language models, chat-optimized models, code generation models, text-to-speech models, and image
generation models. The available model list is regularly updated as new models
are added. To view the current supported models, navigate to the Serverless
Inference section in the Vultr Console and check the model selector in the
Prompt tab.
How do I monitor the usage and cost of my
Vultr serverless inference subscription?
You can monitor your usage and costs by navigating to the "Usage" tab of your
Vultr Serverless Inference subscription in the Vultr Console. Here, you will find
details on your current token usage, overage, and any associated costs. You can
also view your API key and other subscription details in the "Overview" tab.

Can I integrate Vultr serverless inference
with my existing ML pipeline?
Yes, you can integrate Vultr Serverless Inference with your existing machine
learning pipeline. To do this, replace your current inference API URL (such as
OpenAI's base API URL) with Vultr’s API URL. Then, use your Vultr API key for
authentication to seamlessly incorporate Vultr Serverless Inference into your
workflow.
How do I regenerate my Vultr serverless
Inference API key?
You can regenerate your Vultr Serverless Inference API key from the Overview
page in the Vultr Console. This will invalidate the previous API key and generate
a new one for enhanced security.
Why am I not getting high-quality outputs
from Vultr serverless inference?
The quality of the outputs from Vultr Serverless Inference depends on the
machine learning model you are using. If the outputs are not meeting your
expectations, consider trying a different model or refining your prompts. Vultr
provides the infrastructure, but the model's performance is a key factor in the
output quality.

Is there a way to test inference before
committing to a large workload?
Yes, you can test inference workloads by using the "Prompt" tab in the Vultr
Serverless Inference section of the Vultr Console. This allows you to input
prompts, select a model, and adjust settings such as max tokens and
temperature to see how the model responds before running larger workloads.
How secure is my data when using Vultr
serverless inference?
Vultr takes data security seriously. All data transmitted to and from Vultr
Serverless Inference is encrypted, and the subscription is designed with security
best practices to ensure that your data and workloads are protected.

Vector Store
A managed database service optimized for storing and retrieving vector
embeddings to power AI applications and semantic search.

Create Collections
Organize and manage related resources together for improved
administration and access control.

How to Create Vector Store
Collections
Introduction
A vector store is a structured repository for storing and retrieving high-dimensional vector embeddings. The collections within a vector store enable
fast similarity searches, making them useful for Retrieval-Augmented
Generation (RAG) and AI applications.
Follow this guide to create a vector store collection on Vultr Serverless Inference
using the Vultr API.
1. Send a GET  request to the List Serverless Inference endpoint and note
the target inference subscription's ID.
```bash
$ curl "https://api.vultr.com/v2/inference" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
2. Send a GET  request to the Serverless Inference endpoint and note the
target inference subscription's API key.
```bash
$ curl "https://api.vultr.com/v2/inference/{inference-id}" \
-X GET \
-H "Authorization: Bearer ${VULTR_API_KEY}"
```
3. Send a POST  request to the Create Collection endpoint to create a vector
store collection.

```bash
$ curl "https://api.vultrinference.com/v1/vector_store" \
-X POST \
-H "Authorization: Bearer ${INFERENCE_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "name": "{collection-name}"
    }'
```
4. Send a GET  request to the List Collections endpoint to list all the
available vector store collections.
```bash
$ curl "https://api.vultrinference.com/v1/vector_store" \
-X GET \
-H "Authorization: Bearer ${INFERENCE_API_KEY}"

Manage Collections
Organize and manage groups of related resources for easier
administration and access control.
```

How to Manage Vector Store
Collections
Introduction
Managing vector store collections helps to keep your data organized and
accessible. You can retrieve collection details, update collection names, or
delete collections when they are no longer needed.
Follow this guide to manage vector store collections on Vultr Serverless
Inference using the Vultr API.
1. Send a GET  request to the List Collections endpoint and note the target
collection's ID.
```bash
$ curl "https://api.vultrinference.com/v1/vector_store" \
-X GET \
-H "Authorization: Bearer ${INFERENCE_API_KEY}"
```
2. Send a GET  request to the Collection endpoint to retrieve target collection
details.
```bash
$ curl "https://api.vultrinference.com/v1/vector_store/
{collection-id}" \
-X GET \
-H "Authorization: Bearer ${INFERENCE_API_KEY}"
```
3. Send a PATCH  request to the Update Collection endpoint to update a
vector store collection record.

```bash
$ curl "https://api.vultrinference.com/v1/vector_store/
{collection-id}" \
-X PATCH \
-H "Authorization: Bearer ${INFERENCE_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
"name": "{updated-collection-name}"
}'
```
4. Send a DELETE request to the Delete Collection endpoint to delete the
target vector store collection.
```bash
$ curl "https://api.vultrinference.com/v1/vector_store/
{collection-id}" \
-X DELETE \
-H "Authorization: Bearer ${INFERENCE_API_KEY}"

Add Collection Items
A feature that allows you to add new resources to an organized group of
related Vultr services or products.
```

How to Add an Item to Vector Store
Collection
Introduction
A collection item is a data point within a vector store collection, containing a
unique identifier, associated metadata, and a vector representation
(embedding) of the content. These embeddings capture the semantic meaning
of the data, enabling fast and relevant retrieval that enhances tasks such as
information generation and decision-making.
Follow this guide to add an item to a vector store collection on Vultr Serverless
Inference using the Vultr API.
1. Send a GET  request to the List Collections endpoint and note the target
collection's ID.
```bash
$ curl "https://api.vultrinference.com/v1/vector_store" \
-X GET \
    -H "Authorization: Bearer ${INFERENCE_API_KEY}"
```
2. Send a POST  request to the Add Collection Item endpoint to add an item
to the target vector store collection.
```bash
$ curl "https://api.vultrinference.com/v1/vector_store/
{collection-id}/items" \
-X POST \
-H "Authorization: Bearer ${INFERENCE_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "content": "{text-to-be-embedded}",

"description": "{brief-description-of-content}"
}'
```
3. Send a GET request to the List Collection Items endpoint to list all items
in the vector store collection.
```bash
$ curl "https://api.vultrinference.com/v1/vector_store/
{collection-id}/items" \
-X GET \
-H "Authorization: Bearer ${INFERENCE_API_KEY}"

Add Collection Files
Upload and manage files within your collection to organize and share
resources with your team.
```

How to Add a File to Vector Store
Collection
Introduction
A collection file is a document that can be uploaded to a vector store collection,
allowing you to batch-import structured data efficiently. Instead of adding
individual items manually, collection files provide a way to store and manage
multiple data points in a single upload.
Follow this guide to add a file to a vector store collection on Vultr Serverless
Inference using the Vultr API.
1. Send a GET  request to the List Collections endpoint and note the target
collection's ID.
```bash
$ curl "https://api.vultrinference.com/v1/vector_store" \
-X GET \
    -H "Authorization: Bearer ${INFERENCE_API_KEY}"
```
2. Send a POST  request to the Add Collection File endpoint to add a file to
the target vector store collection.
```bash
$ curl "https://api.vultrinference.com/v1/vector_store/
{collection-id}/files" \
-X POST \
-H "Authorization: Bearer ${INFERENCE_API_KEY}" \
-H "Content-Type: multipart/form-data" \
-F "file=@{path-to-your-file}"
```
3. Send a GET request to the List Collection Files endpoint to list all files in
the vector store collection.
```bash
$ curl "https://api.vultrinference.com/v1/vector_store/
{collection-id}/files" \
-X GET \
-H "Authorization: Bearer ${INFERENCE_API_KEY}"

RAG Chat Collection
A collection of RAG (Retrieval-Augmented Generation) chat models that
enhance AI responses with relevant information from your data sources.
```

How to Use Retrieval-Augmented
Generation (RAG) with Vultr
Serverless Inference
Introduction
Retrieval-Augmented Generation (RAG) enhances AI models by combining real-time information retrieval with generative capabilities. When using Vultr
Serverless Inference, RAG enables chat models to incorporate external, domain-specific knowledge from vector store collections. This improves the contextual
accuracy of responses, reduces hallucinations, and ensures that the output is
based on the most relevant and up-to-date information. The RAG endpoint also
supports tool calling, allowing models to invoke defined functions during RAG-based interactions. This enables advanced use cases where the model can not
only retrieve external knowledge but also act on it—for example, performing
calculations, fetching live data, or calling APIs based on retrieved context.
Note
The models that support RAG-based chat completion on Vultr Serverless
Inference are: deepseek-r1-distill-qwen-32b , qwen2.5-32b-instruct ,
qwen2.5-coder-32b-instruct , llama-3.1-70b-instruct-fp8 , llama-3.3-70b-instruct-fp8 ,
deepseek-r1-distill-llama-70b , and deepseek-r1 . mistral-7B-v0.3 and mistral-nemo-instruct-2407 are not compatible with RAG.
Follow this guide to use RAG-based chat completion on Vultr Serverless
Inference using the Vultr API.

Generate RAG-Based Chat Completions
1. Send a GET  request to the List Collections endpoint and note the target
collection's ID.
```bash
$ curl "https://api.vultrinference.com/v1/vector_store" \
-X GET \
-H "Authorization: Bearer ${INFERENCE_API_KEY}"
```
2. Send a GET  request to the List Models endpoint and note the preferred
inference model's ID.
```bash
$ curl "https://api.vultrinference.com/v1/models" \
-X GET \
-H "Authorization: Bearer ${INFERENCE_API_KEY}"
```
3. Send a POST  request to the RAG Chat Completion endpoint to generate
responses using Retrieval-Augmented Generation (RAG).
```bash
$ curl "https://api.vultrinference.com/v1/chat/completions/
RAG" \
-X POST \
-H "Authorization: Bearer ${INFERENCE_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
        "collection": "{collection-id}",
        "model": "{model-id}",
        "messages": [
            {
                "role": "user",
                "content": "{user-input}"
            }
        ],

"max_tokens": 512
}'
```
Visit the RAG Chat Completion endpoint to view additional attributes you
can apply for greater control when interacting with the preferred inference
model.
Use Tool Calling with the RAG Endpoint
Note
Tool calling is currently supported only on the kimi-k2-instruct model.
1. Define your tools using the "tools" parameter in the RAG chat request
body.
2. Set "tool_choice" to "auto", "required", or "none" to control when the
model triggers a tool call.
3. Send a POST request to the RAG Chat Completion endpoint to combine RAG
retrieval and tool invocation.
```bash
$ curl "https://api.vultrinference.com/v1/chat/completions/
RAG" \
-X POST \
-H "Authorization: Bearer ${INFERENCE_API_KEY}" \
-H "Content-Type: application/json" \
--data '{
"collection": "{collection-id}",
"model": "{model-id}",
"messages": [
{ "role": "user", "content": "Ask a question that
requires external data retrieval." }
],
"tools": [
{
"type": "function",
"function": {
"name": "function_name",
"description": "Describe the purpose of

the function.",
"parameters": {
"type": "object",
"properties": {
"parameter_name": {
"type": "string",
"description": "Describe the
expected input parameter."
}
},
"required": ["parameter_name"]
}
}
}
],
"tool_choice": "auto",
"max_tokens": 512
}'
The model responds with a structured tool call, for example:
{
"role": "assistant",
"tool_calls": [
{
"type": "function",
"function": {
"name": "function_name",
"arguments": "{\"parameter_name\": \"example_value\"}"
}
}
]
}
You can execute this function locally or through an API and send the output
back to the RAG endpoint in a follow-up request to generate a complete,
context-aware response.
For detailed implementation steps and usage examples, refer to the Tool
Calling with Vultr Serverless Inference Guide.
```