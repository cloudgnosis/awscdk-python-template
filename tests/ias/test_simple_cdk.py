import copy
import ias.simple_cdk as ias
import aws_cdk as cdk


def test_set_env_account_region_from_env_vars(monkeypatch):
    monkeypatch.setenv("CDK_DEFAULT_ACCOUNT", "123456789012")
    monkeypatch.setenv("CDK_DEFAULT_REGION", "eu-north-1")
    options: ias.IasModelOptions = {"deployment_name": "test"}
    new_options = ias.set_env_account_region_from_env_vars(options)
    assert new_options["environment"]["name"] == ""
    assert new_options["environment"]["account"] == "123456789012"
    assert new_options["environment"]["region"] == "eu-north-1"


def test_set_default_stack_if_no_stacks():
    options: ias.IasModelOptions = {"deployment_name": "test"}
    new_options = ias.set_default_stack_if_no_stacks(options)
    assert len(new_options["stacks"]) == 1
    assert new_options["stacks"][0]["id"] == "default"
    assert new_options["stacks"][0]["name"] == "test"


def test_make_stack_name():
    assert ias._make_stack_name("", "stackid", "") == "stackid"
    assert ias._make_stack_name("test", "default", "") == "test"
    assert ias._make_stack_name("test", "test2", "") == "test-test2"
    assert ias._make_stack_name("test", "test2", "test3") == "test-test2-test3"


def test_set_stack_names():
    options: ias.IasModelOptions = {
        "deployment_name": "test",
        "stacks": [{"id": "test1", "name": "test1name"}, {"id": "test2"}],
    }
    new_options = ias.set_stack_names(options)
    assert len(new_options["stacks"]) == 2
    assert new_options["stacks"][0]["id"] == "test1"
    assert new_options["stacks"][0]["name"] == "test1name"
    assert new_options["stacks"][1]["id"] == "test2"
    assert new_options["stacks"][1]["name"] == "test-test2"


def test_init_ias_model_only_deployment_name():
    model = ias.init_ias_model({"deployment_name": "test"})
    assert model["deployment_name"] == "test"
    assert isinstance(model["app"], cdk.App)
    assert model.get("stacks") is not None
    stacks = model["stacks"]
    assert len(stacks) == 1
    assert isinstance(stacks["default"], cdk.Stack)


def test_init_ias_model_default_env(monkeypatch):
    monkeypatch.setenv("CDK_DEFAULT_REGION", "eu-north-0")
    monkeypatch.setenv("CDK_DEFAULT_ACCOUNT", "123456789012")
    model = ias.init_ias_model({"deployment_name": "test"})
    env_name, env = model["current_environment"]
    assert env_name == ""
    assert env.account == "123456789012"
    assert env.region == "eu-north-0"


def test_init_ias_model_default_stack_info(monkeypatch):
    monkeypatch.setenv("CDK_DEFAULT_REGION", "eu-north-0")
    monkeypatch.setenv("CDK_DEFAULT_ACCOUNT", "123456789012")
    model = ias.init_ias_model({"deployment_name": "test"})
    stack = model["stacks"]["default"]
    assert stack.stack_name == "test"
    assert stack.region == "eu-north-0"
    assert stack.account == "123456789012"


def test_init_model_named_environment(monkeypatch):
    monkeypatch.setenv("CDK_DEFAULT_ACCOUNT", "123456789012")
    monkeypatch.setenv("CDK_DEFAULT_REGION", "eu-north-1")
    model = ias.init_ias_model(
        {"deployment_name": "test", "environment": {"name": "testenv"}}
    )
    env_name, env = model["current_environment"]
    assert env_name == "testenv"
    assert env.account == "123456789012"
    assert env.region == "eu-north-1"


def test_init_model_named_environment_default_region(monkeypatch):
    monkeypatch.setenv("CDK_DEFAULT_ACCOUNT", "123456789012")
    monkeypatch.setenv("CDK_DEFAULT_REGION", "eu-north-0")
    model = ias.init_ias_model(
        {
            "deployment_name": "test",
            "environment": {"name": "testenv", "account": "234567890123"},
        }
    )
    env_name, env = model["current_environment"]
    assert env_name == "testenv"
    assert env.account == "234567890123"
    assert env.region == "eu-north-0"


def test_init_model_named_environment_default_account(monkeypatch):
    monkeypatch.setenv("CDK_DEFAULT_ACCOUNT", "123456789012")
    monkeypatch.setenv("CDK_DEFAULT_REGION", "eu-north-0")
    model = ias.init_ias_model(
        {
            "deployment_name": "test",
            "environment": {"name": "testenv", "region": "eu-north-1"},
        }
    )
    env_name, env = model["current_environment"]
    assert env_name == "testenv"
    assert env.account == "123456789012"
    assert env.region == "eu-north-1"


def test_init_model_multiple_stacks():
    model = ias.init_ias_model(
        {
            "deployment_name": "test",
            "stacks": [{"id": "test2"}, {"id": "test3"}],
        }
    )
    assert len(model["stacks"]) == 2
    assert isinstance(model["stacks"]["test3"], cdk.Stack)
    assert isinstance(model["stacks"]["test2"], cdk.Stack)
    assert model["stacks"]["test3"].stack_name == "test-test3"
    assert model["stacks"]["test2"].stack_name == "test-test2"


def test_init_model_hardcoded_env():
    model = ias.init_ias_model(
        {
            "deployment_name": "test",
            "environment": {
                "name": "testenv",
                "account": "234567890123",
                "region": "eu-north-1",
            },
        }
    )
    env_name, env = model["current_environment"]
    assert env_name == "testenv"
    assert env.account == "234567890123"
    assert env.region == "eu-north-1"


def test_init_model_hardcoded_env_model_postprocessing():
    def hardcode_env(options: ias.IasModelOptions) -> ias.IasModelOptions:
        new_options = copy.deepcopy(options)
        new_options["environment"]["name"] = "hardcoded_env"
        new_options["environment"]["account"] = "111111111111"
        new_options["environment"]["region"] = "eu-north-0"
        return new_options

    model = ias.init_ias_model(
        {
            "deployment_name": "test",
            "environment": {
                "name": "testenv",
                "account": "234567890123",
                "region": "eu-north-1",
            },
        },
        [hardcode_env],
    )
    assert model["current_environment"] == (
        "hardcoded_env",
        cdk.Environment(account="111111111111", region="eu-north-0"),
    )


def test_get_context_data():
    options: ias.IasModelOptions = {
        "deployment_name": "test",
        "context": {
            "config1": "value1",
            "config2": {
                "subconfig1": "subvalue1",
            },
        },
    }
    model = ias.init_ias_model(options)
    stack = model["stacks"]["default"]
    cfg1 = ias.get_context_data(stack, "config1")
    cfg2 = ias.get_context_data(stack, ["config2", "subconfig1"])
    cfg3 = ias.get_context_data(stack, "config3")
    assert cfg1 == "value1"
    assert cfg2 == "subvalue1"
    assert cfg3 is None
