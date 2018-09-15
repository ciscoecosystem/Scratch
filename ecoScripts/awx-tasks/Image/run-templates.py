from os import getenv
from awx import AWX
from pigeon import Pigeon
import json

# ============================================================================
# Global Variables
# ----------------------------------------------------------------------------
pigeon = Pigeon()
TEMPLATE_TASK_LIST = json.loads(getenv('TEMPLATE_TASK_LIST'))
WORKFLOW_VARS = json.loads(getenv('AWX_WORKFLOW_VARS'))
DEPLOYMENT_VARS = json.loads(getenv('DEPLOYMENT_VARS'))['deployment_vars'] if getenv('DEPLOYMENT_VARS') else None
DEPLOYMENT_ID = getenv('JOB_ID')

# ============================================================================
# Main
# ----------------------------------------------------------------------------


def main():
    try:
        awx = AWX(
            endpoint=getenv('AWX_ENDPOINT'),
            token=getenv('AWX_TOKEN')
        )
        EXTRA_VARS = { 'workflow_vars': WORKFLOW_VARS, 'deployment': { 'user': {}, 'id': DEPLOYMENT_ID }}
        if DEPLOYMENT_VARS:
            EXTRA_VARS['deployment']['user'] = DEPLOYMENT_VARS['user']
        resp = awx.test_connectivity()
        keep_going = pigeon.sendUpdate(resp)
        if not keep_going: return
        settings = awx.validate_deployment_settings(awx.render(TEMPLATE_TASK_LIST))
        keep_going = pigeon.sendUpdate(settings)
        if not keep_going: return
        resp = awx.run_deployment(settings['settings'], EXTRA_VARS)
        pigeon.sendUpdate(resp, last=True)
        return
    except Exception as e:
        pigeon.note.update({
            'status_code': 400,
            'message': 'An exception occurred while testing connectivity: {}'.format(str(e)),
            'data': {}
        })
        pigeon.send()


if __name__ == "__main__":
    main()