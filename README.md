# awscdk-python-template

Project template for setting up infrastructure projects based on
AWS Cloud Development Kit.

This is an opinionated template for setting up a Python-based
AWS Cloud Development Kit (CDK) project.

The aim of this template is is to provide some convenience methods to
facilitate the set-up of AWS CDK projects in Python.
Currently, Python 3.10 or later is required.

### Template summary
The summary here of what is included you can see here, to read a bit more about the reasoning, look further below:

- Adding config to CDK context automatically, from TOML files.
- Encourage a flatter, non-inheritance approach to resource composition to facilitate refactoring
- Simplified stack creation - automatic if single stack project, and always assign AWS account and region to stacks
- Simplified stack-level tagging of resources
- Modern package manager usage option - PDM
- Python development tools include:
	- black - code formatting
	- ruff - fast linter
	- pre-commit - Pre-commit hooks for formatting and linting
	- pytest - testing framework
- Logging and print debugging
	- structlog
	- icecream
- Extendable model and behaviour processing of project setup options
- Requires Python 3.10 or higher currently

### Usage

This is a **GitHub template repository**, so if you re using the GitHub GUI, you can click on **Use this template** and select *Create a new repository*.

https://github.com/cloudgnosis/awscdk-python-template

Or just copy the files, or use the parts that fit your use cases. Either way, I hope you find some parts of it useful.
The file `__main__.py` contains a few simple examples.

### Reasoning behind the template

The core of the template comes from a frustration with the regular `cdk init` templates, which is not that flexible. I rip out or change a lot of the content - to where I might have set it up from scratch instead.

There is also a certain amount of boilerplate work for handling config data, stacks, tags, and AWS environment setup.  This also includes developer tooling, where I am a fan of tools like black, ruff, pytest and pre-commit.

AWS CDK examples encourage building solutions with inheritance, and push most logic into constructors. Grouping resources through inheritance leads to (too) long resource identifiers. It makes it harder to refactor resources if you still want to keep the resources after refactoring, because of limitations with CloudFormation.

There are multiple project scaffolding solutions that work for Python, but not so much aimed at issues with AWS CDK and Python.

The indention is to provide a rather lightweight template for setting up AWS CDK projects, which may cover some common use cases. It is extendable and many behaviours can be replaced easily, if desired.

### Example

Here is a rather simple example, which will have a single stack, and all resources tagged with `Environment = dev`:

```python
def main_example():
	model = ias.init_ias_model(
		{
		    "deployment_name": "examples",
		    "tags": {
			    "Environment": "dev",
			},
		}
	)
	stack = model["stacks"]["default"]
	add_sqs_sns_example(stack)
	ias.generate_from_model(model)
```

This will set up a CDK App, and a single stack with id `default`  and name `examples`. All resources will be tagged with tag _Environment_ with value *dev*. The **model** object is a dictionary that contains the app, stack, and environment resources.

You get the stack from the model, and can call functions to add resources to that stack. When this is done, the `generate_from_model()` function will create the CloudFormation, the same as calling `app.synth()` on the CDK App object.

AWS account and region will be determined based on the currently active credentials, in this case.

A slightly more complicated example may look like this:

```python
def main_example():
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
```

Here there are two stacks, with ids `main` and `other` and stack names `examples-main` and `examples-other` . There is a different **option processor**, which in this case includes reading config from TOML files. All config data is available though CDK context, so it can be retrieved via any CDK Construct-type object (Construct, Stack, Stage, App).

The *option processors* are simply functions that update the input options and return a new set of input options. When all these processors have been executed, the actual model initialisation takes place.

### Things to do

- Add handling for stack dependencies
- Generate API docs
	- Issues with getting **pdoc** to work when JSII is involved
- Figure out reasonable scope without making it too heavy, for example
	- Wrappers for sharing data between stacks? (Parameter store, etc)
	- Add (optional) default monitoring (e.g. via cdk-monitoring-constructs)?
	- Add (optional) default security/policy processing (e.g. via cdk-nag)?
- Get more feedback
