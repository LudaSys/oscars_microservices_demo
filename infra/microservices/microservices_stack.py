import aws_cdk
from aws_cdk import (
    # Duration,
    Stack,
    aws_iam as iam,
    aws_dynamodb as ddb,
    aws_lambda as lam
)
from constructs import Construct


class OscarsMicroservicesStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Role for lambdas
        lambda_role = iam.Role(
            self,
            "msvc_lambda_role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSQSFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonCloudWatchFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBReadAccess")
            ]
        )

        # Read value lambda

        # DynamoDB setup
        user_choices_table = ddb.Table(
            self,
            "choices_table",
            table_name="user_choices",
            read_capacity = 1,
            write_capacity = 1,
            billing_mode=ddb.BillingMode.PROVISIONED,
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
            partition_key=ddb.Attribute(name="year", type=ddb.AttributeType.NUMBER),
            sort_key=ddb.Attribute(name="user_id", type=ddb.AttributeType.STRING)
        )

        user_choices_table.auto_scale_write_capacity (
            max_capacity=5,
            min_capacity=1
        )

        user_choices_table.auto_scale_read_capacity(
            max_capacity=5,
            min_capacity=1
        ).scale_on_utilization(target_utilization_percent=80)
