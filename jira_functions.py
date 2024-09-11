import sys
import logging
from jira import JIRA
from database import get_jira_credentials


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def create_jira_issue(summary, description):
    jira_data = get_jira_credentials() 
    if not jira_data:
        logger.error("Jira credentials not found.")
        return None

    jira_base_url, username, password, send_to_jira, project_key = jira_data

    options = {'server': jira_base_url, 'verify': False}
    jira = JIRA(options=options, basic_auth=(username, password))

    issue_dict = {
            "project": {'key': f"{project_key}"},
            "summary": summary,
            "description": description,
            "issuetype": {"name": "Task"}
    }
    try:
        new_issue = jira.create_issue(fields=issue_dict)
        return new_issue.key
    except Exception as e:
        logger.error(f"Failed to create Jira issue: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Jira response: {e.response.text}")
        return None
    
def create_test_issue():
    summary = "Test Issue"
    description = "This is a test issue created for validation."
    
    issue_key = create_jira_issue(summary, description)
    
    if issue_key:
        logger.info(f"Test issue created successfully: {issue_key}")
        return "ok"
    else:
        logger.error("Failed to create test issue.")
        return "error"



