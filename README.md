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

There is also a certain amount of boilerplate work for handling config data, stacks, tags, and AWS environment setup. I'm a fan of black (code formatting), ruff (code linting), pytest (testing) and pre-commit (run checks before git commit). So these are included by default.

AWS CDK examples encourage building solutions with inheritance, and push most logic into constructors. Grouping resources through inheritance leads to (too) long resource identifiers. Keeping resources after refactoring is difficult because of CloudFormation's restrictions.

Also, I think inheritance is overused. **It might be useful for building specific reusable components, but not for everything in a CDK-based solution.**

There are multiple project scaffolding solutions that work for Python, but not so much aimed at issues with AWS CDK and Python.

The intention is to provide a rather lightweight template for setting up AWS CDK projects, which may cover some common use cases. It is extendable and many behaviours can be replaced easily, if desired.

### Examples

*All examples below call a function `add_sqs_sns_example()` to add an SQS queue and an SNS topic, with the SQS as a subscriber to that topic. This is very much like the default AWS CDK template generated, except that the stack to add them to is passed as a parameter to this function. The same pattern can be used for any resources.*

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

### Design considerations

All options and the model structure use the **TypedDict** feature. This is like a regular dictionary, but also includes typing information for the defined fields. Thus you can get type hints in your editor of choice for these structures, plus it allows for you to extend them yourself as well. It also uses **structural typing**, meaning that as long as the dictionary includes the required fields, it is a valid data structure. No need to create class objects explicitly. It is kind of similar to the typing experience found in, for example, TypeScript.

Rather than loading resources into the stack constructor, I suggest using regular functions to add them. This should help with building a bit more modular code without too much boilerplate.

### Things to do

- Add handling for stack dependencies
- Generate API docs
	- Issues with getting **pdoc** to work when JSII is involved
- Figure out reasonable scope without making it too heavy, for example
	- Wrappers for sharing data between stacks? (Parameter store, etc)
	- Add (optional) default monitoring (e.g. via cdk-monitoring-constructs)?
	- Add (optional) default security/policy processing (e.g. via cdk-nag)?
- Get more feedback
