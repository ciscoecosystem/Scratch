from awx import AWX
from os import getenv
from pigeon import Pigeon
import json

# ============================================================================
# Global Variables
# ----------------------------------------------------------------------------
pigeon = Pigeon()
DEPLOYMENT_VARS = json.loads(getenv('DEPLOYMENT_VARS')) if getenv('DEPLOYMENT_VARS') else None

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
        resp = awx.get_deployment_details(DEPLOYMENT_VARS['id'])
        pigeon.sendUpdate(resp, last=True)
        return
    except Exception as e:
        pigeon.sendUpdate({
            'status': 'error',
            'message' : 'An exception occurred while deleting deployment {}'.format(DEPLOYMENT_VARS['id']),
            'data' : {}
        })

if __name__ == "__main__":
    main()