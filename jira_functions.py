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
    
def assign_issue_to_user(jira_username, jira_issue_key):
    jira_data = get_jira_credentials() 
    if not jira_data:
        logger.error("Jira credentials not found.")
        return None

    jira_base_url, username, password, send_to_jira, project_key = jira_data

    options = {'server': jira_base_url, 'verify': False}
    jira = JIRA(options=options, basic_auth=(username, password))

    try:
        issue = jira.issue(jira_issue_key)
        jira.assign_issue(issue ,jira_username)
        logger.info(f"Issue {jira_issue_key} assigned to {jira_username}.")
        return "ok"
    except Exception as e:
        logger.error(f"Failed to assign issue {jira_issue_key} to {jira_username}: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Jira response: {e.response.text}")
        return "error"
    
def get_jira_issue_status(issue_key):
    jira_data = get_jira_credentials() 
    if not jira_data:
        logger.error("Jira credentials not found.")
        return None

    jira_base_url, username, password, send_to_jira, project_key = jira_data

    options = {'server': jira_base_url, 'verify': False}
    jira = JIRA(options=options, basic_auth=(username, password))

    try:
        issue = jira.issue(issue_key)
        status = issue.fields.status.name
        logger.info(f"Issue {issue_key} status: {status}")
        return status
    except Exception as e:
        logger.error(f"Failed to retrieve status for issue {issue_key}: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Jira response: {e.response.text}")
        return None
    
def create_test_issue():
    summary = "Test Issue From Oncall Bot"
    description = "This is a test issue created for validation."
    
    issue_key = create_jira_issue(summary, description)
    
    if issue_key:
        logger.info(f"Test issue created successfully: {issue_key}")
        return "ok"
    else:
        logger.error("Failed to create test issue.")
        return "error"


def transition_issue_to_done(issue_key):
    jira_data = get_jira_credentials() 
    if not jira_data:
        logger.error("Jira credentials not found.")
        return None

    jira_base_url, username, password, send_to_jira, project_key = jira_data

    options = {'server': jira_base_url, 'verify': False}
    jira = JIRA(options=options, basic_auth=(username, password))

    try:
        issue = jira.issue(issue_key)
        
        transitions = jira.transitions(issue)
        
        done_transition_id = None
        for transition in transitions:
            if transition['name'] == 'Done':
                done_transition_id = transition['id']
                break
        
        if done_transition_id:
            jira.transition_issue(issue, done_transition_id)
            logger.info(f"Issue {issue_key} transitioned to Done.")
            return "ok"
        else:
            logger.error(f"No transition to Done found for issue {issue_key}.")
            return "error"
    except Exception as e:
        logger.error(f"Failed to transition issue {issue_key} to Done: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Jira response: {e.response.text}")
        return "error"
