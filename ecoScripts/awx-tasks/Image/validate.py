from awx import AWX
from os import getenv
from pigeon import Pigeon
import json

# ============================================================================
# Global Variables
# ----------------------------------------------------------------------------
pigeon = Pigeon()
TEMPLATE_TASK_LIST = json.loads(getenv('TEMPLATE_TASK_LIST'))

# ============================================================================
# Main
# ----------------------------------------------------------------------------

def main():
    try:
        awx = AWX(
            endpoint=getenv('AWX_ENDPOINT'),
            token=getenv('AWX_TOKEN')
        )
        resp = awx.test_connectivity()
        keep_going = pigeon.sendUpdate(resp)
        if not keep_going: return
        pigeon.sendInfoMessage('Validating task list against AWX: {endpoint}'.format(endpoint=getenv('AWX_ENDPOINT')))
        
        validate_result = awx.validate_deployment_settings(
            deployment_settings=TEMPLATE_TASK_LIST,
            check_mode=True)
        pigeon.sendUpdate(validate_result, last=True)
        return
    except Exception as e:
        pigeon.sendUpdate({
            'status': 'error',
            'message' : 'An exception occurred while validating task list: {}'.format(str(e)),
            'data' : {}
        })

if __name__ == "__main__":
    main()