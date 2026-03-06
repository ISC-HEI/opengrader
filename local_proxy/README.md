# Local Langfuse/LiteLLM proxy


This file will details the installation and usage process to allow for local Langfuse usage debugging using opencode as a agent frontend

## Structure

This proxy needs mutliple parts to work correctly. In summary :

Default usage :

OpenCode -----> OpenRouter

This proxy enables :

OpenCode -----> (Local) LiteLLM ----> OpenRouter
                    ------> (Local) LangFuse

This will not change the frontend (opencode) available to the user. But behind the curtains, it will log every usage to LangFuse, allowing for precise cost tracing and debugging.      

## Installation

The local services will be deployed with `docker compose`, so no installation needed.

For `opencode` to work with a local `LiteLLM` instance, some configuration is needed.


An example configuration is available [here](./opencode.json)

You can copy this configuration either :
- To your project root (`<project root folder>/opencode.json`) -> This imply that `opencode` must be ran from the project root folder
- The global `opencode` configuration (`$HOME/.config/opencode/opencode.json`)

Once the configuration is at the right place, launch `opencode` or `opencode web`, and normally, a custom provider should be available. Select it, and enter you `openrouter` api key here. Once this is done, you should see the model defined in `opencode.json` available. Wait until everything is installed and running before testing it :). 

Next, you can boot the web interface of `langfuse` by doing : 
```bash
docker compose up langfuse-web
```

Wait for all the sevices to start, and then head to [localhost:3000](http://localhost:3000)

Here, create an organization -> project -> API key.

> Be careful, as you can only see the secret key **one** time

Once this was done. You can copy the `env` file to `.env`. And then fill it with the corresponding API keys.

## Usage

To use this, you can start every services at the same time by using :

```bash
docker compose up
```

Once this is up, you can try using the model defined in `opencode.json` (`local_Step_3.5_Flash` by default). And while running a prompt, you should see logs pop in you `docker compose` window.

## Adding models

To add a new model, you need to edit multiples files.

First, add it in the `LiteLLM` [config](./config.yml). Here are the different parameters :

```yaml
# ...
model_list:
  # ...
  - model_name: <model_name> # -> The name that is used between `opencode` and `liteLLM`. You can name it as you want, as long as it is the same in opencode and LiteLLM
    litellm_params:
      model: openrouter/<open router model name> # -> the name of the model (as defined in the openrouter web interface) preceded with `openrouter`. For example : `openrouter/stepfunstep-3.5-flash:free`
      api_key: "os.environ/OPENROUTER_FREE" # Keep it as is. This will load the api key from the `.env` file.
# ...
```

Do not forget to restart the `LiteLLM` service to take edits into account

This will add the new model in the `LiteLLM` proxy. We now need to add it in `opencode`. To do that, you can edit your `opencode` configuration (Either at `<project_root>/opencode.json` or `$HOME/.config/opencode/opencode.json`) to add :

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    ...
    "LiteLLM": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Local - LiteLLM",
      "options": {
        "baseURL": "http://localhost:4000"
      },
      "models": {
        ...
        "<The same name as the model name in LiteLLM>": {
          "name": <The display name in openCode>
        }
      }
    }
  }
}
```

And you should now be able to see the new model in `opencode`, and use it as usual.
