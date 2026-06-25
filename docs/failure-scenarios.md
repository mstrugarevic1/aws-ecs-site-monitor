# Failure Scenarios

This project includes local demonstrations and future AWS-only scenarios.

## Local Demonstrations

1. Monitored service returns HTTP 500
   - Run the worker against a mocked `httpx.MockTransport` that returns `500`.
   - Expected result: the monitor state becomes `DOWN`, result history records the failure, and the alert threshold logic starts counting failures.

2. Monitored service times out
   - Use a mocked transport that raises `httpx.ReadTimeout`.
   - Expected result: the result records `timeout`, status is `DOWN`, and latency is left empty.

3. Repository write fails
   - Replace the in-memory repository with a test double that raises on `add_result`.
   - Expected result: the worker surfaces the error and the message is retried.

4. Queue message repeatedly fails
   - Use the in-memory queue with `max_receive_count=2` and a checker that raises.
   - Expected result: the message is retried and then moved to the dead-letter list.

5. New API version fails its health check locally
   - Start the API with a broken `/healthz` implementation in a throwaway branch or test double.
   - Expected result: the health endpoint returns a failure and the process is not considered healthy.

6. Worker crashes while processing a message
   - Use a checker test double that raises `RuntimeError`.
   - Expected result: the queue message is released for retry.

7. Alert is triggered after three failures
   - Seed a monitor with `consecutive_failures=2` and `failure_threshold=3`, then run one more failed check.
   - Expected result: a single alert notification is recorded.

8. Recovery alert is generated when the service returns to UP
   - Seed a monitor in `DOWN` state, then run a successful check.
   - Expected result: a recovery notification is recorded and the failure counter resets.

## Future AWS Scenarios

1. Checker lacks DynamoDB permission
   - Remove the worker task role permission and run the worker in ECS.
   - Expected result: the task logs an access-denied error and the message is retried.

2. SQS message reaches the DLQ
   - Set the queue redrive policy in Terraform and repeatedly fail the worker.
   - Expected result: the message lands in the dead-letter queue after the retry limit.

3. ECS deployment circuit breaker rolls back
   - Deploy a broken API revision that fails `/healthz`.
   - Expected result: ECS rolls back to the previous task definition.

4. ALB target becomes unhealthy
   - Break the API health endpoint or block the container port.
   - Expected result: the target becomes unhealthy and the alarm fires.

5. SNS notification is sent
   - Cross the failure threshold in the worker with SNS subscription enabled.
   - Expected result: the alert is published to SNS.

