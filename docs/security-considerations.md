# Security Considerations

Implemented or defined controls:

- local mode does not require AWS credentials;
- separate ECS task roles are defined for API, scheduler, and worker;
- API ingress is intended to come through the ALB security group;
- scheduler and worker security groups have no inbound application traffic;
- DynamoDB, SQS, SNS, and CloudWatch use AWS-managed encryption defaults in the prepared Terraform;
- no static AWS credentials are stored in the repository.

Current limitations:

- no authentication or authorization is implemented for the API;
- HTTPS, domain, and ACM certificate are not configured;
- full SSRF protection is not implemented;
- AWS deployment and IAM behavior have not been proven by applying the Terraform.

Treat the repository as a demo architecture, not a hardened production service.
