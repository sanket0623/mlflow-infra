#!/usr/bin/env python3
import aws_cdk as cdk
from mlflow_stack import MlflowStack

app = cdk.App()

MlflowStack(
    app,
    "MlflowPlatformStack",
    env=cdk.Environment(
        account="579035388785",
        region="ap-south-1"
    )
)

app.synth()