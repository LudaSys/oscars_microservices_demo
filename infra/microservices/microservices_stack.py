import aws_cdk
from aws_cdk import (
    # Duration,
    Stack,
    aws_iam as iam,
    aws_dynamodb as ddb,
    aws_lambda as lam,
    aws_logs as logs,
    aws_apigateway as gateway
)
from constructs import Construct


class OscarsMicroservicesStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB setup
        user_choices_table = ddb.Table(
            self,
            "choices_table",
            table_name = "user_choices",
            read_capacity = 1,
            write_capacity = 1,
            billing_mode = ddb.BillingMode.PROVISIONED,
            removal_policy = aws_cdk.RemovalPolicy.DESTROY,
            partition_key = ddb.Attribute(name = "year", type = ddb.AttributeType.NUMBER),
            sort_key = ddb.Attribute(name = "user_id", type = ddb.AttributeType.STRING)
        )

        # Auto scaling rules
        user_choices_table.auto_scale_write_capacity(
            max_capacity = 5,
            min_capacity = 1
        )

        user_choices_table.auto_scale_read_capacity(
            max_capacity = 5,
            min_capacity = 1
        ).scale_on_utilization(target_utilization_percent = 80)

        # Role for lambdas
        lambda_role = iam.Role(
            self,
            "microservice_lambda_role",
            assumed_by = iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies = [
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchFullAccess"),
            ],
        )

        # Create inline policy to access dynamo table
        lambda_role.attach_inline_policy(
            iam.Policy(
                self,
                "oscars_lambda_db_access_inline_policy",
                policy_name = "oscars_db_access_policy",
                statements = [
                    iam.PolicyStatement(
                        effect = iam.Effect.ALLOW,
                        actions = [
                            'dynamodb:*'
                        ],
                        resources = [user_choices_table.table_arn]
                    )
                ]
            )
        )

        # Read value lambda
        read_item_lambda = lam.Function(
            self,
            "read_value",
            runtime = lam.Runtime.PYTHON_3_9,
            memory_size = 128,
            timeout = aws_cdk.Duration.seconds(60),
            code = lam.AssetCode.from_asset("../functions/read_items"),
            handler = "read_items.handler",
            architecture = lam.Architecture.ARM_64,
            role = lambda_role,
            log_retention = logs.RetentionDays.ONE_WEEK,
            current_version_options = lam.VersionOptions(removal_policy = aws_cdk.RemovalPolicy.DESTROY),
            environment = {
                "DYNAMODB_TABLE": "user_choices"
            }
        )

        # Scan items lambda
        scan_item_lambda = lam.Function(
            self,
            "scan_items_oscars",
            runtime = lam.Runtime.PYTHON_3_9,
            memory_size = 128,
            timeout = aws_cdk.Duration.seconds(60),
            code = lam.AssetCode.from_asset("../functions/scan_items"),
            handler = "scan_items.handler",
            architecture = lam.Architecture.ARM_64,
            role = lambda_role,
            log_retention = logs.RetentionDays.ONE_WEEK,
            current_version_options = lam.VersionOptions(removal_policy = aws_cdk.RemovalPolicy.DESTROY),
            environment = {
                "DYNAMODB_TABLE": "user_choices"
            }
        )

        # API Gateway
        rest_api = gateway.RestApi(
            self,
            "oscars-api",
            rest_api_name = "OscarsLambdaApi",
            retain_deployments = False,
            endpoint_export_name = "OscarsRestApiUrl",
            deploy = True,
            endpoint_types = [gateway.EndpointType.REGIONAL],
            deploy_options = gateway.StageOptions(
                stage_name = "dev",
                caching_enabled = False,
                cache_ttl = aws_cdk.Duration.minutes(1),
                throttling_burst_limit = 100,
                throttling_rate_limit = 1000
            )
        )

        # Scan resource and endpoint
        scan_endpoint = rest_api.root.add_resource("scan")
        scan_endpoint.add_method(
            http_method = "GET",
            integration = gateway.LambdaIntegration(scan_item_lambda),
            api_key_required = True
        )

        # Read resource and endpoint
        read_endpoint = rest_api.root.add_resource("read")
        read_endpoint.add_method(
            http_method = "GET",
            integration = gateway.LambdaIntegration(read_item_lambda),
            api_key_required = True
        )

        # Usage plan
        usage_plan = rest_api.add_usage_plan(
            "OscarsApiUsagePlan",
            name = "OscarsUsagePlan",
            throttle = gateway.ThrottleSettings(
                burst_limit = 10,
                rate_limit = 100
            ),
            quota = gateway.QuotaSettings(
                limit = 100,
                offset = 0,
                period = gateway.Period.DAY
            ),
            api_stages = [
                gateway.UsagePlanPerApiStage(
                    api = rest_api,
                    stage = rest_api.deployment_stage
                )
            ]
        )

        # API key
        api_key = rest_api.add_api_key(
            "OscarsApiKey",
            api_key_name = "oscars_api_key",
            description = "API key for Oscars Gateway"
        )

        # Attach api key to use plan
        usage_plan.add_api_key(api_key)
