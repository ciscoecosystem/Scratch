from awx import AWX
from os import getenv
from pigeon import Pigeon

# ============================================================================
# Global Variables
# ----------------------------------------------------------------------------
pigeon = Pigeon()
FETCH_TARGET = getenv('FETCH_TARGET')

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
        pigeon.sendInfoMessage('Fetching {target} from AWX: {endpoint}'.format(target=str(FETCH_TARGET).lower(), endpoint=getenv('AWX_ENDPOINT')))
        options = {
            'TEMPLATES': awx.fetch_templates,
            'CREDENTIALS': awx.fetch_credentials,
            'INVENTORIES': awx.fetch_inventories
        }
        fetch_result = options[FETCH_TARGET]()
        pigeon.sendUpdate(fetch_result, last=True)
        return
    except Exception as e:
        pigeon.sendUpdate({
            'status': 'error',
            'message' : 'An exception occurred while fetching {}: {}'.format(FETCH_TARGET, str(e)),
            'data' : {}
        })

if __name__ == "__main__":
    main()