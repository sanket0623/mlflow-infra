from aws_cdk import (
    Stack, RemovalPolicy, CfnOutput, Duration,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_ecr as ecr,
    aws_s3 as s3,
    aws_rds as rds,
    aws_secretsmanager as secrets,
)
from constructs import Construct

class MlflowStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Create a VPC with 2 availability zones and 1 NAT gateway
        vpc = ec2.Vpc(self, "Vpc", max_azs=2, nat_gateways=1)

        # Create an S3 bucket for MLflow artifacts with versioning enabled and a policy to destroy it when the stack is deleted
        bucket = s3.Bucket(self, "Artifacts",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True)

        db_secret = secrets.Secret(self, "DbSecret",
            generate_secret_string=secrets.SecretStringGenerator(
                secret_string_template='{"username":"mlflow"}',
                generate_string_key='password', exclude_punctuation=True))

        db = rds.DatabaseInstance(self, "Postgres",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16_3),
            vpc=vpc,
            credentials=rds.Credentials.from_secret(db_secret),
            database_name="mlflow",
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            allocated_storage=20,
            removal_policy=RemovalPolicy.DESTROY,
            deletion_protection=False)

        repo = ecr.Repository(self, "MlflowRepo", repository_name="mlflow-server")

        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)

        service = ecs_patterns.ApplicationLoadBalancedFargateService(self, "Service",
            cluster=cluster,
            cpu=1024,
            memory_limit_mib=2048,
            desired_count=1,
            public_load_balancer=True,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(repo, "latest"),
                container_port=5000,
                environment={
                    "MLFLOW_ARTIFACT_ROOT": f"s3://{bucket.bucket_name}",
                    "DB_HOST": db.db_instance_endpoint_address,
                    "DB_PORT": "5432",
                    "DB_NAME": "mlflow",
                },
                secrets={
                    "DB_USER": ecs.Secret.from_secrets_manager(db_secret, "username"),
                    "DB_PASSWORD": ecs.Secret.from_secrets_manager(db_secret, "password"),
                }
            ))

        bucket.grant_read_write(service.task_definition.task_role)
        repo.grant_pull(service.task_definition.execution_role)
        db.connections.allow_default_port_from(service.service)

        scalable = service.service.auto_scale_task_count(max_capacity=2)
        scalable.scale_on_cpu_utilization("CpuScaling", target_utilization_percent=70, cooldown=Duration.seconds(60))

        CfnOutput(self, "AlbUrl", value=f"http://{service.load_balancer.load_balancer_dns_name}")
        CfnOutput(self, "EcrRepo", value=repo.repository_uri)