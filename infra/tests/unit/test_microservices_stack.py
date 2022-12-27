import aws_cdk as core
import aws_cdk.assertions as assertions

from microservices.microservices_stack import OscarsMicroservicesStack

# example tests. To run these tests, uncomment this file along with the example
# resource in microservices/microservices_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = OscarsMicroservicesStack(app, "microservices")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
