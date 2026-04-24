#!/usr/bin/env python3
import aws_cdk as cdk
from mlflow_stack import MlflowStack

# This is the entry point for the CDK application. It initializes the app and defines the stack(s) to be deployed.
app = cdk.App()
MlflowStack(app, "MlflowPlatformStack")
app.synth()