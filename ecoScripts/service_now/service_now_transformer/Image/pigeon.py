import json

class Pigeon(object):
    def __init__(self):
        self.note = {
            "status_code" : 0,
            "message" : "",
            "data" : {}
        }

    def send(self):
        print(json.dumps(self.note))

    def sendUpdate(self, update, last=False):
        status = self.translate(str(update['status']).lower())
        if not last and status == 200:
            status = 100
        self.note.update({
            'status_code': status,
            'message': update['message'] if 'message' in update else '',
            'data': update['data'] if 'data' in update else {}
        })
        self.send()
        return True if status < 400 else False

    def translate(self, status):
        if status.isdigit():
            return int(status)
        elif status in ['info']:
            return 100
        elif status in ['success', 'succeeded', 'verified']:
            return 200
        elif status in ['warning']:
            return 300
        elif status in ['error', 'fail', 'failed']:
            return 400
        else:
            return 404

    def sendInfoMessage(self, message):
        self.sendUpdate({
            'status': 'info',
            'message': message
        })
