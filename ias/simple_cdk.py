"""Simplified boilerplate for AWS CDK solutions in Python

This module provides a simplified interface for creating AWS CDK solutions.
It is based on the following concepts:

- A model describing the infrastructure. Under the hood, this includes:

    - A deployment name
    - A CDK App
    - A collection of CDK Stacks
    - The current environment
    - Configuration data, possibly read from a source, e.g. a TOML file

- A few conveniance functions for creating the model, generating the resulting
  CloudFormation template(s), and sharing data between stacks.

- Function-based resource model creation, as opposed to class inheritance-based creation.

- Using structural typing for parameterizing resources, similar to AWS CDK for TypeScript.
  This approach leverages Python's TypedDict, rather than Python classes.

- Resource parameters follow a data-oriented approach with extendable dictionary
  structures.As long as the needed data is in place, it does not matter if there
  are other additional keys and values as well.
"""
import copy
import os
import structlog
from typing import TypedDict, Callable, Any, List
import aws_cdk as cdk
import constructs as cons

try:
    from typing import Required
except ImportError:
    from typing_extensions import Required
try:
    import tomllib as toml
except ImportError:
    import tomli as toml

#######################
### Data structures ###
#######################


class IasModel(TypedDict, total=False):
    """Model for the IAS solution.

    The model includes the following:

    - The deployment name
    - The CDK App
    - A collection of CDK Stacks
    - The current environment
    """

    deployment_name: Required[str]
    app: Required[cdk.App]
    stacks: Required[dict[str, cdk.Stack]]
    current_environment: Required[tuple[str, cdk.Environment]]


class EnvironmentOptions(TypedDict, total=False):
    """Settings for the CDK App's environment. Environment is also given a name."""

    name: Required[str]
    account: str
    region: str


class StackInfoOptions(TypedDict, total=False):
    """Stack information for the IAS solution.

    Includes the CDK identifier, and optional stack name and stack dependencies
    """

    id: Required[str]
    name: str
    depends_on: list[str]


class IasModelOptions(TypedDict, total=False):
    """Options for initialising the model.

    Includes the deployment name, names of stacks to include,
    and environment settings. Also includes setting initial context
    and tags. Only deployment name is required.
    """

    deployment_name: Required[str]
    stacks: list[StackInfoOptions]
    environment: EnvironmentOptions
    context: dict[str, Any]
    tags: dict[str, str]


### Helper functions ###


def _create_environment(opts: EnvironmentOptions) -> tuple[str, cdk.Environment]:
    """Create an AWS CDK Environment from the given options."""
    env = cdk.Environment(account=opts.get("account"), region=opts.get("region"))
    return opts["name"], env


def _make_stack_name(prefix: str, id: str, env_name: str) -> str:
    """Create a stack name from the given parameters."""

    if id == "default" and prefix != "":
        return f"{prefix}"
    elif prefix == "":
        return f"{id}"
    elif env_name == "":
        return f"{prefix}-{id}"
    else:
        return f"{prefix}-{id}-{env_name}"


def _apply_stack_tags(stack: cdk.Stack, tags: dict[str, str]) -> None:
    """Apply tags to the given stack."""
    stacktags = cdk.Tags.of(stack)
    for key, value in tags.items():
        stacktags.add(key, value)


#########################
### Option processors ###
#########################


def set_env_account_region_from_env_vars(
    options: IasModelOptions, logger=structlog.get_logger()
) -> IasModelOptions:
    """Function to implement environment settings from CDK environment variables."""
    new_options = copy.deepcopy(options)
    env = new_options.get("environment", {})
    if env.get("account") is None:
        env["account"] = os.getenv("CDK_DEFAULT_ACCOUNT")
    if env.get("region") is None:
        env["region"] = os.getenv("CDK_DEFAULT_REGION")
    if env.get("name") is None:
        env["name"] = ""
    new_options["environment"] = env
    logger.debug("set_env_account_region_from_env_vars", env=env)
    return new_options


def set_default_stack_if_no_stacks(
    options: IasModelOptions, logger=structlog.get_logger()
) -> IasModelOptions:
    """Function to implement default stack settings if no stacks are specified."""
    new_options = copy.deepcopy(options)
    stacks = new_options.get("stacks", [])
    if len(stacks) == 0:
        stack_info = {
            "id": "default",
            "name": new_options.get("deployment_name", ""),
            "depends_on": [],
        }
        stacks.append(stack_info)
        new_options["stacks"] = stacks
        logger.debug("set_default_stack_if_no_stacks", stacks=stacks)
    return new_options


def set_stack_names(
    options: IasModelOptions, logger=structlog.get_logger()
) -> IasModelOptions:
    """Function to implement naming policy for stacks.

    If a stack already has a name explicitly set, no change is made

    If the environment name is empty, the stack name is the deployment name
    followed by the stack ID.

    If the environment name is not empty, the stack name is the deployment name
    followed by the stack ID, followed by the environment name.
    """
    new_options = copy.deepcopy(options)
    deployment_name = new_options.get("deployment_name", "")
    env_name = new_options.get("environment", {}).get("name", "")
    stacks = new_options.get("stacks", [])
    for stack_info in stacks:
        stack_id = stack_info.get("id", "default")
        if stack_info.get("name") is None:
            stack_info["name"] = _make_stack_name(deployment_name, stack_id, env_name)
    new_options["stacks"] = stacks
    logger.debug("set_stack_names", stacks=stacks)
    return new_options


def load_toml_config_files(
    options: IasModelOptions, logger=structlog.get_logger()
) -> IasModelOptions:
    """Function to implement configuration loading from TOML files.

    The configuration data is loaded from the following files, in order:

    - The environment name, followed by
      ".toml"
    - The deployment name, followed by ".toml"
    - The deployment name, followed by "-", followed by the environment name,
      followed by ".toml"

    Any settings already existing will be overwritten if the same setting is loaded
    from a file.
    """
    deployment_name = options.get("deployment_name", "")
    env_name = options.get("environment", {}).get("name", "")
    config_paths = []
    if env_name != "":
        config_paths.append(f"{env_name}.toml")
    if deployment_name != "":
        config_paths.append(f"{deployment_name}.toml")
    if deployment_name != "" and env_name != "":
        config_paths.append(f"{deployment_name}-{env_name}.toml")

    config_result: dict[str, Any] = options.get("context", {})
    for config_path in config_paths:
        try:
            with open(config_path, "rb") as f:
                config_result.update(toml.load(f))
        except FileNotFoundError:
            pass
    new_options = copy.deepcopy(options)
    new_options["context"] = config_result
    logger.debug(
        "load_toml_config_files", context=config_result, config_paths=config_paths
    )
    return new_options


def simple_defaults(
    options: IasModelOptions, logger=structlog.get_logger()
) -> IasModelOptions:
    """Processor to add some default settings to the model.

    This processor adds some default settings to the model:
    - Get default environment settings from CDK environment variables
    - Set a default stack entry if no stacks have been specified
    - Get default stack names from the deployment name and/or environment name
    """
    options = set_env_account_region_from_env_vars(options, logger=logger)
    options = set_default_stack_if_no_stacks(options, logger=logger)
    options = set_stack_names(options, logger=logger)
    return options


def simple_config_defaults(
    options: IasModelOptions, logger=structlog.get_logger()
) -> IasModelOptions:
    """Processor to add some default settings to the model.

    This processor adds some default settings to the model:
    - Same settings as simple_env_and_stack_defaults processor
    - Load configuration settings from TOML files
    """
    options = simple_defaults(options, logger=logger)
    options = load_toml_config_files(options, logger=logger)
    return options


##################################
### Model management functions ###
##################################


def init_ias_model(
    options: IasModelOptions,
    option_processors: list[Callable[[IasModelOptions], IasModelOptions]] = [
        simple_defaults
    ],
    *,
    logger=structlog.get_logger(),
) -> IasModel:
    """Initialises the model for the IAS solution.

    The model dictionary may include the following:

    - The deployment name
    - The CDK App
    - A collection of CDK Stacks
    - The current environment

    The environment consists of an AWS account and AWS region combination.

    The input parameters are the IAS model options, and a list of option processors.
    The IAS model options include:
        - deployment name (mandatory)
        - list of stack id:s and/or stack names
        - environment settings (AWS account id and region)
        - configuration/context settings
        - stack tags

    Option processors are functions that process the options before building the model.
    They are called in the order specified. Input is the IasModelOptions, and the
    output is the modified IasModelOptions.

    The default option processors included will set the default environment settings
    from the CDK environment variables CDK_DEFAULT_ACCOUNT and CDK_DEFAULT_REGION.
    They will also set the default stack settings if no stacks have been specified.
    In addition, they will set the default stack names from the deployment name
    and/or environment name.

    There is also a default option processor included that will load configuration
    settings from TOML files.

    Args:
        options (IasModelOptions): The options for the model.
        options_processors: list[Callable[[IasModelOptions], IasModelOptions]]: A list of
            functions that process the options before building the model.

    Returns:
        IasModel: The model.
    """
    for processor in option_processors:
        options = processor(options)
    logger.debug("init_ias_model", options=options)
    deployment_name = options["deployment_name"]
    stacks: dict[str, cdk.Stack] = {}
    env = options.get("environment", {"name": ""})
    current_env = _create_environment(env)
    app = cdk.App(context=options.get("context", None))

    for stack_info in options.get("stacks", []):
        stack_id = stack_info["id"]
        stack_name = stack_info.get("name", stack_id)
        stack = cdk.Stack(app, stack_id, stack_name=stack_name, env=current_env[1])
        _apply_stack_tags(stack, options.get("tags", {}))
        stacks[stack_id] = stack
    model: IasModel = {
        "deployment_name": deployment_name,
        "app": app,
        "stacks": stacks,
        "current_environment": current_env,
    }
    return model


def generate_from_model(model: IasModel) -> None:
    """Generate (synthesize) CloudFormation and assets from model"""
    model["app"].synth()


#########################
### Support functions ###
#########################


def get_context_data(scope: cons.Construct, key: str | List[str]) -> Any | None:
    """Get the context data for a construct"""
    if isinstance(key, str):
        return scope.node.try_get_context(key)
    else:
        context = scope.node.try_get_context(key[0])
        for k in key[1:]:
            if context is None:
                break
            context = context.get(k)
        return context


def add_namespace(scope: cons.Construct, name: str) -> cons.Construct:
    """Add a namespace to a stack for grouping of resources"""
    return cons.Construct(scope, name)


def set_log_level(level) -> None:
    """Set the log level for the logger"""
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(level))
