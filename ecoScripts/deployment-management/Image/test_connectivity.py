from awx import AWX
from os import getenv
from pigeon import Pigeon

# ============================================================================
# Global Variables
# ----------------------------------------------------------------------------
pigeon = Pigeon()

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
        pigeon.sendUpdate(resp,last=True)
        return
    except Exception as e:
        pigeon.sendUpdate({
            'status': 'error',
            'message' : 'An exception occurred while testing connectivity: {}'.format(str(e)),
            'data' : {}
        })


if __name__ == "__main__":
    main()