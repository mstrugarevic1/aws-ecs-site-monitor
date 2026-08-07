from pathlib import Path

WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "deploy.yml"


def test_deployment_workflow_guards_and_verification() -> None:
    workflow = WORKFLOW.read_text()

    assert "github.ref == 'refs/heads/main'" in workflow
    assert "environment: aws-dev" in workflow
    assert "id-token: write" in workflow
    assert "allowed-account-ids:" in workflow
    assert "-target=module.ecr" in workflow
    assert "aws ecs wait services-stable" in workflow
    assert '"http://$alb_dns/healthz"' in workflow
