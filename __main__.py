import logging
import ias.simple_cdk as ias
import aws_cdk as cdk
from aws_cdk import (
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_sqs as sqs,
)


def add_sqs_sns_example(scope: cdk.Stack):
    config_group = scope.node.id  # Use CDK stack id as config group name
    queue = sqs.Queue(scope, "queue", visibility_timeout=cdk.Duration.seconds(300))
    topic = sns.Topic(
        scope,
        "topic",
        topic_name=ias.get_context_data(scope, [config_group, "topic_name"]),
    )
    topic.add_subscription(subs.SqsSubscription(queue))


def main_example1():
    """Simple example of using the ias.init_ias_model function.

    Initialises the model with just a deployment name.
    A default stack is created, id is "default" and name same as deployment name.
    An SNS topic and an SQS queue that subscribes to that topic is created.
    """
    model = ias.init_ias_model({"deployment_name": "examples"})
    stack = model["stacks"]["default"]
    add_sqs_sns_example(stack)
    ias.generate_from_model(model)


def main_example2():
    """Simple example of using the ias.init_ias_model function.

    Initialises the model with just a deployment name.
    A default stack is created, id is "default" and name same as deployment name.
    An SNS topic and an SQS queue that subscribes to that topic is created.
    The topic name is set from a config entry in the config file "examples.toml".
    """
    model = ias.init_ias_model(
        {"deployment_name": "examples"},
        option_processors=[ias.simple_config_defaults],
    )
    stack = model["stacks"]["default"]
    add_sqs_sns_example(stack)
    ias.generate_from_model(model)


def main_example3():
    """Simple example of using the ias.init_ias_model function.

    Initialises the model with a deployment name, a stack, and stack tags.
    Creates a stack with id "main" and name is "examples-main".
    An SNS topic and an SQS queue that subscribes to that topic is created.
    The topic name is set from a config entry in the config file "examples.toml".
    Resources in the stack get the tag 'Environment' with value 'dev'.
    """
    model = ias.init_ias_model(
        {
            "deployment_name": "examples",
            "stacks": [{"id": "main"}],
            "tags": {"Environment": "dev"},
        },
        option_processors=[ias.simple_config_defaults],
    )
    stack = model["stacks"]["main"]
    add_sqs_sns_example(stack)
    ias.generate_from_model(model)


def main_example4():
    """Simple example of using the ias.init_ias_model function.

    Initialises the model with a deployment name, 2 stacks, and stack tags.
    Creates a stack with id "main" and name is "examples-main".
    Creates a stack with id "other" and name is "examples-other".
    An SNS topic and an SQS queue that subscribes to that topic is created, in each stack.
    The topic name is set from a config entry in the config file "examples.toml".
    Resources in the stacks get the tag 'Environment' with value 'dev'.
    """
    model = ias.init_ias_model(
        {
            "deployment_name": "examples",
            "stacks": [{"id": "main"}, {"id": "other"}],
            "tags": {"Environment": "dev"},
        },
        option_processors=[ias.simple_config_defaults],
    )
    main_stack = model["stacks"]["main"]
    other_stack = model["stacks"]["other"]
    add_sqs_sns_example(main_stack)
    add_sqs_sns_example(other_stack)
    ias.generate_from_model(model)


if __name__ == "__main__":
    # Comment out this one or set to logging.DEBUG for more logging details
    ias.set_log_level(logging.INFO)

    ## Select example to run, uncommewnt the one you want to run
    main_example1()
    # main_example2()
    # main_example3()
    # main_example4()
